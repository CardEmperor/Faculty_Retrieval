# 🤖 AI & Future of Work — Professor Directory

A hostable Streamlit web app to explore Economics & Finance professors researching
AI, automation, FinTech, and the future of work — with **free live search** (no API
key, no payment) to find professors beyond the seeded database.

## What's included

| File | Purpose |
|------|---------|
| `app.py` | The Streamlit application |
| `professors_data.json` | Seed database of 76 professors |
| `requirements.txt` | Python dependencies |
| `AI_Future_of_Work_Professors.xlsx` | Excel workbook of the seed database |

## Features

- **📋 Professor Profiles** — expandable cards with metrics, cited works, links, and a
  **"Show top co-authors" button** that pulls each professor's frequent collaborators
  live from OpenAlex
- **🔎 Find New Professors** — **free** live search via OpenAlex (240M+ scholarly
  works); returns real citation counts, h-index, institutions, and most-cited works.
  **Searching by professor name also displays their top co-authors automatically.**
  Found professors merge into every tab and the downloads.
- **📊 Analytics** — Impact vs Social scatter, top-15 rankings, area distribution
  (search-found professors highlighted in green)
- **📄 Top Cited Works** — searchable table of notable works
- **📥 Download Data** — export everything (seed + found) as CSV or JSON

## Co-authors (via OpenAlex)

For any professor — seeded or found via search — the app can show their **top
co-authors**, ranked by number of joint works (ties broken by joint citation count).
It works by resolving the professor to their OpenAlex profile, pulling up to 200 of
their most-cited works, and aggregating co-authorships across them. Each co-author
row shows their institution, joint-work count, joint citations, and a link to their
OpenAlex profile, plus a bar chart of the top 10 collaborators.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Live search — completely free

The "Find New Professors" tab uses **OpenAlex**, a free and open scholarly database.
**No API key, no account, no funds required.** Search by research field/topic or by
professor name. **Strongly recommended:** enter your email in the sidebar — OpenAlex
routes identified requests into a faster, more reliable "polite pool" instead of the
shared anonymous pool, which noticeably cuts down on overload errors (still free,
never validated, just a courtesy identifier).

### If you see "OpenAlex: HTTP 503" or timeouts

A 503 means OpenAlex's own servers are temporarily overloaded — it's not something
wrong with your query, and it's especially common on shared hosting like Streamlit
Community Cloud, where many different apps' traffic can share the same egress IPs.
The app already handles this automatically:

- **Retries with backoff** — up to 5 attempts per request, with jittered exponential
  delay (≈1, 2, 4, 8, 16 s), honoring OpenAlex's `Retry-After` header if it sends one.
- **Stale-but-usable fallback** — if all retries fail but the app has previously
  fetched that exact result successfully, it shows that cached result with a small
  "showing cached results" notice instead of a hard error.
- **A visible Retry button** appears wherever a search or co-author lookup fails
  outright, so you don't have to retype your query.
- **Bounded concurrency** — at most 3 simultaneous requests, to avoid piling on an
  already-stressed endpoint.

If you still see persistent 503s: add your email in the sidebar if you haven't, wait
a minute (OpenAlex overloads are usually brief), and try again.

### Honest limitation

OpenAlex provides academic data (citations, h-index, works, institutions) but **not**
LinkedIn/Twitter activity. So professors found via search show **Social: N/A**. Their
impact score is derived from h-index using this transparent mapping:

| h-index | Impact score |
|---------|--------------|
| ≥150 | 99 |
| ≥100 | 95 |
| ≥70 | 90 |
| ≥50 | 85 |
| ≥35 | 80 |
| ≥25 | 75 |
| ≥15 | 68 |
| ≥8 | 60 |
| <8 | 50 |

## Deploy free on Streamlit Community Cloud

1. Push these files to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo.
3. Deploy. **No secrets or API keys needed.**

## Notes

- Professors found via live search persist for the browser session. Use the download
  buttons to save an enriched database, or "Clear all found professors" to reset.
- Verify anything decision-critical against the professor's actual profile and Google
  Scholar — derived impact scores are approximate.
