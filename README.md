# AI-Agent Tic Tac Toe

Simple Python project that runs a Tkinter-based Tic Tac Toe game (`game.py`) and a small Flask webhook server (`main.py`) that integrates with GitHub and Google Generative AI.

This README explains how to set up and run the project on macOS, Windows and Ubuntu, and how to download the helper repository used by the project.

## Prerequisites

- Python 3.10+ (recommended). The code uses modern libraries; if you have an earlier 3.x version, some features may not work.
- pip (Python package installer)
- Git (for cloning the external repo)

Optional (for `main.py` webhook functionality):
- A GitHub personal access token with repo permissions (set `GITHUB_TOKEN`)
- A Google API key for Generative AI (set `GOOGLE_API_KEY`)
- A `.env` file with environment variables (example below)

## External repository

This project references another repository. Clone it if you need the example/test assets or want to follow along:

https://github.com/amirmahdimon/test_game

To clone:

```bash
git clone https://github.com/amirmahdimon/test_game.git
```

## Setup

First, create and activate a virtual environment (recommended) and install dependencies.

macOS / Ubuntu

```bash
# create venv
python3 -m venv .venv
source .venv/bin/activate

# install packages
pip install --upgrade pip
pip install -r requirements.txt  # if you have a requirements.txt
# or install individually:
pip install flask python-dotenv PyGithub google-generative-ai
```

Windows (PowerShell)

```powershell
# create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install packages
python -m pip install --upgrade pip
python -m pip install -r requirements.txt  # if you have a requirements.txt
# or install individually:
python -m pip install flask python-dotenv PyGithub google-generative-ai
```

Notes:
- If you don't plan to run `main.py` (the webhook server), you can skip installing the Google and GitHub related packages.
- The GUI game (`game.py`) only depends on the standard `tkinter` package, which is included with most Python distributions. On some Linux systems you may need to install it separately (e.g., `sudo apt install python3-tk`).

## Environment variables (optional)

Create a `.env` file in the project root with the following keys if you plan to run `main.py`:

```
GITHUB_TOKEN=ghp_xxx
GOOGLE_API_KEY=AIza... or your key
REPO_NAME=owner/repo
TARGET_FILE=game.py
```

## Run the Tic Tac Toe GUI (game.py)

macOS / Ubuntu

```bash
# activate venv if used
source .venv/bin/activate

python3 game.py
```

Windows (PowerShell)

```powershell
.# activate venv
.\.venv\Scripts\Activate.ps1

python game.py
```

When you run `game.py` a small dialog will ask for the board size (3 for 3x3). Provide a number (>=3) and the Tkinter GUI will open.

## Run the webhook server (main.py)

Warning: `main.py` attempts to contact GitHub and Google Generative AI using environment variables. Make sure you set the variables described above.

macOS / Ubuntu

```bash
source .venv/bin/activate
python3 main.py
```

Windows (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

The Flask server starts on port 3000 and exposes a `/webhook` endpoint that expects GitHub issue events. This script will create branches, commit files, and open pull requests when properly configured.

## Troubleshooting

- If Tkinter dialogs fail on Ubuntu, install the system package:

```bash
sudo apt update
sudo apt install python3-tk
```

- If you see import errors for `google.generativeai` or `github`, confirm the packages are installed in the active environment.

## Quick checklist

- Python 3.10+
- (optional) virtual environment activated
- install dependencies
- (optional) set `.env` keys for `main.py`
- run `python game.py` to play

## License

This repository does not include an explicit license. Check the original code and contributors for licensing terms.
