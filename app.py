import os
from datetime import date
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai

from services.google_services import fetch_gmail, fetch_calendar
from services.notion_service import fetch_page, search_database, append_paragraph

load_dotenv()

st.set_page_config(
    page_title="AI Daily Command Center",
    page_icon="🤖",
    layout="wide",
)

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1400px;}
.hero {
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,.25);
    margin-bottom: 1rem;
}
.metric-card {
    padding: 1rem;
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,.25);
    min-height: 110px;
}
.small {font-size: .85rem; opacity: .7;}
</style>
""", unsafe_allow_html=True)

# ---------- State ----------
for key, default in {
    "emails": [],
    "calendar": [],
    "notion_notes": "",
    "notion_pages": [],
    "results": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- Gemini ----------
@st.cache_resource
def gemini_client():
    key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=key) if key else None


def ai(prompt):
    client = gemini_client()
    if not client:
        return "⚠️ GEMINI_API_KEY is missing in .env"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Gemini error: {e}"


def context():
    return f"""
TODAY: {date.today().strftime("%A, %d %B %Y")}

GMAIL:
{st.session_state.emails}

GOOGLE CALENDAR:
{st.session_state.calendar}

NOTION NOTES:
{st.session_state.notion_notes}

NOTION PAGES:
{st.session_state.notion_pages}
"""

# ---------- Header ----------
st.markdown("""
<div class="hero">
<h1>🤖 AI Daily Command Center</h1>
<p>Gmail + Google Calendar + Notion + Gemini</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("🔌 Connections")

    gemini_ok = bool(os.getenv("GEMINI_API_KEY"))
    notion_ok = bool(os.getenv("NOTION_API_TOKEN"))
    google_ok = Path("credentials.json").exists() or Path("token.json").exists()

    st.write("🧠 Gemini:", "🟢 Connected" if gemini_ok else "🔴 Missing")
    st.write("📧 Gmail:", "🟢 Ready" if google_ok else "🟡 OAuth needed")
    st.write("📅 Calendar:", "🟢 Ready" if google_ok else "🟡 OAuth needed")
    st.write("🧠 Notion:", "🟢 Connected" if notion_ok else "🟡 Token needed")

    st.divider()

    if st.button("🔄 Sync All Sources", use_container_width=True):
        with st.spinner("Connecting to Gmail and Calendar..."):
            try:
                st.session_state.emails = fetch_gmail()
                st.session_state.calendar = fetch_calendar(days=2)
            except Exception as e:
                st.error(f"Google sync failed: {e}")

        if notion_ok:
            try:
                page_id = os.getenv("NOTION_PAGE_ID")
                db_id = os.getenv("NOTION_DATABASE_ID")
                if page_id:
                    st.session_state.notion_notes = fetch_page(page_id)
                if db_id:
                    st.session_state.notion_pages = search_database(database_id=db_id)
            except Exception as e:
                st.error(f"Notion sync failed: {e}")

        st.success("Sync completed.")

# ---------- Top metrics ----------
emails = st.session_state.emails
events = st.session_state.calendar
notion_pages = st.session_state.notion_pages

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><h2>📧 {len(emails)}</h2><span class="small">Recent emails</span></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><h2>📅 {len(events)}</h2><span class="small">Upcoming events</span></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><h2>🧠 {len(notion_pages)}</h2><span class="small">Notion pages</span></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><h2>🤖 Gemini</h2><span class="small">AI productivity engine</span></div>', unsafe_allow_html=True)

st.write("")

# ---------- Source tabs ----------
tabs = st.tabs(["📧 Gmail", "📅 Calendar", "🧠 Notion", "⚡ AI Actions"])

with tabs[0]:
    st.subheader("Gmail Inbox")
    if not emails:
        st.info("Click 'Sync All Sources' to load recent Gmail messages.")
    else:
        for email in emails:
            with st.expander(f"{email.get('subject') or '(No subject)'} — {email.get('from', '')}"):
                st.write(email.get("date", ""))
                st.write(email.get("snippet", ""))
                if email.get("body"):
                    st.caption(email["body"][:2000])

with tabs[1]:
    st.subheader("Google Calendar")
    if not events:
        st.info("Click 'Sync All Sources' to load upcoming events.")
    else:
        for event in events:
            with st.container(border=True):
                st.write(f"**{event['summary']}**")
                st.write(f"🕒 {event['start']} → {event['end']}")
                if event["location"]:
                    st.write(f"📍 {event['location']}")

with tabs[2]:
    st.subheader("Notion Knowledge")
    if st.session_state.notion_notes:
        st.text_area("Connected page content", st.session_state.notion_notes, height=300)
    elif notion_pages:
        for p in notion_pages:
            st.write(f"• {p['title']}")
    else:
        st.info("Configure NOTION_PAGE_ID or NOTION_DATABASE_ID, then sync.")

with tabs[3]:
    st.subheader("AI Productivity Actions")

    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("🌅 Generate My AI Day", use_container_width=True):
            st.session_state.results["day"] = ai(f"""
You are a personal productivity assistant.

Analyze:
{context()}

Create a practical daily plan:
1. Top 3 priorities
2. Important emails
3. Calendar commitments
4. Suggested focus blocks
5. Deadlines
6. Recommended order of work

Do not invent information.
""")

    with a2:
        if st.button("📧 Analyze Inbox", use_container_width=True):
            st.session_state.results["email"] = ai(f"""
Analyze the Gmail data in:
{context()}

Classify messages as:
🔴 URGENT
🟡 ACTION REQUIRED
🟢 INFORMATIONAL

For action-required emails, suggest a short reply draft.
Do not send anything. Do not invent facts.
""")

    with a3:
        if st.button("📝 Prepare Meeting", use_container_width=True):
            st.session_state.results["meeting"] = ai(f"""
Prepare the next meeting using:
{context()}

Return:
- Meeting objective
- Relevant emails
- Relevant Notion knowledge
- Current context
- Questions to ask
- Decisions needed
- Follow-up actions
""")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("✅ Prioritize Tasks", use_container_width=True):
            st.session_state.results["tasks"] = ai(f"""
From the information below, extract actionable tasks and prioritize them:
{context()}

Return:
HIGH
MEDIUM
LOW
and recommended order.
""")

    with b2:
        if st.button("🧠 Connect Knowledge", use_container_width=True):
            st.session_state.results["knowledge"] = ai(f"""
Find useful connections between Gmail, Calendar and Notion:
{context()}

Return:
- Relevant knowledge
- Related projects
- Missing information
- Learning/research suggestions
""")

    with b3:
        if st.button("🌙 End-of-Day Review", use_container_width=True):
            st.session_state.results["review"] = ai(f"""
Create an end-of-day review using:
{context()}

Return:
- Completed/known activity
- Pending actions
- Risks
- Top 3 priorities for tomorrow
- One improvement suggestion
""")

# ---------- AI results ----------
if st.session_state.results:
    st.divider()
    st.header("📊 AI Results")

    order = [
        ("day", "🌅 My AI Day"),
        ("email", "📧 Inbox Intelligence"),
        ("tasks", "✅ Task Prioritization"),
        ("meeting", "📝 Meeting Brief"),
        ("knowledge", "🧠 Knowledge Connections"),
        ("review", "🌙 End-of-Day Review"),
    ]

    for key, title in order:
        if key in st.session_state.results:
            with st.container(border=True):
                st.subheader(title)
                st.markdown(st.session_state.results[key])

                if key in {"meeting", "review"} and os.getenv("NOTION_PAGE_ID"):
                    if st.button(f"💾 Save {title} to Notion", key=f"save_{key}"):
                        try:
                            append_paragraph(
                                os.getenv("NOTION_PAGE_ID"),
                                f"{title}\n\n{st.session_state.results[key]}"
                            )
                            st.success("Saved to Notion.")
                        except Exception as e:
                            st.error(f"Could not save to Notion: {e}")

st.divider()
st.caption(
    "Privacy/safety: this demo uses read-only Gmail and Calendar scopes. "
    "It does not send emails or modify calendar events. Review AI output before acting."
)
