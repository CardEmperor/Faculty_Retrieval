# 🤖 AI & Future of Work — Professor Directory

A hostable Streamlit web app to explore Economics & Finance professors researching
AI, automation, FinTech, and the future of work — now with **AI-powered live search**
to find professors beyond the seeded database.

## What's included

| File | Purpose |
|------|---------|
| `app.py` | The Streamlit application |
| `professors_data.json` | Seed database of 76 professors |
| `requirements.txt` | Python dependencies |
| `AI_Future_of_Work_Professors.xlsx` | Excel workbook of the seed database |
| `secrets.toml.example` | Template for the API key when hosting |

## Features

- **📋 Professor Profiles** — expandable cards with metrics, cited works, links
- **🔎 Find New Professors** — live web search (via Claude) for professors *not* in the
  database; found professors merge into every tab and the downloads
- **📊 Analytics** — Impact vs Social scatter, top-15 rankings, area distribution
  (search-found professors are highlighted in green)
- **📄 Top Cited Works** — searchable table of notable works
- **📥 Download Data** — export everything (seed + found) as CSV or JSON

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Enable AI live search

The "Find New Professors" tab needs an Anthropic API key (get one at
[console.anthropic.com](https://console.anthropic.com)).

**Option A — quick (per session):** paste the key into the sidebar under *AI Search Setup*.

**Option B — for hosting:** create `.streamlit/secrets.toml`:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

(See `secrets.toml.example`.)

## Deploy free on Streamlit Community Cloud

1. Push these files to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo.
3. In the app's **Settings → Secrets**, paste your `ANTHROPIC_API_KEY`.
4. Deploy. Done!

## Notes

- Professors found via live search persist for the browser session. Use the
  download buttons to save an enriched database, or "Clear all found professors"
  to reset.
- The app never hard-codes your API key; it is read from the sidebar input or
  Streamlit secrets only.
