import os
import base64
import re
import logging
from flask import Flask, request, jsonify
from github import Github
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Terminal Cleanup: Hide Flask/Werkzeug HTTP logs ---
# Set the logging level for Werkzeug (Flask's underlying server) to ERROR
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) 
# -------------------------------------------------------

# --- Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
REPO_NAME = os.getenv("REPO_NAME")
TARGET_FILE = os.getenv("TARGET_FILE", "game.py")
# Define the local path for file saving (the same directory where main.py runs)
LOCAL_FILE_PATH = os.path.join(os.getcwd(), TARGET_FILE) 

# --- Clients Setup ---
# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
# !!! MODEL UPGRADE: Using gemini-2.5-pro for higher quality and complex reasoning !!!
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# GitHub client setup
# NOTE: DeprecationWarning is expected here, but functionality is correct.
g = Github(GITHUB_TOKEN)

def clean_gemini_output(text):
    """Cleans Gemini's output from markdown tags."""
    # Remove ```python from the start and ``` from the end
    cleaned_text = re.sub(r'^```python\s*', '', text, flags=re.MULTILINE)
    cleaned_text = re.sub(r'^```\s*', '', cleaned_text, flags=re.MULTILINE)
    # Remove trailing ```
    cleaned_text = cleaned_text.strip().rstrip('`')
    return cleaned_text.strip()

def get_ai_code(current_code, issue_text, is_new_file):
    """Sends a request to Gemini and gets the new code."""
    
    # --- OPTIMIZED SYSTEM INSTRUCTION (for higher quality and context analysis) ---
    system_instruction = "You are an elite, meticulous Python developer. Your sole purpose is to analyze the provided GitHub Issue (Title and Description), understand the intent, and output the absolute best, most robust, and highest quality raw Python code required to fulfill the request. You must output ONLY the complete, executable Python code. Do not include any explanations, markdown formatting (like ```python), or introductory text. Pay close attention to all details in the request and adhere to existing code style."
    # -----------------------------------------------------------------------------

    if is_new_file:
        prompt = f"""
        {system_instruction}
        
        Task: Create a NEW Python file named '{TARGET_FILE}'.
        Requirements described in the issue:
        "{issue_text}"
        
        Generate the full code for this new file.
        """
        print("[-] Gemini is creating a NEW file...")
    else:
        prompt = f"""
        {system_instruction}
        
        Task: Update the existing code inside '{TARGET_FILE}'.
        
        Current Code:
        ```python
        {current_code}
        ```
        
        Requested Changes based on issue:
        "{issue_text}"
        
        Provide the FULL updated code ready for replacement.
        """
        print("[-] Gemini is UPDATING existing code...")
    
    # Progress Indicator Start
    print("[-] Waiting for Gemini response (Generating code, please wait)...", end="", flush=True)

    # Synchronous API call
    response = model.generate_content(prompt)
    
    # Progress Indicator End
    print("\r[V] Gemini response received. Code generation complete.           ")

    raw_code = response.text
    return clean_gemini_output(raw_code)

def handle_github_flow(issue_number, issue_title, issue_body):
    """Handles the entire GitHub flow: read, branch, local save, commit, pull request, and closing the issue."""
    try:
        repo = g.get_repo(REPO_NAME)
        # Assumes 'main' branch, update if your branch is 'master'
        main_branch = repo.get_branch("main") 
        
        current_code = ""
        file_sha = None
        is_new_file = False

        # 1. Try to read the file (check existence on GitHub)
        try:
            print(f"[-] Checking if {TARGET_FILE} exists on GitHub...")
            file_content_obj = repo.get_contents(TARGET_FILE, ref="main")
            current_code = base64.b64decode(file_content_obj.content).decode("utf-8")
            file_sha = file_content_obj.sha # Need SHA for updating
            print(f"[V] File found on GitHub.")
        except Exception:
             # File does not exist (404)
            print(f"[X] File {TARGET_FILE} not found on GitHub. Will create from scratch.")
            is_new_file = True
            current_code = "" 

        # 2. Get new code from the AI
        full_issue_text = f"Title: {issue_title}\nDescription:\n{issue_body}"
        new_code = get_ai_code(current_code, full_issue_text, is_new_file)
        
        # 3. Create a new branch
        branch_name = f"ai-fix-{issue_number}"
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
        print(f"[-] Created branch: {branch_name}")
        
        # 4. Create or update file in the new branch (GitHub Commit)
        commit_msg = f"AI generated code for Issue #{issue_number}"
        if is_new_file:
            # Create new file (create_file)
            repo.create_file(
                path=TARGET_FILE,
                message=commit_msg,
                content=new_code,
                branch=branch_name
            )
            print("[-] New file created and committed to GitHub.")
        else:
            # Update existing file (update_file requires SHA)
            repo.update_file(
                path=TARGET_FILE,
                message=commit_msg,
                content=new_code,
                sha=file_sha,
                branch=branch_name
            )
            print("[-] File updated and committed to GitHub.")
        
        # --- Prepare PR Body (including AI guidance for bug fixes) ---
        pr_body = f"Automation by Gemini AI.\nFixes #{issue_number}."
        
        # Check if the issue is a bug report (to add troubleshooting guidance)
        bug_keywords = ["error", "bug", "traceback", "exception", "failed", "crash"]
        if any(keyword in issue_title.lower() or keyword in issue_body.lower() for keyword in bug_keywords):
            pr_body += "\n\n---\n**🧠 AI Debugging Note:** This PR attempts to fix a reported issue. Review the changes carefully, especially around Tkinter window lifecycle or input validation."
        # -----------------------------------------------------------------
            
        # 5. Create Pull Request
        pr = repo.create_pull(
            title=f"AI Fix: {issue_title}",
            body=pr_body,
            head=branch_name,
            base="main"
        )
        print(f"[+] Pull Request Created: {pr.html_url}")

        # --- Close the Issue Automatically ---
        issue = repo.get_issue(issue_number) # Fetch the issue object
        issue.edit(state='closed')
        print(f"[V] Issue #{issue_number} successfully closed.")
        # ----------------------------------------------------

        # 6. LOCAL SAVE (After PR creation to avoid server restart issue)
        print(f"[-] Saving/Updating {TARGET_FILE} locally at: {LOCAL_FILE_PATH}")
        with open(LOCAL_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(new_code)
        print("[V] Local file successfully updated. Check your project folder!")
        
        return pr.html_url

    except Exception as e:
        print(f"[!] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return str(e)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # Only react when issue is opened
    if data and data.get('action') == 'opened' and 'issue' in data:
        issue = data['issue']
        print(f"\n[!] --- New Issue Opened: #{issue['number']} ---")
        pr_url = handle_github_flow(issue['number'], issue['title'], issue['body'])
        return jsonify({"status": "success", "pr_url": pr_url}), 200
    # Event ignored
    return jsonify({"msg": "OK, but event ignored"}), 200

if __name__ == '__main__':
    print("[-] Server starting on port 3000...")
    # use_reloader=False prevents the server from restarting every time the local file is updated.
    app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)