# Tuhame

Tuhame is an autonomous housing and property-investigation pipeline for Nairobi rentals and listing discovery. It searches live listings with Exa, extracts the claims that matter, filters out low-confidence candidates, compares rents, and stores repeatable evidence in SQLite.

## Run

Use the existing environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py "2-bedroom Kilimani, max KES 85000, secure, parking"
```

The maximum rent is supplied by the user for each search. If no command-line request is provided, the program prompts for one. It is never assigned to a listing's extracted rent.

Set `EXA_API_KEY` in `.env` before running. Search results and pipeline events are cached in `pipeline.db` for reliable demos.

## Web investigation desk

Start the same pipeline through the browser:

```powershell
.venv\Scripts\python.exe -m web_server
```

Open `http://127.0.0.1:8000`. The web search uses the Tuhame investigation pipeline and requires `EXA_API_KEY` for live source discovery.

This repository is configured as the GitHub remote `https://github.com/vickymaish/Tuhame.git` and is intended for production project handoff.

