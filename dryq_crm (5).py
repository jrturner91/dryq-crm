import streamlit as st
import pandas as pd
import math
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# DryQ CRM — Airtable-Backed Version
# ═══════════════════════════════════════════════════════════════════════════════
# Setup:
#   1. pip install pyairtable (add to requirements.txt)
#   2. In Streamlit Cloud → Settings → Secrets, add:
#        AIRTABLE_API_KEY = "patXXXXXXXXXXXXXX"
#        AIRTABLE_BASE_ID = "appXXXXXXXXXXXXXX"
#   3. Create an Airtable base called "DryQ CRM" with a table called "Leads"
#      Fields: Lead Name (text), Lead Type (single select), Location (text),
#              Audience Size (number), Engagement Score (number),
#              Est Weekly Turnout (number), Num Locations (number),
#              Charlotte Hub (checkbox), Notes (long text),
#              Status (single select), Assigned To (single select),
#              Last Updated (text)
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

# ── DryQ Logo (base64 embedded) ─────────────────────────────────────────────
LOGO_B64 = "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"

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0e1117;
    color: #e8e8e8;
  }
  h1, h2, h3, h4 { font-family: 'Barlow Condensed', sans-serif; letter-spacing: 0.04em; }

  section[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 2px solid #FF4B00;
  }
  section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

  [data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #2a2f3a;
    border-radius: 8px;
    padding: 1rem;
    border-left: 4px solid #FF4B00;
  }

  .section-header {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-bottom: 2px solid #FF4B00;
    padding-bottom: 4px;
    margin-bottom: 1rem;
  }

  .tag {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .tag-runclub    { background:#FF4B00; color:#fff; }
  .tag-shop       { background:#FFB300; color:#000; }
  .tag-influencer { background:#00C9A7; color:#000; }

  .sync-badge {
    display: inline-block;
    background: #1a2a1a;
    border: 1px solid #2a5a2a;
    color: #4CAF50;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 0.05em;
  }
  .sync-badge-err {
    background: #2a1a1a;
    border-color: #5a2a2a;
    color: #FF4B00;
  }
</style>
""", unsafe_allow_html=True)


# ── Airtable Connection ──────────────────────────────────────────────────────
@st.cache_resource
def get_table():
    api = Api(st.secrets["AIRTABLE_API_KEY"])
    return api.table(st.secrets["AIRTABLE_BASE_ID"], "Leads")


# ── Load from Airtable ───────────────────────────────────────────────────────
def load_leads():
    """Pull all records from Airtable and return as DataFrame."""
    try:
        table = get_table()
        records = table.all()
        if not records:
            return pd.DataFrame(columns=COLUMNS + ["_airtable_id"])
        rows = []
        for r in records:
            f = r["fields"].copy()
            f["_airtable_id"] = r["id"]
            rows.append(f)
        df = pd.DataFrame(rows)
        # Ensure all expected columns exist with safe defaults
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
        # Coerce numeric columns
        for col in ["Audience Size", "Engagement Score", "Est Weekly Turnout", "Num Locations"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        df["Charlotte Hub"] = df["Charlotte Hub"].fillna(False).astype(bool)
        return df
    except Exception as e:
        st.error(f"⚠️ Could not connect to Airtable: {e}")
        return pd.DataFrame(columns=COLUMNS + ["_airtable_id"])


# ── Push helpers ─────────────────────────────────────────────────────────────
def airtable_fields(row_dict):
    """Strip internal keys and prep a clean dict for Airtable."""
    skip = {"_airtable_id", "Est Revenue Potential ($)", "Priority Score", "Priority Tier"}
    return {k: v for k, v in row_dict.items() if k not in skip}


def create_lead(fields: dict):
    table = get_table()
    record = table.create(airtable_fields(fields))
    return record["id"]


def update_lead(airtable_id: str, fields: dict):
    table = get_table()
    table.update(airtable_id, airtable_fields(fields))


def delete_lead(airtable_id: str):
    table = get_table()
    table.delete(airtable_id)


# ── Priority & Revenue Calculations ─────────────────────────────────────────
def calculate_priority(row):
    score = 0
    lt = row["Lead Type"]
    eng = row["Engagement Score"]
    aud = row["Audience Size"]
    if lt == "Run Club":
        turnout = row.get("Est Weekly Turnout", 0)
        rev = turnout * 0.10 * 24
        score = min(100, (rev / 576) * 100)
        if row["Charlotte Hub"]:
            score = min(100, score * 1.25)
    elif lt == "Specialty Shop":
        locations = row.get("Num Locations", 1)
        rev = locations * 15 * 14
        score = min(100, (rev / 630) * 100)
        if row["Charlotte Hub"]:
            score = min(100, score * 1.15)
    elif lt == "Influencer":
        reach_factor = math.log10(max(aud, 1)) / 6
        score = reach_factor * eng * 10
        score = min(100, score)
        if row["Charlotte Hub"]:
            score = min(100, score * 1.10)
    return round(score)


def estimated_revenue(row):
    lt = row["Lead Type"]
    if lt == "Run Club":
        return round(row.get("Est Weekly Turnout", 0) * 0.10 * 24)
    elif lt == "Specialty Shop":
        return round(row.get("Num Locations", 1) * 15 * 14)
    elif lt == "Influencer":
        return round(row["Audience Size"] * 0.005 * 24)
    return 0


def priority_tier(score):
    if score >= 70: return "🔴 High"
    if score >= 40: return "🟡 Medium"
    return "⚪ Low"


# ── Session State — load once per session ────────────────────────────────────
if "leads_df" not in st.session_state:
    st.session_state.leads_df = load_leads()
    st.session_state.last_loaded = datetime.now()


# ── Build enriched dataframe ─────────────────────────────────────────────────
df = st.session_state.leads_df.copy()
df["Est Revenue Potential ($)"] = df.apply(estimated_revenue, axis=1)
df["Priority Score"] = df.apply(calculate_priority, axis=1)
df["Priority Tier"] = df["Priority Score"].apply(priority_tier)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:10px;">
        <img src="data:image/jpeg;base64,{LOGO_B64}" alt="DryQ" style="height:60px; border-radius:8px; margin-bottom:6px;" />
        <h2 style="font-family:'Barlow Condensed',sans-serif; color:#ffffff; margin:0; font-size:1.6rem; letter-spacing:0.06em;">
            CRM
        </h2>
        <p style="color:#666; font-size:0.75rem; margin-top:2px;">Sweat-Resistant Runner Pouch</p>
        <p style="color:#555; font-size:0.7rem;">$28 retail · $24 early · $14 wholesale</p>
    </div>
    """, unsafe_allow_html=True)

    # Live sync indicator
    loaded_at = st.session_state.get("last_loaded")
    if loaded_at:
        st.markdown(
            f'<div style="text-align:center; margin-bottom:8px;">'
            f'<span class="sync-badge">● Live · Airtable</span></div>',
            unsafe_allow_html=True,
        )

    if st.button("🔄 Refresh from Airtable", use_container_width=True):
        st.session_state.leads_df = load_leads()
        st.session_state.last_loaded = datetime.now()
        st.rerun()

    st.markdown("---")

    type_filter = st.multiselect("Filter by Lead Type", options=LEAD_TYPES, default=LEAD_TYPES)
    status_filter = st.multiselect("Filter by Status", options=STATUSES, default=STATUSES)
    hub_only = st.checkbox("Charlotte Hub Only", value=False)
    tier_filter = st.multiselect("Filter by Priority Tier", options=["🔴 High", "🟡 Medium", "⚪ Low"], default=["🔴 High", "🟡 Medium", "⚪ Low"])
    min_score, max_score = st.slider("Priority Score Range", min_value=0, max_value=100, value=(0, 100), step=5)
    search = st.text_input("🔍 Search Lead Name / Location", "")

    st.markdown("---")
    st.caption("Phase: Prototype / Early Testing")
    st.caption("Hub: Charlotte, NC")


# ── Filter Data ──────────────────────────────────────────────────────────────
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


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="font-family:'Barlow Condensed',sans-serif; font-size:2.8rem;
           font-weight:800; letter-spacing:0.06em; color:#ffffff; margin-bottom:0;">
  DRYQ CRM
</h1>
<p style="color:#888; margin-top:2px; font-size:1rem;">
  Lead Prioritization Dashboard · Sweat-Resistant Runner Pouch · Charlotte Hub
</p>
""", unsafe_allow_html=True)
st.markdown("---")


# ── KPI Cards ────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
total_leads = len(filtered)
high_priority = len(filtered[filtered["Priority Tier"] == "🔴 High"])
total_rev = filtered["Est Revenue Potential ($)"].sum()
avg_engagement = filtered["Engagement Score"].mean() if len(filtered) else 0
clt_leads = len(filtered[filtered["Charlotte Hub"] == True])

c1.metric("Total Leads", total_leads)
c2.metric("🔴 High Priority", high_priority)
c3.metric("CLT Hub Leads", clt_leads)
c4.metric("Est. Revenue Potential", f"${total_rev:,.0f}")
c5.metric("Avg Engagement", f"{avg_engagement:.1f}/10")
st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# ── ADD NEW LEAD ─────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">➕ Add New Lead</div>', unsafe_allow_html=True)

with st.expander("Click to add a new lead", expanded=False):
    with st.form("add_lead_form", clear_on_submit=True):
        acol1, acol2, acol3 = st.columns(3)
        with acol1:
            new_name = st.text_input("Lead Name *", placeholder="e.g. South End Runners")
            new_type = st.selectbox("Lead Type", LEAD_TYPES)
            new_location = st.text_input("Location", placeholder="e.g. South End, Charlotte")
            new_hub = st.checkbox("Charlotte Hub")
        with acol2:
            new_audience = st.number_input("Audience Size", min_value=0, value=0)
            new_engagement = st.slider("Engagement Score", 1, 10, 5)
            new_status = st.selectbox("Status", STATUSES)
            new_assigned = st.selectbox("Assign To", TEAM_MEMBERS)
        with acol3:
            new_turnout = st.number_input("Est Weekly Turnout (Run Clubs)", min_value=0, value=0)
            new_locations = st.number_input("Num Locations (Shops)", min_value=0, value=1)
            new_notes = st.text_area("Notes", height=100)

        submitted = st.form_submit_button("Add Lead", type="primary", use_container_width=True)
        if submitted:
            if not new_name.strip():
                st.error("Lead name is required.")
            else:
                new_lead = {
                    "Lead Name": new_name.strip(),
                    "Lead Type": new_type,
                    "Location": new_location,
                    "Audience Size": new_audience,
                    "Engagement Score": new_engagement,
                    "Est Weekly Turnout": new_turnout,
                    "Num Locations": new_locations,
                    "Charlotte Hub": new_hub,
                    "Notes": new_notes,
                    "Status": new_status,
                    "Assigned To": new_assigned,
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                try:
                    new_id = create_lead(new_lead)
                    new_lead["_airtable_id"] = new_id
                    st.session_state.leads_df = pd.concat(
                        [st.session_state.leads_df, pd.DataFrame([new_lead])],
                        ignore_index=True,
                    )
                    st.success(f"✅ '{new_name}' saved to Airtable!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to save to Airtable: {e}")

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# ── LEAD PIPELINE TABLE ─────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Lead Pipeline</div>', unsafe_allow_html=True)

display_cols = [
    "Lead Name", "Lead Type", "Location", "Status", "Assigned To",
    "Audience Size", "Engagement Score", "Est Revenue Potential ($)",
    "Priority Score", "Priority Tier", "Charlotte Hub", "Notes",
]


def color_rows(row):
    tier = row["Priority Tier"]
    if tier == "🔴 High":
        return ["background-color: rgba(255,75,0,0.12)"] * len(row)
    elif tier == "🟡 Medium":
        return ["background-color: rgba(255,179,0,0.08)"] * len(row)
    return ["background-color: rgba(60,60,60,0.08)"] * len(row)


def color_score(val):
    if val >= 70: return "color: #FF4B00; font-weight: 700;"
    if val >= 40: return "color: #FFB300; font-weight: 600;"
    return "color: #888;"


styled = (
    filtered[display_cols]
    .style.apply(color_rows, axis=1)
    .map(color_score, subset=["Priority Score"])
    .format({"Est Revenue Potential ($)": "${:,.0f}", "Priority Score": "{:.0f}"})
    .set_properties(**{"font-size": "0.88rem"})
)
st.dataframe(styled, use_container_width=True, height=450)
st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# ── UPDATE / ASSIGN LEAD ─────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">✏️ Update & Assign Leads</div>', unsafe_allow_html=True)

lead_names = st.session_state.leads_df["Lead Name"].tolist()

if lead_names:
    selected_lead_name = st.selectbox("Select a lead to update", lead_names)
    lead_idx = st.session_state.leads_df[
        st.session_state.leads_df["Lead Name"] == selected_lead_name
    ].index[0]
    lead_data = st.session_state.leads_df.loc[lead_idx]

    with st.form("update_lead_form"):
        ucol1, ucol2, ucol3 = st.columns(3)
        with ucol1:
            upd_name = st.text_input("Lead Name", value=lead_data["Lead Name"])
            upd_type = st.selectbox("Lead Type", LEAD_TYPES, index=LEAD_TYPES.index(lead_data["Lead Type"]))
            upd_location = st.text_input("Location", value=lead_data["Location"])
            upd_hub = st.checkbox("Charlotte Hub", value=bool(lead_data["Charlotte Hub"]))
        with ucol2:
            upd_status = st.selectbox(
                "Status", STATUSES,
                index=STATUSES.index(lead_data.get("Status", "New")) if lead_data.get("Status", "New") in STATUSES else 0,
            )
            upd_assigned = st.selectbox(
                "Assign To", TEAM_MEMBERS,
                index=TEAM_MEMBERS.index(lead_data.get("Assigned To", "Unassigned")) if lead_data.get("Assigned To", "Unassigned") in TEAM_MEMBERS else 0,
            )
            upd_audience = st.number_input("Audience Size", min_value=0, value=int(lead_data["Audience Size"]))
            upd_engagement = st.slider("Engagement Score", 1, 10, int(lead_data["Engagement Score"]))
        with ucol3:
            upd_turnout = st.number_input("Est Weekly Turnout", min_value=0, value=int(lead_data["Est Weekly Turnout"]))
            upd_locations = st.number_input("Num Locations", min_value=0, value=int(lead_data["Num Locations"]))
            upd_notes = st.text_area("Notes", value=lead_data.get("Notes", ""))

        ucol_btn1, ucol_btn2 = st.columns([3, 1])
        with ucol_btn1:
            update_submitted = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
        with ucol_btn2:
            delete_submitted = st.form_submit_button("🗑️ Delete Lead", use_container_width=True)

        if update_submitted:
            updated = {
                "Lead Name": upd_name, "Lead Type": upd_type,
                "Location": upd_location, "Audience Size": upd_audience,
                "Engagement Score": upd_engagement, "Est Weekly Turnout": upd_turnout,
                "Num Locations": upd_locations, "Charlotte Hub": upd_hub,
                "Notes": upd_notes, "Status": upd_status,
                "Assigned To": upd_assigned,
                "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            try:
                airtable_id = lead_data.get("_airtable_id", "")
                if airtable_id:
                    update_lead(airtable_id, updated)
                updated["_airtable_id"] = airtable_id
                for k, v in updated.items():
                    st.session_state.leads_df.loc[lead_idx, k] = v
                st.success(f"✅ '{upd_name}' updated in Airtable!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Airtable update failed: {e}")

        if delete_submitted:
            try:
                airtable_id = lead_data.get("_airtable_id", "")
                if airtable_id:
                    delete_lead(airtable_id)
                st.session_state.leads_df = st.session_state.leads_df.drop(lead_idx).reset_index(drop=True)
                st.success(f"🗑️ '{selected_lead_name}' deleted from Airtable.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Airtable delete failed: {e}")


# ── Quick Assign ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">⚡ Quick Assign</div>', unsafe_allow_html=True)

unassigned = st.session_state.leads_df[
    st.session_state.leads_df["Assigned To"] == "Unassigned"
]["Lead Name"].tolist()

if unassigned:
    st.info(f"**{len(unassigned)} unassigned leads** need attention.")
    qa_cols = st.columns(min(len(unassigned), 4))
    for i, lead_name in enumerate(unassigned[:8]):
        col = qa_cols[i % len(qa_cols)]
        with col:
            new_owner = st.selectbox(lead_name, TEAM_MEMBERS, key=f"qa_{i}")
            if new_owner != "Unassigned":
                idx = st.session_state.leads_df[
                    st.session_state.leads_df["Lead Name"] == lead_name
                ].index[0]
                airtable_id = st.session_state.leads_df.loc[idx, "_airtable_id"]
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                try:
                    if airtable_id:
                        update_lead(airtable_id, {"Assigned To": new_owner, "Last Updated": ts})
                    st.session_state.leads_df.loc[idx, "Assigned To"] = new_owner
                    st.session_state.leads_df.loc[idx, "Last Updated"] = ts
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Quick assign failed: {e}")
else:
    st.success("All leads are assigned!")


# ── Charts ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">Analytics</div>', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("**Revenue Potential by Lead Type**")
    rev_by_type = filtered.groupby("Lead Type")["Est Revenue Potential ($)"].sum().reset_index()
    st.bar_chart(rev_by_type.set_index("Lead Type"), color="#FF4B00")
with col_b:
    st.markdown("**Priority Score Distribution**")
    score_data = filtered[["Lead Name", "Priority Score"]].set_index("Lead Name").sort_values("Priority Score", ascending=True)
    st.bar_chart(score_data, color="#FFB300")
with col_c:
    st.markdown("**Leads by Status**")
    status_counts = filtered["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    st.bar_chart(status_counts.set_index("Status"), color="#00C9A7")


# ── Priority Formula Guide ───────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">Priority Score Logic ("Charlotte Model")</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
**🔴 Run Clubs (High Priority)**

`Revenue = Est Weekly Turnout × 10% conversion × $24`

`Score = Revenue / $576 × 100`

Charlotte Hub adds **+25%** boost.
Focus: Mad Miles, Barn Burners, Queen City Pacers
""")
with col2:
    st.markdown("""
**🟡 Specialty Shops (Medium Priority)**

`Revenue = Locations × 15 units × $14 wholesale`

`Score = Revenue / $630 × 100`

Charlotte Hub adds **+15%** boost.
Focus: Charlotte Running Co., Run For Your Life
""")
with col3:
    st.markdown("""
**🟢 Influencers (Tactical Priority)**

`Score = log₁₀(Audience) / 6 × Engagement × 10`

Charlotte Hub adds **+10%** boost.
Focus: High-engagement "realistic runners"
CLT5K Queen, Paige Runs CLT, SweatyMama_CLT
""")


# ── Export ───────────────────────────────────────────────────────────────────
st.markdown("---")
csv_data = filtered[display_cols].to_csv(index=False)
st.download_button(
    label="⬇️ Export Filtered Leads as CSV",
    data=csv_data,
    file_name="dryq_crm_leads.csv",
    mime="text/csv",
)

st.caption("DryQ CRM · Built for Charlotte prototype launch · $24 early supporter · $28 retail")
