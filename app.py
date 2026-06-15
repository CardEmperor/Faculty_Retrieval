import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
import plotly.graph_objects as go

# ═══════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════
st.set_page_config(
    page_title="AI & Future of Work — Professor Directory",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════
# LOAD SEED DATA
# ═══════════════════════════════════════
@st.cache_data
def load_data():
    data_file = os.path.join(os.path.dirname(__file__), "professors_data.json")
    with open(data_file) as f:
        return json.load(f)

seed_profs = load_data()

# Session state holds professors found via live search (so they persist across reruns)
if "extra_profs" not in st.session_state:
    st.session_state.extra_profs = []

# Combined list used everywhere in the app
profs = seed_profs + st.session_state.extra_profs
df = pd.DataFrame(profs)

# ═══════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════
st.markdown("""
<style>
    .main { background-color: #0E1117; }
    .block-container { padding-top: 1.5rem; max-width: 1400px; }
    .stMetric { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; }
    h1 { background: linear-gradient(135deg, #E94560, #FF7675); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem !important; }
    .professor-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 20px; margin-bottom: 12px; }
    div[data-testid="stExpander"] { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; }
    .found-badge { background: rgba(46,204,113,0.15); color: #2ECC71; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# AI SEARCH HELPER (Anthropic API + web search)
# ═══════════════════════════════════════
def get_api_key():
    """Look for the key in Streamlit secrets first, then sidebar input."""
    key = None
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", None)
    except Exception:
        key = None
    return key or st.session_state.get("api_key_input", None)

def search_professors_ai(query, api_key, n_results=5):
    """
    Use Claude with the web_search tool to find finance/economics professors
    matching the query who are NOT already in the database.
    Returns (list_of_professor_dicts, raw_text, error_or_None).
    """
    try:
        import anthropic
    except ImportError:
        return [], "", "The 'anthropic' package is not installed. Run: pip install anthropic"

    existing_names = ", ".join(sorted(p["name"] for p in (seed_profs + st.session_state.extra_profs)))

    prompt = f"""Search the web for {n_results} Economics or Finance professors who research AI, automation, the future of work, FinTech, or machine learning in economics/finance, and who match this request: "{query}".

IMPORTANT: Do NOT include any of these professors who are already in our database:
{existing_names}

For each professor you find, return their information. Use web search to find accurate, current details.

Return ONLY a valid JSON array (no markdown, no backticks, no preamble). Each object must have exactly these fields:
- "name": full name
- "university": current institution
- "department": department/school
- "title": academic title (e.g. "Professor", "Assoc. Professor", "Asst. Professor")
- "country": country
- "areas": array of 3-6 research area strings
- "h_index": integer estimate (best guess from Google Scholar if available, else estimate)
- "citations": integer estimate of total citations
- "impact_score": integer 0-100 estimating academic impact (based on citations, h-index, influence)
- "social_score": integer 0-100 estimating social media activeness (LinkedIn + Twitter/X presence)
- "top_cited": array of 2-4 strings naming their most cited/notable works
- "linkedin": short description of LinkedIn presence (e.g. "Active (10K+ followers)") or ""
- "twitter": their Twitter/X handle with follower note (e.g. "@handle (50K+)") or ""
- "website": personal/faculty page URL or ""
- "scholar": Google Scholar URL or ""
- "email": email if found or ""
- "ra_hiring": boolean, true if they appear to take PhD students / hire RAs
- "phd_students": short note on their lab/students or ""
- "seeks": short description of what they look for in students or ""
- "awards": notable awards or ""

Return the JSON array only."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}],
            messages=[{"role": "user", "content": prompt}]
        )
        # Concatenate all text blocks from the response
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        cleaned = text.replace("```json", "").replace("```", "").strip()
        # Extract the JSON array
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        results = json.loads(cleaned)
        if isinstance(results, list):
            return results, text, None
        return [], text, "Response was not a JSON array."
    except json.JSONDecodeError:
        return [], text if 'text' in dir() else "", "Could not parse the results as JSON. Try rephrasing your search."
    except Exception as e:
        return [], "", f"Search error: {str(e)}"

# ═══════════════════════════════════════
# HEADER
# ═══════════════════════════════════════
st.title("🤖 AI & Future of Work — Professor Directory")
n_found = len(st.session_state.extra_profs)
subtitle = f"**{len(seed_profs)} seeded professors**"
if n_found:
    subtitle += f" + **{n_found} found via live search**"
subtitle += " researching AI, Automation, FinTech & the Future of Work"
st.markdown(subtitle)
st.markdown("---")

# ═══════════════════════════════════════
# SIDEBAR FILTERS
# ═══════════════════════════════════════
with st.sidebar:
    st.header("🔍 Filters")

    search = st.text_input("Search by name, university, or area", "")

    all_areas = sorted(set(a for p in profs for a in p["areas"]))
    selected_areas = st.multiselect("Research Areas", all_areas, default=[])

    all_countries = sorted(set(p["country"] for p in profs))
    selected_countries = st.multiselect("Country", all_countries, default=[])

    all_unis = sorted(set(p["university"] for p in profs))
    selected_unis = st.multiselect("University", all_unis, default=[])

    ra_only = st.checkbox("🟢 Hiring RAs / PhD Students Only", False)

    impact_range = st.slider("Impact Score Range", 0, 100, (0, 100))
    social_range = st.slider("Social Activeness Range", 0, 100, (0, 100))

    sort_by = st.selectbox("Sort By", ["Impact Score ↓", "Social Score ↓", "h-index ↓", "Citations ↓", "Name A-Z"])

    st.markdown("---")
    st.subheader("🔑 AI Search Setup")
    st.caption("Add an Anthropic API key to enable live web search for new professors. Get one at console.anthropic.com")
    st.text_input("Anthropic API Key", type="password", key="api_key_input",
                  help="Stored only in this session. For hosting, add ANTHROPIC_API_KEY to Streamlit secrets instead.")

# ═══════════════════════════════════════
# FILTER LOGIC
# ═══════════════════════════════════════
def apply_filters(plist):
    out = plist.copy()
    if search:
        s = search.lower()
        out = [p for p in out if s in p["name"].lower() or s in p["university"].lower()
               or any(s in a.lower() for a in p["areas"]) or s in p.get("seeks", "").lower()]
    if selected_areas:
        out = [p for p in out if any(a in p["areas"] for a in selected_areas)]
    if selected_countries:
        out = [p for p in out if p["country"] in selected_countries]
    if selected_unis:
        out = [p for p in out if p["university"] in selected_unis]
    if ra_only:
        out = [p for p in out if p.get("ra_hiring")]
    out = [p for p in out if impact_range[0] <= p.get("impact_score", 0) <= impact_range[1]]
    out = [p for p in out if social_range[0] <= p.get("social_score", 0) <= social_range[1]]
    if sort_by == "Impact Score ↓":
        out.sort(key=lambda p: p.get("impact_score", 0), reverse=True)
    elif sort_by == "Social Score ↓":
        out.sort(key=lambda p: p.get("social_score", 0), reverse=True)
    elif sort_by == "h-index ↓":
        out.sort(key=lambda p: p.get("h_index", 0), reverse=True)
    elif sort_by == "Citations ↓":
        out.sort(key=lambda p: p.get("citations", 0), reverse=True)
    else:
        out.sort(key=lambda p: p["name"])
    return out

filtered = apply_filters(profs)

# ═══════════════════════════════════════
# METRICS ROW
# ═══════════════════════════════════════
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Professors", len(profs))
c2.metric("Showing", len(filtered))
c3.metric("Hiring RAs", sum(1 for p in filtered if p.get("ra_hiring")))
c4.metric("Avg Impact", f"{sum(p.get('impact_score',0) for p in filtered)/max(len(filtered),1):.0f}")
c5.metric("Avg Social", f"{sum(p.get('social_score',0) for p in filtered)/max(len(filtered),1):.0f}")

st.markdown("---")

# ═══════════════════════════════════════
# TABS
# ═══════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Professor Profiles",
    "🔎 Find New Professors",
    "📊 Analytics",
    "📄 Top Cited Works",
    "📥 Download Data"
])

# ── helper to render one professor card ──
def render_professor(p, found=False):
    badge = " 🟢" if found else ""
    header = f"**{p['name']}**{badge} — {p.get('university','')} ({p.get('title','')})  |  Impact: {p.get('impact_score','?')}  |  Social: {p.get('social_score','?')}"
    with st.expander(header):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Department:** {p.get('department','')}")
            st.markdown(f"**Country:** {p.get('country','')}")
            st.markdown(f"**Research Areas:** {', '.join(p.get('areas', []))}")
            if p.get("seeks"):
                st.markdown(f"**What They Seek:** {p['seeks']}")
            if p.get("phd_students"):
                st.markdown(f"**Students/Lab:** {p['phd_students']}")
            if p.get("awards"):
                st.markdown(f"🏆 **Awards:** {p['awards']}")
        with col2:
            st.metric("Impact Score", p.get("impact_score", "?"))
            st.metric("h-index", p.get("h_index", "?"))
            cites = p.get("citations", 0)
            st.metric("Citations", f"{cites:,}" if isinstance(cites, int) else cites)
            st.metric("Social Score", p.get("social_score", "?"))
            ra_status = "✅ Yes" if p.get("ra_hiring") else "❌ No"
            st.markdown(f"**Hiring RAs:** {ra_status}")
        if p.get("top_cited"):
            st.markdown("**📝 Most Cited Works:**")
            for paper in p["top_cited"]:
                st.markdown(f"- {paper}")
        link_parts = []
        if p.get("email"): link_parts.append(f"📧 [{p['email']}](mailto:{p['email']})")
        if p.get("website"): link_parts.append(f"🌐 [Website]({p['website']})")
        if p.get("scholar"): link_parts.append(f"🎓 [Scholar]({p['scholar']})")
        if p.get("twitter"): link_parts.append(f"🐦 {p['twitter']}")
        if p.get("linkedin"): link_parts.append(f"💼 {p['linkedin']}")
        if link_parts:
            st.markdown(" | ".join(link_parts))

# ── TAB 1: PROFILES ──
with tab1:
    if not filtered:
        st.info("No professors match your filters. Try widening them, or use the **Find New Professors** tab to search the web.")
    for p in filtered:
        is_found = p in st.session_state.extra_profs
        render_professor(p, found=is_found)

# ── TAB 2: FIND NEW PROFESSORS (live web search) ──
with tab2:
    st.subheader("🔎 Find Professors Beyond the Database")
    st.markdown("Search the web for Economics & Finance professors **not** among the seeded ones. "
                "Found professors are added to every tab (profiles, analytics, downloads) for this session.")

    api_key = get_api_key()
    if not api_key:
        st.warning("⚠️ Add your **Anthropic API key** in the sidebar (under *AI Search Setup*) to enable live search. "
                   "For a hosted app, add `ANTHROPIC_API_KEY` to your Streamlit secrets instead.")

    colq, coln = st.columns([4, 1])
    with colq:
        query = st.text_input("Describe who you're looking for",
                              placeholder="e.g. 'professors studying generative AI and labor markets in Europe' or 'AI and accounting researchers'")
    with coln:
        n_results = st.number_input("# results", min_value=1, max_value=10, value=5)

    # Quick search suggestions
    st.caption("Quick searches:")
    suggestions = [
        "AI and healthcare economics professors",
        "generative AI productivity researchers",
        "FinTech and crypto finance professors in Asia",
        "automation and labor economics rising stars",
        "machine learning asset pricing researchers",
    ]
    scols = st.columns(len(suggestions))
    clicked_suggestion = None
    for i, s in enumerate(suggestions):
        if scols[i].button(s, key=f"sugg_{i}"):
            clicked_suggestion = s

    do_search = st.button("🔍 Search the Web", type="primary", disabled=not api_key)

    active_query = clicked_suggestion or (query if do_search else None)

    if active_query:
        if not api_key:
            st.error("Please add your Anthropic API key in the sidebar first.")
        else:
            with st.spinner(f"Searching the web for: {active_query} ..."):
                results, raw, err = search_professors_ai(active_query, api_key, n_results)
            if err:
                st.error(err)
                if raw:
                    with st.expander("Show raw response"):
                        st.text(raw)
            elif not results:
                st.warning("No new professors found. Try a different or broader query.")
            else:
                st.success(f"Found {len(results)} professor(s)! Review below and click **Add** to include them in the directory.")
                existing_names_lower = {p["name"].lower() for p in profs}
                for idx, r in enumerate(results):
                    # Skip if somehow already present
                    if r.get("name", "").lower() in existing_names_lower:
                        continue
                    with st.container():
                        st.markdown(f"### {r.get('name','Unknown')} — {r.get('university','')}")
                        cc1, cc2 = st.columns([3, 1])
                        with cc1:
                            st.markdown(f"**{r.get('title','')}**, {r.get('department','')} ({r.get('country','')})")
                            st.markdown(f"**Areas:** {', '.join(r.get('areas', []))}")
                            if r.get("seeks"):
                                st.markdown(f"**Seeks:** {r['seeks']}")
                            if r.get("top_cited"):
                                st.markdown("**Top works:** " + "; ".join(r["top_cited"][:3]))
                            links = []
                            if r.get("website"): links.append(f"[Website]({r['website']})")
                            if r.get("scholar"): links.append(f"[Scholar]({r['scholar']})")
                            if r.get("twitter"): links.append(f"🐦 {r['twitter']}")
                            if r.get("email"): links.append(f"📧 {r['email']}")
                            if links:
                                st.markdown(" | ".join(links))
                        with cc2:
                            st.metric("Impact", r.get("impact_score", "?"))
                            st.metric("Social", r.get("social_score", "?"))
                            st.metric("h-index", r.get("h_index", "?"))
                        if st.button(f"➕ Add {r.get('name','')}", key=f"add_{idx}_{r.get('name','')}"):
                            # normalize fields so it merges cleanly
                            r.setdefault("ra_hiring", False)
                            for fld in ["h_index", "citations", "impact_score", "social_score"]:
                                try:
                                    r[fld] = int(r.get(fld, 0))
                                except (ValueError, TypeError):
                                    r[fld] = 0
                            r.setdefault("areas", [])
                            r.setdefault("top_cited", [])
                            st.session_state.extra_profs.append(r)
                            st.success(f"Added {r.get('name','')}! It now appears across all tabs.")
                            st.rerun()

                # Option to add all at once
                if st.button("➕➕ Add ALL found professors", key="add_all"):
                    added = 0
                    for r in results:
                        if r.get("name", "").lower() not in existing_names_lower:
                            r.setdefault("ra_hiring", False)
                            for fld in ["h_index", "citations", "impact_score", "social_score"]:
                                try:
                                    r[fld] = int(r.get(fld, 0))
                                except (ValueError, TypeError):
                                    r[fld] = 0
                            r.setdefault("areas", [])
                            r.setdefault("top_cited", [])
                            st.session_state.extra_profs.append(r)
                            added += 1
                    st.success(f"Added {added} professor(s)!")
                    st.rerun()

    # Show currently added professors with option to clear
    if st.session_state.extra_profs:
        st.markdown("---")
        st.markdown(f"**🟢 {len(st.session_state.extra_profs)} professor(s) added via search this session:**")
        st.markdown(", ".join(p["name"] for p in st.session_state.extra_profs))
        if st.button("🗑️ Clear all found professors"):
            st.session_state.extra_profs = []
            st.rerun()

# ── TAB 3: ANALYTICS ──
with tab3:
    st.subheader("Impact Score vs Social Activeness")
    fig_df = pd.DataFrame(filtered)
    if len(fig_df) > 0:
        # mark which are found via search
        fig_df["source"] = ["Found via Search" if p in st.session_state.extra_profs else "Seeded" for p in filtered]
        fig = px.scatter(fig_df, x="social_score", y="impact_score", size="h_index",
                         color="source", symbol="source",
                         hover_name="name", hover_data=["university", "h_index", "citations"],
                         labels={"social_score": "Social Activeness Score", "impact_score": "Academic Impact Score"},
                         size_max=45, template="plotly_dark",
                         color_discrete_map={"Seeded": "#4A90D9", "Found via Search": "#2ECC71"})
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top 15 by Impact Score")
        top15 = fig_df.nlargest(15, "impact_score")
        fig2 = px.bar(top15, x="name", y="impact_score", color="impact_score",
                      color_continuous_scale="Reds", template="plotly_dark",
                      labels={"impact_score": "Impact Score", "name": "Professor"})
        fig2.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Top 15 by Social Activeness")
        top15s = fig_df.nlargest(15, "social_score")
        fig3 = px.bar(top15s, x="name", y="social_score", color="social_score",
                      color_continuous_scale="Blues", template="plotly_dark",
                      labels={"social_score": "Social Score", "name": "Professor"})
        fig3.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Research Areas Distribution")
        area_counts = {}
        for p in filtered:
            for a in p.get("areas", []):
                area_counts[a] = area_counts.get(a, 0) + 1
        if area_counts:
            area_df = pd.DataFrame(sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:20], columns=["Area", "Count"])
            fig4 = px.bar(area_df, x="Count", y="Area", orientation="h", template="plotly_dark",
                          color="Count", color_continuous_scale="Viridis")
            fig4.update_layout(height=500, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No data to chart with current filters.")

# ── TAB 4: TOP CITED ──
with tab4:
    st.subheader("Most Cited Works")
    works = []
    for p in filtered:
        for paper in p.get("top_cited", [])[:3]:
            works.append({"Professor": p["name"], "University": p.get("university", ""),
                          "Work": paper, "Impact": p.get("impact_score", 0), "h-index": p.get("h_index", 0)})
    works_df = pd.DataFrame(works)
    if len(works_df) > 0:
        search_works = st.text_input("Search works", "", key="search_works")
        if search_works:
            works_df = works_df[works_df.apply(
                lambda r: search_works.lower() in str(r["Work"]).lower() or search_works.lower() in str(r["Professor"]).lower(), axis=1)]
        st.dataframe(works_df, use_container_width=True, height=600)
    else:
        st.info("No works to show with current filters.")

# ── TAB 5: DOWNLOAD ──
with tab5:
    st.subheader("Download Database")
    st.caption("Downloads include both the seeded professors AND any found via live search this session.")

    csv_df = pd.DataFrame([{
        "Name": p.get("name", ""), "University": p.get("university", ""), "Department": p.get("department", ""),
        "Title": p.get("title", ""), "Country": p.get("country", ""), "Areas": "; ".join(p.get("areas", [])),
        "h_index": p.get("h_index", 0), "Citations": p.get("citations", 0), "Impact_Score": p.get("impact_score", 0),
        "Social_Score": p.get("social_score", 0), "Hiring_RAs": p.get("ra_hiring", False),
        "Email": p.get("email", ""), "Twitter": p.get("twitter", ""),
        "LinkedIn": p.get("linkedin", ""), "Website": p.get("website", ""),
        "Scholar": p.get("scholar", ""), "Seeks": p.get("seeks", ""),
        "Awards": p.get("awards", ""), "Top_Cited": " | ".join(p.get("top_cited", [])[:3]),
        "Source": "Found via Search" if p in st.session_state.extra_profs else "Seeded"
    } for p in profs])

    st.download_button("📥 Download CSV (all professors)", csv_df.to_csv(index=False), "ai_professors.csv", "text/csv")
    st.download_button("📥 Download JSON (all professors)", json.dumps(profs, indent=2), "ai_professors.json", "application/json")

    if st.session_state.extra_profs:
        st.download_button("📥 Download ONLY found professors (JSON)",
                           json.dumps(st.session_state.extra_profs, indent=2),
                           "found_professors.json", "application/json")

    st.markdown("---")
    st.markdown("### How to Host This App")
    st.code("""
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place these files in a folder:
#    - app.py (this file)
#    - professors_data.json (the seed data)
#    - requirements.txt

# 3. Run locally:
streamlit run app.py

# 4. Enable AI live search:
#    - Get an API key at console.anthropic.com
#    - Paste it in the sidebar (AI Search Setup), OR
#    - For hosting, create .streamlit/secrets.toml with:
#        ANTHROPIC_API_KEY = "sk-ant-..."

# 5. Deploy to Streamlit Cloud (free):
#    - Push to GitHub
#    - Go to share.streamlit.io
#    - Connect your repo, add the secret, and deploy!
    """, language="bash")
