# **🤖 AI & Future of Work — Professor Directory**

A hostable Streamlit web app to explore Economics & Finance professors researching

AI, automation, FinTech, and the future of work — with **free live search** (no API

key, no payment) to find professors beyond the seeded database.

## **What's included**

| File | Purpose |
| :---- | :---- |
| app.py | The Streamlit application |
| professors\_data.json | Seed database of 76 professors |
| requirements.txt | Python dependencies |

## **Features**

* **📋 Professor Profiles** — expandable cards with metrics, cited works, links, and a  
  **"Show top co-authors" button** that pulls each professor's frequent collaborators  
  live from OpenAlex  
* **🔎 Stateful Live Search** — **free** live search via OpenAlex (240M+ works) to dynamically add new professors. Search queries and results are securely stored in the session state, so your results **never vanish** when you click "Add Professor" or "Show co-authors".  
* **📊 Analytics** — Impact vs Social scatter, top-15 rankings, area distribution  
  (search-found professors highlighted in green)  
* **📄 Top Cited Works** — searchable table of notable works  
* **📥 Download Data** — export everything (seed \+ newly found researchers) as CSV or JSON

## **Co-authors (via OpenAlex)**

For any professor — seeded or found via search — the app can show their **top co-authors**, ranked by number of joint works (ties broken by joint citation count).

It works by resolving the professor to their OpenAlex profile, pulling up to 200 of

their most-cited works, and aggregating co-authorships across them. Each co-author

row shows their institution, joint-work count, joint citations, and a link to their

OpenAlex profile, plus a bar chart of the top 10 collaborators.

## **Run locally**

pip install \-r requirements.txt  
streamlit run app.py

## **Live search — completely free**

The "Find New Professors" tab uses **OpenAlex**, a free and open scholarly database.

**No API key, no account, no funds required.** Search by research field/topic or by

professor name. Optionally enter your email in the sidebar to use OpenAlex's faster

"polite pool" (still free).

### **Honest limitation**

OpenAlex provides academic data (citations, h-index, works, institutions) but **not**

LinkedIn/Twitter activity. So professors found via search show **Social: N/A**. Their

impact score is derived from h-index using this transparent mapping:

| h-index | Impact score |
| :---- | :---- |
| ≥150 | 99 |
| ≥100 | 95 |
| ≥70 | 90 |
| ≥50 | 85 |
| ≥35 | 80 |
| ≥25 | 75 |
| ≥15 | 68 |
| ≥8 | 60 |
| \<8 | 50 |

## **Deploy free on Streamlit Community Cloud**

1. Push these files to a GitHub repo.  
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo.  
3. Deploy. **No secrets or API keys needed.**

## **Notes**

* Professors found via live search persist for the browser session. Use the download  
  buttons to save an enriched database, or "Clear all found professors" to reset.  
* Verify anything decision-critical against the professor's actual profile and Google  
  Scholar — derived impact scores are approximate.