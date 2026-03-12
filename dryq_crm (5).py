import streamlit as st
import pandas as pd
import math
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# DryQ CRM — Airtable-Backed Version with corrected 12-month LTV revenue model
# Pricing: $28 retail, $24 early supporter, $14 wholesale
# ═══════════════════════════════════════════════════════════════════════════════

from pyairtable import Api

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DryQ CRM",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ────────────────────────────────────────────────────────────────
TEAM_MEMBERS = ["Unassigned", "JT", "CB", "JM", "JP", "AW"]
STATUSES = ["New", "Contacted", "Qualified", "Negotiating", "Won", "Lost"]
LEAD_TYPES = ["Run Club", "Specialty Shop", "Influencer"]

COLUMNS = [
    "Lead Name", "Lead Type", "Location", "Audience Size",
    "Engagement Score", "Est Weekly Turnout", "Num Locations",
    "Charlotte Hub", "Notes", "Status", "Assigned To", "Last Updated",
]

# ── Pricing constants ────────────────────────────────────────────────────────
RETAIL_PRICE     = 28   # consumer / run club
WHOLESALE_PRICE  = 14   # specialty shops
RESTOCKS_PER_YEAR = 4   # shop restock cycles
UNITS_PER_RESTOCK = 15  # units per location per restock
INFLUENCER_POSTS  = 2   # estimated posts/year per influencer
INFLUENCER_CVR    = 0.005  # 0.5% audience conversion

# ── Revenue ceilings for score normalisation ─────────────────────────────────
RC_CEILING   = 29120   # 200 turnout × 10% × $28 × 52
SHOP_CEILING = 2520    # 3 locs × 15 units × $14 × 4 restocks
INF_CEILING  = 30520   # 109k audience × 0.5% × $28 × 2

# ── DryQ Logo ────────────────────────────────────────────────────────────────
LOGO_B64 = "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"

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'Barlow', sans-serif; background-color: #0e1117; color: #e8e8e8; }
  h1, h2, h3, h4 { font-family: 'Barlow Condensed', sans-serif; letter-spacing: 0.04em; }
  section[data-testid="stSidebar"] { background-color: #161b22; border-right: 2px solid #FF4B00; }
  section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
  [data-testid="metric-container"] { background: #161b22; border: 1px solid #2a2f3a; border-radius: 8px; padding: 1rem; border-left: 4px solid #FF4B00; }
  .section-header { font-family: 'Barlow Condensed', sans-serif; font-size: 1.6rem; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.08em; border-bottom: 2px solid #FF4B00; padding-bottom: 4px; margin-bottom: 1rem; }
  .tag { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; font-family: 'Barlow Condensed', sans-serif; letter-spacing: 0.05em; text-transform: uppercase; }
  .tag-runclub { background:#FF4B00; color:#fff; }
  .tag-shop { background:#FFB300; color:#000; }
  .tag-influencer { background:#00C9A7; color:#000; }
</style>
""", unsafe_allow_html=True)


# ── Airtable ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_table():
    api = Api(st.secrets["AIRTABLE_API_KEY"])
    return api.table(st.secrets["AIRTABLE_BASE_ID"], "Leads")


def load_leads():
    try:
        records = get_table().all()
        if not records:
            return pd.DataFrame(columns=COLUMNS + ["_airtable_id"])
        rows = []
        for r in records:
            f = r["fields"].copy()
            f["_airtable_id"] = r["id"]
            rows.append(f)
        df = pd.DataFrame(rows)
        defaults = {
            "Lead Name": "", "Lead Type": "Run Club", "Location": "",
            "Audience Size": 0, "Engagement Score": 5, "Est Weekly Turnout": 0,
            "Num Locations": 1, "Charlotte Hub": False, "Notes": "",
            "Status": "New", "Assigned To": "Unassigned", "Last Updated": "",
            "_airtable_id": "",
        }
        for col, default in defaults.items():
            if col not in df.columns:
                df[col] = default
        for col in ["Audience Size", "Engagement Score", "Est Weekly Turnout", "Num Locations"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        df["Charlotte Hub"] = df["Charlotte Hub"].fillna(False).astype(bool)
        return df
    except Exception as e:
        st.error(f"⚠️ Could not connect to Airtable: {e}")
        return pd.DataFrame(columns=COLUMNS + ["_airtable_id"])


def airtable_fields(row_dict):
    skip = {"_airtable_id", "Est Revenue 12mo ($)", "Priority Score", "Priority Tier"}
    return {k: v for k, v in row_dict.items() if k not in skip}

def create_lead(fields):
    r = get_table().create(airtable_fields(fields))
    return r["id"]

def update_lead(airtable_id, fields):
    get_table().update(airtable_id, airtable_fields(fields))

def delete_lead(airtable_id):
    get_table().delete(airtable_id)


# ── 12-Month LTV Revenue ─────────────────────────────────────────────────────
def estimated_revenue(row):
    lt = row["Lead Type"]
    if lt == "Run Club":
        # Weekly turnout × 10% conversion × $28 retail × 52 weeks
        return round(row.get("Est Weekly Turnout", 0) * 0.10 * RETAIL_PRICE * 52)
    elif lt == "Specialty Shop":
        # Locations × 15 units × $14 wholesale × 4 restocks/year
        return round(row.get("Num Locations", 1) * UNITS_PER_RESTOCK * WHOLESALE_PRICE * RESTOCKS_PER_YEAR)
    elif lt == "Influencer":
        # Audience × 0.5% conversion × $28 retail × 2 posts/year
        return round(row["Audience Size"] * INFLUENCER_CVR * RETAIL_PRICE * INFLUENCER_POSTS)
    return 0


# ── Priority Score (normalised to 12mo revenue ceilings) ────────────────────
def calculate_priority(row):
    lt  = row["Lead Type"]
    eng = row["Engagement Score"]
    rev = estimated_revenue(row)
    hub = row["Charlotte Hub"]

    if lt == "Run Club":
        score = min(100, (rev / RC_CEILING) * 100)
        if hub: score = min(100, score * 1.25)

    elif lt == "Specialty Shop":
        score = min(100, (rev / SHOP_CEILING) * 100)
        if hub: score = min(100, score * 1.15)

    elif lt == "Influencer":
        # Blend revenue potential with engagement quality
        rev_score = min(100, (rev / INF_CEILING) * 100)
        eng_score = (eng / 10) * 100
        score = (rev_score * 0.6) + (eng_score * 0.4)
        score = min(100, score)
        if hub: score = min(100, score * 1.10)
    else:
        score = 0

    return round(score)


def priority_tier(score):
    if score >= 60: return "🔴 High"
    if score >= 30: return "🟡 Medium"
    return "⚪ Low"


# ── Session State ─────────────────────────────────────────────────────────────
if "leads_df" not in st.session_state:
    st.session_state.leads_df = load_leads()
    st.session_state.last_loaded = datetime.now()

df = st.session_state.leads_df.copy()
df["Est Revenue 12mo ($)"] = df.apply(estimated_revenue, axis=1)
df["Priority Score"]       = df.apply(calculate_priority, axis=1)
df["Priority Tier"]        = df["Priority Score"].apply(priority_tier)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:10px;">
        <img src="data:image/jpeg;base64,{LOGO_B64}" alt="DryQ" style="height:60px; border-radius:8px; margin-bottom:6px;" />
        <h2 style="font-family:'Barlow Condensed',sans-serif; color:#ffffff; margin:0; font-size:1.6rem; letter-spacing:0.06em;">CRM</h2>
        <p style="color:#666; font-size:0.75rem; margin-top:2px;">Sweat-Resistant Runner Pouch</p>
        <p style="color:#555; font-size:0.7rem;">$28 retail · $24 early · $14 wholesale</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="text-align:center; margin-bottom:8px;"><span style="background:#1a2a1a; border:1px solid #2a5a2a; color:#4CAF50; padding:2px 10px; border-radius:20px; font-size:0.72rem;">● Live · Airtable</span></div>', unsafe_allow_html=True)

    if st.button("🔄 Refresh from Airtable", use_container_width=True):
        st.session_state.leads_df = load_leads()
        st.session_state.last_loaded = datetime.now()
        st.rerun()

    st.markdown("---")
    type_filter   = st.multiselect("Filter by Lead Type", options=LEAD_TYPES, default=LEAD_TYPES)
    status_filter = st.multiselect("Filter by Status", options=STATUSES, default=STATUSES)
    hub_only      = st.checkbox("Charlotte Hub Only", value=False)
    tier_filter   = st.multiselect("Filter by Priority Tier", options=["🔴 High", "🟡 Medium", "⚪ Low"], default=["🔴 High", "🟡 Medium", "⚪ Low"])
    min_score, max_score = st.slider("Priority Score Range", 0, 100, (0, 100), step=5)
    search        = st.text_input("🔍 Search Lead Name / Location", "")
    st.markdown("---")
    st.caption("Phase: Prototype / Early Testing")
    st.caption("Hub: Charlotte, NC")


# ── Filter ────────────────────────────────────────────────────────────────────
filtered = df[
    df["Lead Type"].isin(type_filter)
    & df["Status"].isin(status_filter)
    & df["Priority Tier"].isin(tier_filter)
    & df["Priority Score"].between(min_score, max_score)
]
if hub_only:
    filtered = filtered[filtered["Charlotte Hub"] == True]
if search:
    mask = (
        filtered["Lead Name"].str.contains(search, case=False, na=False)
        | filtered["Location"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]
filtered = filtered.sort_values("Priority Score", ascending=False)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="font-family:'Barlow Condensed',sans-serif; font-size:2.8rem; font-weight:800; letter-spacing:0.06em; color:#ffffff; margin-bottom:0;">
  DRYQ CRM
</h1>
<p style="color:#888; margin-top:2px; font-size:1rem;">
  Lead Prioritization Dashboard · Sweat-Resistant Runner Pouch · Charlotte Hub
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Leads",          len(filtered))
c2.metric("🔴 High Priority",     len(filtered[filtered["Priority Tier"] == "🔴 High"]))
c3.metric("CLT Hub Leads",        len(filtered[filtered["Charlotte Hub"] == True]))
c4.metric("Est. 12mo Revenue",    f"${filtered['Est Revenue 12mo ($)'].sum():,.0f}")
c5.metric("Avg Engagement",       f"{filtered['Engagement Score'].mean():.1f}/10" if len(filtered) else "—")
st.markdown("---")


# ── Add Lead ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">➕ Add New Lead</div>', unsafe_allow_html=True)
with st.expander("Click to add a new lead", expanded=False):
    with st.form("add_lead_form", clear_on_submit=True):
        a1, a2, a3 = st.columns(3)
        with a1:
            new_name     = st.text_input("Lead Name *", placeholder="e.g. South End Runners")
            new_type     = st.selectbox("Lead Type", LEAD_TYPES)
            new_location = st.text_input("Location", placeholder="e.g. South End, Charlotte")
            new_hub      = st.checkbox("Charlotte Hub")
        with a2:
            new_audience   = st.number_input("Audience Size", min_value=0, value=0)
            new_engagement = st.slider("Engagement Score", 1, 10, 5)
            new_status     = st.selectbox("Status", STATUSES)
            new_assigned   = st.selectbox("Assign To", TEAM_MEMBERS)
        with a3:
            new_turnout   = st.number_input("Est Weekly Turnout (Run Clubs)", min_value=0, value=0)
            new_locations = st.number_input("Num Locations (Shops)", min_value=0, value=1)
            new_notes     = st.text_area("Notes", height=100)

        if st.form_submit_button("Add Lead", type="primary", use_container_width=True):
            if not new_name.strip():
                st.error("Lead name is required.")
            else:
                new_lead = {
                    "Lead Name": new_name.strip(), "Lead Type": new_type,
                    "Location": new_location, "Audience Size": new_audience,
                    "Engagement Score": new_engagement, "Est Weekly Turnout": new_turnout,
                    "Num Locations": new_locations, "Charlotte Hub": new_hub,
                    "Notes": new_notes, "Status": new_status, "Assigned To": new_assigned,
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                try:
                    new_lead["_airtable_id"] = create_lead(new_lead)
                    st.session_state.leads_df = pd.concat(
                        [st.session_state.leads_df, pd.DataFrame([new_lead])], ignore_index=True
                    )
                    st.success(f"✅ '{new_name}' saved to Airtable!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to save: {e}")

st.markdown("---")


# ── Pipeline Table ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Lead Pipeline</div>', unsafe_allow_html=True)

display_cols = [
    "Lead Name", "Lead Type", "Location", "Status", "Assigned To",
    "Audience Size", "Engagement Score", "Est Revenue 12mo ($)",
    "Priority Score", "Priority Tier", "Charlotte Hub", "Notes",
]

def color_rows(row):
    t = row["Priority Tier"]
    if t == "🔴 High":   return ["background-color: rgba(255,75,0,0.12)"] * len(row)
    if t == "🟡 Medium": return ["background-color: rgba(255,179,0,0.08)"] * len(row)
    return ["background-color: rgba(60,60,60,0.08)"] * len(row)

def color_score(val):
    if val >= 60: return "color: #FF4B00; font-weight: 700;"
    if val >= 30: return "color: #FFB300; font-weight: 600;"
    return "color: #888;"

styled = (
    filtered[display_cols].style
    .apply(color_rows, axis=1)
    .map(color_score, subset=["Priority Score"])
    .format({"Est Revenue 12mo ($)": "${:,.0f}", "Priority Score": "{:.0f}"})
    .set_properties(**{"font-size": "0.88rem"})
)
st.dataframe(styled, use_container_width=True, height=450)
st.markdown("---")


# ── Update / Assign ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">✏️ Update & Assign Leads</div>', unsafe_allow_html=True)
lead_names = st.session_state.leads_df["Lead Name"].tolist()

if lead_names:
    selected = st.selectbox("Select a lead to update", lead_names)
    idx      = st.session_state.leads_df[st.session_state.leads_df["Lead Name"] == selected].index[0]
    ld       = st.session_state.leads_df.loc[idx]

    with st.form("update_lead_form"):
        u1, u2, u3 = st.columns(3)
        with u1:
            upd_name     = st.text_input("Lead Name",  value=ld["Lead Name"])
            upd_type     = st.selectbox("Lead Type",   LEAD_TYPES, index=LEAD_TYPES.index(ld["Lead Type"]))
            upd_location = st.text_input("Location",   value=ld["Location"])
            upd_hub      = st.checkbox("Charlotte Hub", value=bool(ld["Charlotte Hub"]))
        with u2:
            upd_status   = st.selectbox("Status",    STATUSES,     index=STATUSES.index(ld.get("Status","New")) if ld.get("Status","New") in STATUSES else 0)
            upd_assigned = st.selectbox("Assign To", TEAM_MEMBERS, index=TEAM_MEMBERS.index(ld.get("Assigned To","Unassigned")) if ld.get("Assigned To","Unassigned") in TEAM_MEMBERS else 0)
            upd_audience   = st.number_input("Audience Size",     min_value=0, value=int(ld["Audience Size"]))
            upd_engagement = st.slider("Engagement Score", 1, 10,  int(ld["Engagement Score"]))
        with u3:
            upd_turnout   = st.number_input("Est Weekly Turnout", min_value=0, value=int(ld["Est Weekly Turnout"]))
            upd_locations = st.number_input("Num Locations",      min_value=0, value=int(ld["Num Locations"]))
            upd_notes     = st.text_area("Notes", value=ld.get("Notes", ""))

        b1, b2 = st.columns([3, 1])
        with b1: update_btn = st.form_submit_button("💾 Save Changes",  type="primary", use_container_width=True)
        with b2: delete_btn = st.form_submit_button("🗑️ Delete Lead",                   use_container_width=True)

        if update_btn:
            updated = {
                "Lead Name": upd_name, "Lead Type": upd_type, "Location": upd_location,
                "Audience Size": upd_audience, "Engagement Score": upd_engagement,
                "Est Weekly Turnout": upd_turnout, "Num Locations": upd_locations,
                "Charlotte Hub": upd_hub, "Notes": upd_notes, "Status": upd_status,
                "Assigned To": upd_assigned,
                "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            try:
                aid = ld.get("_airtable_id", "")
                if aid: update_lead(aid, updated)
                updated["_airtable_id"] = aid
                for k, v in updated.items():
                    st.session_state.leads_df.loc[idx, k] = v
                st.success(f"✅ '{upd_name}' updated!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

        if delete_btn:
            try:
                aid = ld.get("_airtable_id", "")
                if aid: delete_lead(aid)
                st.session_state.leads_df = st.session_state.leads_df.drop(idx).reset_index(drop=True)
                st.success(f"🗑️ '{selected}' deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Delete failed: {e}")


# ── Quick Assign ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">⚡ Quick Assign</div>', unsafe_allow_html=True)
unassigned = st.session_state.leads_df[st.session_state.leads_df["Assigned To"] == "Unassigned"]["Lead Name"].tolist()

if unassigned:
    st.info(f"**{len(unassigned)} unassigned leads** need attention.")
    qa_cols = st.columns(min(len(unassigned), 4))
    for i, name in enumerate(unassigned[:8]):
        with qa_cols[i % len(qa_cols)]:
            new_owner = st.selectbox(name, TEAM_MEMBERS, key=f"qa_{i}")
            if new_owner != "Unassigned":
                qidx = st.session_state.leads_df[st.session_state.leads_df["Lead Name"] == name].index[0]
                aid  = st.session_state.leads_df.loc[qidx, "_airtable_id"]
                ts   = datetime.now().strftime("%Y-%m-%d %H:%M")
                try:
                    if aid: update_lead(aid, {"Assigned To": new_owner, "Last Updated": ts})
                    st.session_state.leads_df.loc[qidx, "Assigned To"] = new_owner
                    st.session_state.leads_df.loc[qidx, "Last Updated"] = ts
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Quick assign failed: {e}")
else:
    st.success("All leads are assigned!")


# ── Analytics ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">Analytics</div>', unsafe_allow_html=True)
ca, cb, cc = st.columns(3)
with ca:
    st.markdown("**12mo Revenue Potential by Lead Type**")
    st.bar_chart(filtered.groupby("Lead Type")["Est Revenue 12mo ($)"].sum().reset_index().set_index("Lead Type"), color="#FF4B00")
with cb:
    st.markdown("**Priority Score Distribution**")
    st.bar_chart(filtered[["Lead Name","Priority Score"]].set_index("Lead Name").sort_values("Priority Score"), color="#FFB300")
with cc:
    st.markdown("**Leads by Status**")
    sc = filtered["Status"].value_counts().reset_index()
    sc.columns = ["Status","Count"]
    st.bar_chart(sc.set_index("Status"), color="#00C9A7")


# ── Formula Guide ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">Revenue Model — 12-Month LTV</div>', unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown(f"""
**🔴 Run Clubs**

`Weekly Turnout × 10% × $28 × 52 weeks`

Ceiling: **$29,120** (200 turnout/week)

Charlotte Hub **+25%** boost.

*Mad Miles @ 120 → ~$17,472/yr*
""")
with f2:
    st.markdown(f"""
**🟡 Specialty Shops**

`Locations × 15 units × $14 wholesale × 4 restocks`

Ceiling: **$2,520** (3 locations)

Charlotte Hub **+15%** boost.

*Charlotte Running Co. (2 loc) → $1,680/yr*
""")
with f3:
    st.markdown(f"""
**🟢 Influencers**

`Audience × 0.5% × $28 × 2 posts/year`

Score = 60% revenue + 40% engagement

Ceiling: **$30,520** (109k audience)

Charlotte Hub **+10%** boost.
""")


# ── Export ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.download_button(
    label="⬇️ Export Filtered Leads as CSV",
    data=filtered[display_cols].to_csv(index=False),
    file_name="dryq_crm_leads.csv",
    mime="text/csv",
)
st.caption("DryQ CRM · $28 retail · $24 early supporter · $14 wholesale · 12-month LTV model")
