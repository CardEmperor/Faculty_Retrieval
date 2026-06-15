import streamlit as st
import pandas as pd
import json
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import plotly.express as px

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

if "extra_profs" not in st.session_state:
    st.session_state.extra_profs = []

if "coauthors_show" not in st.session_state:
    st.session_state.coauthors_show = set()

profs = seed_profs + st.session_state.extra_profs
df = pd.DataFrame(profs)

# ═══════════════════════════════════════
# CSS
# ═══════════════════════════════════════
st.markdown("""
<style>
    .main { background-color: #0E1117; }
    .block-container { padding-top: 1.5rem; max-width: 1400px; }
    .stMetric { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; }
    h1 { background: linear-gradient(135deg, #E94560, #FF7675); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem !important; }
    div[data-testid="stExpander"] { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# OPENALEX — resilient network layer
# ═══════════════════════════════════════
OPENALEX_BASE = "https://api.openalex.org"

# ── One shared session: connection-pooled + automatic retries with backoff ──
#   3 retries, starting at 1 s and doubling: 1 s → 2 s → 4 s.
#   Only retried for transient errors (408, 429, 500, 502, 503, 504).
#   Per-request read timeout is kept short (8 s) so a stall fails fast
#   and the adapter retries, rather than blocking the UI for 25+ seconds.
def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,          # wait 1 s, 2 s, 4 s between attempts
        status_forcelist={408, 429, 500, 502, 503, 504},
        allowed_methods={"GET"},
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://",  adapter)
    return session

# Module-level singleton — reused across Streamlit reruns via the module cache.
_SESSION = _make_session()

# Short individual timeout: (connect_timeout, read_timeout).
# The adapter will retry up to 3× if this fires, total worst-case ≈ 8+16+32 = 56 s,
# but typical success on retry-2 is well under 20 s.
_TIMEOUT = (5, 8)

COUNTRY_NAMES = {
    "US":"United States","GB":"United Kingdom","CA":"Canada","DE":"Germany","FR":"France",
    "IT":"Italy","NL":"Netherlands","CH":"Switzerland","ES":"Spain","SE":"Sweden","DK":"Denmark",
    "CN":"China","HK":"Hong Kong","SG":"Singapore","IN":"India","AU":"Australia","JP":"Japan",
    "BE":"Belgium","AT":"Austria","NO":"Norway","FI":"Finland","IE":"Ireland","IL":"Israel",
    "KR":"South Korea","BR":"Brazil","PT":"Portugal","NZ":"New Zealand",
}

def _country_name(code):
    return COUNTRY_NAMES.get((code or "").upper(), (code or "").upper())

def _impact_from_hindex(h):
    for t, s in [(150,99),(100,95),(70,90),(50,85),(35,80),(25,75),(15,68),(8,60)]:
        if h >= t:
            return s
    return 50

def _params(extra: dict, mailto: str | None) -> dict:
    p = dict(extra)
    if mailto:
        p["mailto"] = mailto
    return p

def _get(url, params, label="OpenAlex"):
    """Thin GET wrapper that converts network errors to a clear message."""
    try:
        r = _SESSION.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.Timeout:
        return None, f"{label}: timed out after 3 retries — OpenAlex may be slow right now. Try again in a moment."
    except requests.exceptions.ConnectionError as e:
        return None, f"{label}: connection error — {e}"
    except requests.exceptions.HTTPError as e:
        return None, f"{label}: HTTP {e.response.status_code}"
    except Exception as e:
        return None, f"{label}: {e}"

# ── Schema helpers ──
def _author_core(a: dict) -> dict:
    inst, country = "", ""
    lki = a.get("last_known_institutions") or []
    if not lki and a.get("last_known_institution"):
        lki = [a["last_known_institution"]]
    if lki and isinstance(lki[0], dict):
        inst    = lki[0].get("display_name", "") or ""
        country = _country_name(lki[0].get("country_code", "") or "")
    areas = [c["display_name"] for c in (a.get("x_concepts") or [])
             if (c.get("score") or 0) >= 20 and c.get("display_name")][:6]
    areas = areas or ["(see OpenAlex profile)"]
    stats = a.get("summary_stats") or {}
    h     = int(stats.get("h_index") or 0)
    cites = int(a.get("cited_by_count") or 0)
    orcid = (a.get("ids") or {}).get("orcid", "") or ""
    return {
        "name":         a.get("display_name", "Unknown"),
        "university":   inst,
        "department":   "",
        "title":        "Researcher (via OpenAlex)",
        "country":      country,
        "areas":        areas,
        "h_index":      h,
        "citations":    cites,
        "impact_score": _impact_from_hindex(h),
        "social_score": None,
        "top_cited":    [],
        "linkedin":     "",
        "twitter":      "",
        "website":      a.get("id", ""),   # OpenAlex canonical URL
        "scholar":      orcid,
        "email":        "",
        "ra_hiring":    None,
        "phd_students": "",
        "seeks":        "",
        "awards":       "",
        "works_count":  int(a.get("works_count") or 0),
        "_source":      "openalex",
    }

# ── Top-works fetch (lean payload) ──
@st.cache_data(ttl=21600, show_spinner=False)
def fetch_top_works(author_id: str, mailto=None, n=3) -> list[str]:
    data, err = _get(f"{OPENALEX_BASE}/works",
                     _params({"filter": f"author.id:{author_id}",
                              "sort": "cited_by_count:desc",
                              "per-page": n,
                              "select": "display_name,publication_year,cited_by_count"},
                             mailto))
    if err or not data:
        return []
    out = []
    for w in data.get("results", []):
        title = w.get("display_name") or "Untitled"
        year  = w.get("publication_year")
        cites = w.get("cited_by_count", 0) or 0
        label = f"{title} ({year})" if year else title
        out.append(f"{label} — {cites:,} citations")
    return out

def _author_to_prof(a: dict, mailto=None) -> dict:
    core = _author_core(a)
    aid  = (a.get("id", "") or "").split("/")[-1]
    if aid:
        core["top_cited"] = fetch_top_works(aid, mailto)
    return core

# ── Author search by name ──
@st.cache_data(ttl=21600, show_spinner=False)
def search_by_name(name: str, n: int, mailto=None) -> tuple[list, str | None]:
    data, err = _get(f"{OPENALEX_BASE}/authors",
                     _params({"search": name, "per-page": n}, mailto))
    if err:
        return [], err
    authors = data.get("results", []) if data else []
    # Fetch top works in parallel (one thread per author)
    results = []
    with ThreadPoolExecutor(max_workers=min(n, 5)) as ex:
        futs = {ex.submit(_author_to_prof, a, mailto): a for a in authors}
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception:
                pass
    results.sort(key=lambda p: p.get("citations", 0), reverse=True)
    return results, None

# ── Author search by field (lean: request only authorships + citations) ──
@st.cache_data(ttl=21600, show_spinner=False)
def search_by_field(topic: str, n: int, mailto=None) -> tuple[list, str | None]:
    data, err = _get(f"{OPENALEX_BASE}/works",
                     _params({"search": topic,
                              "sort":   "cited_by_count:desc",
                              "per-page": 50,
                              "select": "cited_by_count,authorships"},
                             mailto))
    if err:
        return [], err
    # Collect unique author IDs in citation-weighted order
    seen: dict[str, str] = {}  # id → display_name
    for w in (data or {}).get("results", []):
        for au in w.get("authorships", []):
            aobj = au.get("author") or {}
            aid  = aobj.get("id")
            if aid and aid not in seen:
                seen[aid] = aobj.get("display_name", "")
            if len(seen) >= n * 4:
                break

    # Fetch full author records in parallel
    def _fetch_one(aid):
        d, e = _get(f"{OPENALEX_BASE}/authors/{aid.split('/')[-1]}",
                    _params({}, mailto), label=f"author {aid[-8:]}")
        if e or not d:
            return None
        return _author_to_prof(d, mailto)

    out = []
    with ThreadPoolExecutor(max_workers=min(n, 5)) as ex:
        futs = {ex.submit(_fetch_one, aid): aid for aid in list(seen)[:n * 2]}
        for fut in as_completed(futs):
            try:
                p = fut.result()
                if p:
                    out.append(p)
            except Exception:
                pass
            if len(out) >= n:
                break

    out.sort(key=lambda p: p.get("citations", 0), reverse=True)
    return out[:n], None

def run_search(mode, query, n, mailto):
    if mode == "Research field / topic":
        return search_by_field(query, n, mailto)
    return search_by_name(query, n, mailto)

# ── Co-author resolution & fetch ──
@st.cache_data(ttl=21600, show_spinner=False)
def resolve_author_id(name: str, mailto=None) -> tuple[str | None, str | None, str | None]:
    """Resolve a professor name → (openalex_url, display_name, institution)."""
    data, err = _get(f"{OPENALEX_BASE}/authors",
                     _params({"search": name, "per-page": 1,
                              "select": "id,display_name,last_known_institutions"},
                             mailto))
    if err or not data:
        return None, None, None
    results = data.get("results", [])
    if not results:
        return None, None, None
    a    = results[0]
    inst = ""
    lki  = a.get("last_known_institutions") or []
    if lki and isinstance(lki[0], dict):
        inst = lki[0].get("display_name", "") or ""
    return a.get("id"), a.get("display_name"), inst

@st.cache_data(ttl=21600, show_spinner=False)
def fetch_coauthors(
    author_url: str,
    mailto=None,
    top_n: int = 15,
    max_works: int = 100,
) -> tuple[list, int, str | None]:
    """
    Aggregate co-authors from the author's most-cited works.

    Strategy
    --------
    • Fetch works in pages of 50 (not one huge 200-row request).
    • Use select= to pull only the three fields we need, cutting payload ~80 %.
    • Stop as soon as we have max_works worth of results.
    • All HTTP calls go through the retry session (_get), so transient 5xx /
      timeouts are retried automatically with back-off before surfacing an error.
    """
    if not author_url:
        return [], 0, "No OpenAlex author id."
    aid       = author_url.split("/")[-1]
    counts: dict[str, int]  = {}
    cocites: dict[str, int] = {}
    info:   dict[str, dict] = {}
    total_fetched = 0
    PAGE_SIZE = 50

    for page in range(1, (max_works // PAGE_SIZE) + 2):
        if total_fetched >= max_works:
            break
        data, err = _get(
            f"{OPENALEX_BASE}/works",
            _params({"filter":   f"author.id:{aid}",
                     "sort":     "cited_by_count:desc",
                     "per-page": PAGE_SIZE,
                     "page":     page,
                     "select":   "cited_by_count,authorships"},
                    mailto),
            label=f"works p{page}",
        )
        if err:
            if total_fetched == 0:
                return [], 0, err      # nothing yet — propagate the error
            break                      # got some pages already — use them
        results = (data or {}).get("results", [])
        if not results:
            break
        for w in results:
            wc = w.get("cited_by_count", 0) or 0
            for au in w.get("authorships", []):
                aobj = au.get("author") or {}
                cid  = aobj.get("id")
                if not cid or cid == author_url:
                    continue
                counts[cid]  = counts.get(cid, 0) + 1
                cocites[cid] = cocites.get(cid, 0) + wc
                if cid not in info:
                    insts = au.get("institutions") or []
                    iname = (insts[0].get("display_name", "")
                             if insts and isinstance(insts[0], dict) else "")
                    info[cid] = {"name": aobj.get("display_name", ""), "institution": iname}
        total_fetched += len(results)
        # If the page was smaller than PAGE_SIZE, there are no more pages
        if len(results) < PAGE_SIZE:
            break
        time.sleep(0.1)  # be a polite client between pages

    ranked = sorted(counts.items(),
                    key=lambda x: (x[1], cocites.get(x[0], 0)),
                    reverse=True)[:top_n]
    coauthors = [{
        "name":            info[cid]["name"],
        "institution":     info[cid]["institution"],
        "joint_works":     cnt,
        "joint_citations": cocites.get(cid, 0),
        "openalex":        cid,
    } for cid, cnt in ranked]
    return coauthors, total_fetched, None

def render_coauthors(p: dict, mailto, key_prefix: str = ""):
    name       = p.get("name", "")
    author_url = p.get("website") if p.get("_source") == "openalex" else None

    with st.spinner(f"Loading co-authors for {name}…"):
        resolved_inst = None
        if not author_url:
            author_url, _rn, resolved_inst = resolve_author_id(name, mailto)
        if not author_url:
            st.info(f"No OpenAlex profile found for **{name}**.")
            return
        coauthors, nworks, err = fetch_coauthors(author_url, mailto)

    if err:
        st.warning(f"⚠️ {err}")
        return
    if not coauthors:
        st.info("No co-authors found on OpenAlex for this author.")
        return
    if resolved_inst:
        st.caption(f"OpenAlex match: **{name}** — {resolved_inst}")

    st.markdown(
        f"**🔗 Top {len(coauthors)} co-authors** "
        f"(from {nworks} most-cited works · ranked by joint-work count, tie-broken by joint citations):"
    )
    ca_df = pd.DataFrame([{
        "Co-author":       c["name"],
        "Institution":     c["institution"] or "—",
        "Joint works":     c["joint_works"],
        "Joint citations": c["joint_citations"],
        "OpenAlex":        c["openalex"],
    } for c in coauthors])
    st.dataframe(
        ca_df, use_container_width=True, hide_index=True,
        column_config={"OpenAlex": st.column_config.LinkColumn("OpenAlex", display_text="profile ↗")},
    )
    chart_df = ca_df.head(10).sort_values("Joint works")
    fig = px.bar(
        chart_df, x="Joint works", y="Co-author", orientation="h",
        template="plotly_dark", color="Joint works", color_continuous_scale="Tealgrn",
        labels={"Joint works": "Joint works"},
    )
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True,
                    key=f"{key_prefix}_coauth_{(author_url or name)[-12:]}")

# ═══════════════════════════════════════
# HEADER
# ═══════════════════════════════════════
st.title("🤖 AI & Future of Work — Professor Directory")
n_found = len(st.session_state.extra_profs)
subtitle = f"**{len(seed_profs)} seeded professors**"
if n_found:
    subtitle += f" + **{n_found} found via search**"
subtitle += " researching AI, Automation, FinTech & the Future of Work"
st.markdown(subtitle)
st.markdown("---")

# ═══════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════
with st.sidebar:
    st.header("🔍 Filters")
    search = st.text_input("Search by name, university, or area", "")
    all_areas = sorted(set(a for p in profs for a in p["areas"]))
    selected_areas = st.multiselect("Research Areas", all_areas, default=[])
    all_countries = sorted(set(p["country"] for p in profs if p.get("country")))
    selected_countries = st.multiselect("Country", all_countries, default=[])
    all_unis = sorted(set(p["university"] for p in profs if p.get("university")))
    selected_unis = st.multiselect("University", all_unis, default=[])
    ra_only = st.checkbox("🟢 Hiring RAs / PhD Students Only", False)
    impact_range = st.slider("Impact Score Range", 0, 100, (0, 100))
    social_range = st.slider("Social Activeness Range", 0, 100, (0, 100))
    sort_by = st.selectbox("Sort By", ["Impact Score ↓", "Social Score ↓", "h-index ↓", "Citations ↓", "Name A-Z"])

    st.markdown("---")
    st.subheader("🔎 Live Search (free)")
    st.caption("Powered by OpenAlex — no API key or payment needed. Optionally add your email "
               "below to use OpenAlex's faster 'polite pool'.")
    st.text_input("Your email (optional)", key="openalex_mailto",
                  help="Optional. OpenAlex gives faster, more reliable responses when you identify yourself.")

# ═══════════════════════════════════════
# FILTERS
# ═══════════════════════════════════════
def apply_filters(plist):
    out = plist.copy()
    if search:
        s = search.lower()
        out = [p for p in out if s in p["name"].lower() or s in p.get("university", "").lower()
               or any(s in a.lower() for a in p["areas"]) or s in p.get("seeks", "").lower()]
    if selected_areas:
        out = [p for p in out if any(a in p["areas"] for a in selected_areas)]
    if selected_countries:
        out = [p for p in out if p.get("country") in selected_countries]
    if selected_unis:
        out = [p for p in out if p.get("university") in selected_unis]
    if ra_only:
        out = [p for p in out if p.get("ra_hiring")]
    out = [p for p in out if impact_range[0] <= p.get("impact_score", 0) <= impact_range[1]]

    def social_ok(p):
        sc = p.get("social_score")
        if sc is None:
            return social_range == (0, 100)   # unknown passes only when range isn't narrowed
        return social_range[0] <= sc <= social_range[1]
    out = [p for p in out if social_ok(p)]

    key = {"Impact Score ↓": ("impact_score", True), "Social Score ↓": ("social_score", True),
           "h-index ↓": ("h_index", True), "Citations ↓": ("citations", True), "Name A-Z": ("name", False)}[sort_by]
    out.sort(key=lambda p: (p.get(key[0]) is None, p.get(key[0]) or (0 if key[1] else "")), reverse=key[1])
    return out

filtered = apply_filters(profs)

# ═══════════════════════════════════════
# METRICS
# ═══════════════════════════════════════
social_vals = [p["social_score"] for p in filtered if p.get("social_score") is not None]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Professors", len(profs))
c2.metric("Showing", len(filtered))
c3.metric("Hiring RAs", sum(1 for p in filtered if p.get("ra_hiring")))
c4.metric("Avg Impact", f"{sum(p.get('impact_score',0) for p in filtered)/max(len(filtered),1):.0f}")
c5.metric("Avg Social", f"{sum(social_vals)/len(social_vals):.0f}" if social_vals else "—")
st.markdown("---")

# ═══════════════════════════════════════
# TABS
# ═══════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Professor Profiles", "🔎 Find New Professors", "📊 Analytics", "📄 Top Cited Works", "📥 Download Data"
])

def render_professor(p, found=False):
    badge = " 🟢" if found else ""
    soc = p.get("social_score")
    soc_disp = soc if soc is not None else "N/A"
    header = f"**{p['name']}**{badge} — {p.get('university','')} ({p.get('title','')})  |  Impact: {p.get('impact_score','?')}  |  Social: {soc_disp}"
    with st.expander(header):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Department:** {p.get('department','') or '—'}")
            st.markdown(f"**Country:** {p.get('country','') or '—'}")
            st.markdown(f"**Research Areas:** {', '.join(p.get('areas', []))}")
            if p.get("seeks"):
                st.markdown(f"**What They Seek:** {p['seeks']}")
            if p.get("phd_students"):
                st.markdown(f"**Students/Lab:** {p['phd_students']}")
            if p.get("awards"):
                st.markdown(f"🏆 **Awards:** {p['awards']}")
            if p.get("_source") == "openalex":
                st.caption("Source: OpenAlex (live). Social score unavailable from free academic data.")
        with col2:
            st.metric("Impact Score", p.get("impact_score", "?"))
            st.metric("h-index", p.get("h_index", "?"))
            cites = p.get("citations", 0)
            st.metric("Citations", f"{cites:,}" if isinstance(cites, int) else cites)
            st.metric("Social Score", soc_disp)
            ra = p.get("ra_hiring")
            ra_status = "✅ Yes" if ra else ("❓ Unknown" if ra is None else "❌ No")
            st.markdown(f"**Hiring RAs:** {ra_status}")
        if p.get("top_cited"):
            st.markdown("**📝 Most Cited Works:**")
            for paper in p["top_cited"]:
                st.markdown(f"- {paper}")
        links = []
        if p.get("email"): links.append(f"📧 [{p['email']}](mailto:{p['email']})")
        if p.get("website"): links.append(f"🌐 [Profile/Website]({p['website']})")
        if p.get("scholar"): links.append(f"🎓 [Scholar/ORCID]({p['scholar']})")
        if p.get("twitter"): links.append(f"🐦 {p['twitter']}")
        if p.get("linkedin"): links.append(f"💼 {p['linkedin']}")
        if links:
            st.markdown(" | ".join(links))

        # Co-author lookup (live from OpenAlex)
        st.markdown("---")
        ckey = p.get("website") or p.get("name", "")
        mailto_local = st.session_state.get("openalex_mailto", "") or None
        if ckey in st.session_state.coauthors_show:
            render_coauthors(p, mailto_local, key_prefix="card")
            if st.button("Hide co-authors", key=f"hide_coauth_{ckey}"):
                st.session_state.coauthors_show.discard(ckey)
                st.rerun()
        else:
            if st.button("🔗 Show top co-authors (OpenAlex)", key=f"show_coauth_{ckey}"):
                st.session_state.coauthors_show.add(ckey)
                st.rerun()

# ── TAB 1 ──
with tab1:
    if not filtered:
        st.info("No professors match your filters. Try widening them, or use **Find New Professors** to search the web.")
    for p in filtered:
        render_professor(p, found=(p in st.session_state.extra_profs))

# ── TAB 2: FIND NEW PROFESSORS (OpenAlex) ──
with tab2:
    st.subheader("🔎 Find Professors Beyond the Database — Free, No API Key")
    st.markdown("Searches **OpenAlex**, an open catalog of 240M+ scholarly works. Returns real citation "
                "counts, h-index, institutions, and most-cited works. Found professors are added to every "
                "tab for this session. **Searching by professor name also shows their top co-authors.**")
    st.info("ℹ️ OpenAlex provides academic metrics only. **Social activeness scores aren't available** "
            "from free data, so searched professors show *Social: N/A*. Impact, h-index, citations and "
            "works are all real.")

    mailto = st.session_state.get("openalex_mailto", "") or None

    mode = st.radio("Search by", ["Research field / topic", "Professor name"], horizontal=True)
    colq, coln = st.columns([4, 1])
    with colq:
        if mode == "Research field / topic":
            query = st.text_input("Topic / field",
                                   placeholder="e.g. 'artificial intelligence labor economics' or 'fintech credit'")
        else:
            query = st.text_input("Professor name", placeholder="e.g. 'Daniel Kahneman'")
    with coln:
        n_results = st.number_input("# results", min_value=1, max_value=10, value=5)

    st.caption("Quick field searches:")
    suggestions = [
        "artificial intelligence automation labor",
        "generative AI productivity",
        "machine learning asset pricing",
        "fintech financial inclusion",
        "future of work economics",
    ]
    scols = st.columns(len(suggestions))
    clicked = None
    for i, s in enumerate(suggestions):
        if scols[i].button(s, key=f"sugg_{i}"):
            clicked = s

    do_search = st.button("🔍 Search OpenAlex", type="primary")
    active_query = clicked or (query if do_search else None)
    active_mode = "Research field / topic" if clicked else mode

    if active_query:
        with st.spinner(f"Searching OpenAlex for: {active_query} ..."):
            results, err = run_search(active_mode, active_query, int(n_results), mailto)
        if err:
            st.error(err)
        elif not results:
            st.warning("No researchers found. Try different keywords or the other search mode.")
        else:
            existing = {p["name"].lower() for p in profs}
            new_results = [r for r in results if r.get("name", "").lower() not in existing]
            if not new_results:
                st.warning("All matches are already in your directory. Try a different query.")
            else:
                st.success(f"Found {len(new_results)} researcher(s). Review and click **Add** to include them.")
                for idx, r in enumerate(new_results):
                    st.markdown(f"### {r.get('name','Unknown')} — {r.get('university','(institution unknown)')}")
                    cc1, cc2 = st.columns([3, 1])
                    with cc1:
                        st.markdown(f"**{r.get('country','')}**")
                        st.markdown(f"**Areas:** {', '.join(r.get('areas', []))}")
                        if r.get("top_cited"):
                            st.markdown("**Top works:**")
                            for w in r["top_cited"]:
                                st.markdown(f"- {w}")
                        links = []
                        if r.get("website"): links.append(f"[OpenAlex profile]({r['website']})")
                        if r.get("scholar"): links.append(f"[ORCID]({r['scholar']})")
                        if links:
                            st.markdown(" | ".join(links))
                    with cc2:
                        st.metric("Impact (est.)", r.get("impact_score", "?"))
                        st.metric("h-index", r.get("h_index", "?"))
                        st.metric("Citations", f"{r.get('citations',0):,}")
                        st.caption("Social: N/A")
                    # Co-authors: shown automatically for name searches, on-demand for field searches
                    mailto_res = st.session_state.get("openalex_mailto", "") or None
                    if active_mode == "Professor name":
                        with st.expander(f"🔗 Top co-authors of {r.get('name','')}", expanded=True):
                            render_coauthors(r, mailto_res, key_prefix=f"search{idx}")
                    else:
                        rk = r.get("website") or r.get("name", "")
                        if rk in st.session_state.coauthors_show:
                            render_coauthors(r, mailto_res, key_prefix=f"search{idx}")
                        elif st.button(f"🔗 Show co-authors of {r.get('name','')}", key=f"sc_show_{idx}_{rk}"):
                            st.session_state.coauthors_show.add(rk)
                            st.rerun()
                    if st.button(f"➕ Add {r.get('name','')}", key=f"add_{idx}_{r.get('name','')}"):
                        st.session_state.extra_profs.append(r)
                        st.success(f"Added {r.get('name','')}!")
                        st.rerun()

                if len(new_results) > 1 and st.button("➕➕ Add ALL", key="add_all"):
                    have = {p["name"].lower() for p in (seed_profs + st.session_state.extra_profs)}
                    for r in new_results:
                        if r.get("name", "").lower() not in have:
                            st.session_state.extra_profs.append(r)
                    st.success(f"Added {len(new_results)} researcher(s)!")
                    st.rerun()

    if st.session_state.extra_profs:
        st.markdown("---")
        st.markdown(f"**🟢 {len(st.session_state.extra_profs)} added via search this session:** "
                    + ", ".join(p["name"] for p in st.session_state.extra_profs))
        if st.button("🗑️ Clear all found professors"):
            st.session_state.extra_profs = []
            st.rerun()

# ── TAB 3: ANALYTICS ──
with tab3:
    st.subheader("Impact Score vs Social Activeness")
    if filtered:
        fig_df = pd.DataFrame(filtered)
        fig_df["source"] = ["Found via Search" if p in st.session_state.extra_profs else "Seeded" for p in filtered]
        scatter_df = fig_df.copy()
        scatter_df["social_score"] = pd.to_numeric(scatter_df["social_score"], errors="coerce")
        dropped = int(scatter_df["social_score"].isna().sum())
        scatter_df = scatter_df.dropna(subset=["social_score"])
        if len(scatter_df):
            fig = px.scatter(scatter_df, x="social_score", y="impact_score", size="h_index",
                             color="source", symbol="source", hover_name="name",
                             hover_data=["university", "h_index", "citations"],
                             labels={"social_score": "Social Activeness Score", "impact_score": "Academic Impact Score"},
                             size_max=45, template="plotly_dark",
                             color_discrete_map={"Seeded": "#4A90D9", "Found via Search": "#2ECC71"})
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        if dropped:
            st.caption(f"Note: {dropped} searched professor(s) omitted from this chart — social scores aren't "
                       "available from OpenAlex. They still appear in the impact chart and all other tabs.")

        st.subheader("Top 15 by Impact Score")
        top15 = fig_df.nlargest(15, "impact_score")
        fig2 = px.bar(top15, x="name", y="impact_score", color="impact_score",
                      color_continuous_scale="Reds", template="plotly_dark",
                      labels={"impact_score": "Impact Score", "name": "Professor"})
        fig2.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

        seeded_social = fig_df[fig_df["source"] == "Seeded"]
        if len(seeded_social):
            st.subheader("Top 15 by Social Activeness (seeded professors)")
            top15s = seeded_social.nlargest(15, "social_score")
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
    if len(works_df):
        sw = st.text_input("Search works", "", key="search_works")
        if sw:
            works_df = works_df[works_df.apply(
                lambda r: sw.lower() in str(r["Work"]).lower() or sw.lower() in str(r["Professor"]).lower(), axis=1)]
        st.dataframe(works_df, use_container_width=True, height=600)
    else:
        st.info("No works to show with current filters.")

# ── TAB 5: DOWNLOAD ──
with tab5:
    st.subheader("Download Database")
    st.caption("Includes both seeded professors and any found via live search this session.")
    csv_df = pd.DataFrame([{
        "Name": p.get("name", ""), "University": p.get("university", ""), "Department": p.get("department", ""),
        "Title": p.get("title", ""), "Country": p.get("country", ""), "Areas": "; ".join(p.get("areas", [])),
        "h_index": p.get("h_index", 0), "Citations": p.get("citations", 0), "Impact_Score": p.get("impact_score", 0),
        "Social_Score": p.get("social_score") if p.get("social_score") is not None else "N/A",
        "Hiring_RAs": p.get("ra_hiring", ""), "Email": p.get("email", ""), "Twitter": p.get("twitter", ""),
        "LinkedIn": p.get("linkedin", ""), "Website": p.get("website", ""), "Scholar": p.get("scholar", ""),
        "Seeks": p.get("seeks", ""), "Awards": p.get("awards", ""),
        "Top_Cited": " | ".join(p.get("top_cited", [])[:3]),
        "Source": "Found via Search (OpenAlex)" if p in st.session_state.extra_profs else "Seeded"
    } for p in profs])
    st.download_button("📥 Download CSV (all professors)", csv_df.to_csv(index=False), "ai_professors.csv", "text/csv")
    st.download_button("📥 Download JSON (all professors)", json.dumps(profs, indent=2), "ai_professors.json", "application/json")
    if st.session_state.extra_profs:
        st.download_button("📥 Download ONLY found professors (JSON)",
                           json.dumps(st.session_state.extra_profs, indent=2), "found_professors.json", "application/json")

    st.markdown("---")
    st.markdown("### How to Host This App")
    st.code("""
# 1. Install dependencies
pip install -r requirements.txt

# 2. Keep these files together:
#    app.py, professors_data.json, requirements.txt

# 3. Run locally:
streamlit run app.py

# 4. Deploy free on Streamlit Community Cloud:
#    - Push to GitHub
#    - Go to share.streamlit.io, connect the repo, deploy
#    No API keys or secrets required - search runs on free OpenAlex.
    """, language="bash")
