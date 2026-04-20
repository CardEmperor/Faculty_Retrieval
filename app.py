
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
# LOAD DATA
# ═══════════════════════════════════════
@st.cache_data
def load_data():
    data_file = os.path.join(os.path.dirname(__file__), "professors_data.json")
    with open(data_file) as f:
        profs = json.load(f)
    return profs

profs = load_data()
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
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# HEADER
# ═══════════════════════════════════════
st.title("🤖 AI & Future of Work — Professor Directory")
st.markdown(f"**{len(profs)} Economics & Finance Professors** researching AI, Automation, FinTech & the Future of Work")
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

# ═══════════════════════════════════════
# FILTER LOGIC
# ═══════════════════════════════════════
filtered = profs.copy()

if search:
    s = search.lower()
    filtered = [p for p in filtered if s in p["name"].lower() or s in p["university"].lower()
                or any(s in a.lower() for a in p["areas"]) or s in p.get("seeks","").lower()]

if selected_areas:
    filtered = [p for p in filtered if any(a in p["areas"] for a in selected_areas)]

if selected_countries:
    filtered = [p for p in filtered if p["country"] in selected_countries]

if selected_unis:
    filtered = [p for p in filtered if p["university"] in selected_unis]

if ra_only:
    filtered = [p for p in filtered if p["ra_hiring"]]

filtered = [p for p in filtered if impact_range[0] <= p["impact_score"] <= impact_range[1]]
filtered = [p for p in filtered if social_range[0] <= p["social_score"] <= social_range[1]]

if sort_by == "Impact Score ↓":
    filtered.sort(key=lambda p: p["impact_score"], reverse=True)
elif sort_by == "Social Score ↓":
    filtered.sort(key=lambda p: p["social_score"], reverse=True)
elif sort_by == "h-index ↓":
    filtered.sort(key=lambda p: p["h_index"], reverse=True)
elif sort_by == "Citations ↓":
    filtered.sort(key=lambda p: p["citations"], reverse=True)
else:
    filtered.sort(key=lambda p: p["name"])

# ═══════════════════════════════════════
# METRICS ROW
# ═══════════════════════════════════════
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Professors", len(profs))
c2.metric("Showing", len(filtered))
c3.metric("Hiring RAs", sum(1 for p in filtered if p["ra_hiring"]))
c4.metric("Avg Impact", f"{sum(p['impact_score'] for p in filtered)/max(len(filtered),1):.0f}")
c5.metric("Avg Social", f"{sum(p['social_score'] for p in filtered)/max(len(filtered),1):.0f}")

st.markdown("---")

# ═══════════════════════════════════════
# TABS
# ═══════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["📋 Professor Profiles", "📊 Analytics", "📄 Top Cited Works", "📥 Download Data"])

# ── TAB 1: PROFILES ──
with tab1:
    for p in filtered:
        with st.expander(f"**{p['name']}** — {p['university']} ({p['title']})  |  Impact: {p['impact_score']}  |  Social: {p['social_score']}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Department:** {p['department']}")
                st.markdown(f"**Country:** {p['country']}")
                st.markdown(f"**Research Areas:** {', '.join(p['areas'])}")
                st.markdown(f"**What They Seek:** {p.get('seeks','')}")
                if p.get("phd_students"):
                    st.markdown(f"**Students/Lab:** {p['phd_students']}")
                if p.get("awards"):
                    st.markdown(f"🏆 **Awards:** {p['awards']}")

            with col2:
                st.metric("Impact Score", p["impact_score"])
                st.metric("h-index", p["h_index"])
                st.metric("Citations", f"{p['citations']:,}")
                st.metric("Social Score", p["social_score"])
                ra_status = "✅ Yes" if p["ra_hiring"] else "❌ No"
                st.markdown(f"**Hiring RAs:** {ra_status}")

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

# ── TAB 2: ANALYTICS ──
with tab2:
    st.subheader("Impact Score vs Social Activeness")
    fig_df = pd.DataFrame(filtered)
    if len(fig_df) > 0:
        fig = px.scatter(fig_df, x="social_score", y="impact_score", size="h_index",
                         color="country", hover_name="name", hover_data=["university","h_index","citations"],
                         labels={"social_score":"Social Activeness Score","impact_score":"Academic Impact Score"},
                         size_max=45, template="plotly_dark")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top 15 by Impact Score")
        top15 = fig_df.nlargest(15, "impact_score")
        fig2 = px.bar(top15, x="name", y="impact_score", color="impact_score",
                      color_continuous_scale="Reds", template="plotly_dark",
                      labels={"impact_score":"Impact Score","name":"Professor"})
        fig2.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Top 15 by Social Activeness")
        top15s = fig_df.nlargest(15, "social_score")
        fig3 = px.bar(top15s, x="name", y="social_score", color="social_score",
                      color_continuous_scale="Blues", template="plotly_dark",
                      labels={"social_score":"Social Score","name":"Professor"})
        fig3.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Research Areas Distribution")
        area_counts = {}
        for p in filtered:
            for a in p["areas"]:
                area_counts[a] = area_counts.get(a, 0) + 1
        area_df = pd.DataFrame(sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:20], columns=["Area","Count"])
        fig4 = px.bar(area_df, x="Count", y="Area", orientation="h", template="plotly_dark",
                      color="Count", color_continuous_scale="Viridis")
        fig4.update_layout(height=500, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig4, use_container_width=True)

# ── TAB 3: TOP CITED ──
with tab3:
    st.subheader("Most Cited Works")
    works = []
    for p in filtered:
        for paper in p["top_cited"][:3]:
            works.append({"Professor": p["name"], "University": p["university"],
                         "Work": paper, "Impact": p["impact_score"], "h-index": p["h_index"]})
    works_df = pd.DataFrame(works)
    if len(works_df) > 0:
        search_works = st.text_input("Search works", "", key="search_works")
        if search_works:
            works_df = works_df[works_df.apply(lambda r: search_works.lower() in r["Work"].lower() or search_works.lower() in r["Professor"].lower(), axis=1)]
        st.dataframe(works_df, use_container_width=True, height=600)

# ── TAB 4: DOWNLOAD ──
with tab4:
    st.subheader("Download Database")
    csv_df = pd.DataFrame([{
        "Name": p["name"], "University": p["university"], "Department": p["department"],
        "Title": p["title"], "Country": p["country"], "Areas": "; ".join(p["areas"]),
        "h_index": p["h_index"], "Citations": p["citations"], "Impact_Score": p["impact_score"],
        "Social_Score": p["social_score"], "Hiring_RAs": p["ra_hiring"],
        "Email": p.get("email",""), "Twitter": p.get("twitter",""),
        "LinkedIn": p.get("linkedin",""), "Website": p.get("website",""),
        "Scholar": p.get("scholar",""), "Seeks": p.get("seeks",""),
        "Awards": p.get("awards",""), "Top_Cited": " | ".join(p["top_cited"][:3])
    } for p in profs])

    st.download_button("📥 Download CSV", csv_df.to_csv(index=False), "ai_professors.csv", "text/csv")
    st.download_button("📥 Download JSON", json.dumps(profs, indent=2), "ai_professors.json", "application/json")

    st.markdown("---")
    st.markdown("### How to Host This App")
    st.code("""
# 1. Install dependencies
pip install streamlit pandas plotly

# 2. Place these files in a folder:
#    - app.py (this file)
#    - professors_data.json (the data file)

# 3. Run locally:
streamlit run app.py

# 4. Deploy to Streamlit Cloud (free):
#    - Push to GitHub
#    - Go to share.streamlit.io
#    - Connect your repo
#    - Deploy!
    """, language="bash")
