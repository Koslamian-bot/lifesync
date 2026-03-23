# LifeSync

LifeSync is currently a small Python CLI project for turning a user's daily routine into structured JSON using the Google Gemini API.

## Project layout

```text
lifesync/
|-- .gitignore
|-- README.md
`-- lifesync-engine/
    |-- engine.py
    |-- requirements.txt
    |-- .env.example
    `-- engine/            # local virtual environment, should not be committed
```

## Current project analysis

- The working application code is in `lifesync-engine/engine.py`.
- `lifesync-engine/engine/` is a local Python virtual environment and should stay out of Git.
- The app requires one secret in a `.env` file: `GEMINI_API_KEY`.
- The project is currently set up as a command-line script, not a packaged module or web app.

## Prerequisites

- Python 3.13 recommended
- A Google Gemini API key

## Setup

From the repository root:

```powershell
cd lifesync-engine
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Then open `lifesync-engine/.env` and set your real API key:

```env
GEMINI_API_KEY=your_api_key_here
```

## Run the project

From `lifesync-engine/`:

```powershell
.venv\Scripts\Activate.ps1
python engine.py
```

The script will:

1. Ask for a description of the user's daily routine.
2. Send that text to Gemini for structured extraction.
3. Ask follow-up questions if required fields are missing.
4. Print the final JSON profile.

## Recommended GitHub workflow

Before pushing:

```powershell
git init
git add .
git commit -m "Initial project setup"
```

Because of the `.gitignore`, Git should exclude:

- local virtual environments
- `.env` files
- Python cache files
- editor-specific folders

## Notes for teammates

- Do not commit real API keys.
- Use `.env.example` as the template for local setup.
- Prefer creating a fresh `.venv` instead of using the existing `engine/` folder.
