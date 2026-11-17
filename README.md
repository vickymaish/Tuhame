# RouteGuard

RouteGuard is the rebranded, AI-powered housing and property investigation platform for Nairobi rentals and listing discovery. It searches live listings, extracts the details that matter, filters out low-quality or misleading information, and helps users move from search to decision faster.

This project was previously known as Tuhame.

## Demo

[![Watch the RouteGuard demo](https://img.youtube.com/vi/mqZGPpAE-bI/hqdefault.jpg)](https://www.youtube.com/watch?v=mqZGPpAE-bI)

[Watch the demo video](https://youtu.be/mqZGPpAE-bI)

## Why RouteGuard?

- Finds live rental listings quickly
- Extracts key details such as rent, location, and amenities
- Filters weak or mismatched listings
- Built for Nairobi property discovery and investigation workflows

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

Open `http://127.0.0.1:8000`. The web search uses the RouteGuard investigation pipeline and requires `EXA_API_KEY` for live source discovery.

This repository is configured as the GitHub remote `https://github.com/vickymaish/Tuhame.git` and is intended for production project handoff.
