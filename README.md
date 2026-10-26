# AI-Powered Daily Routine — Integrated Streamlit Dashboard

Integrations:
- Gemini
- Gmail
- Google Calendar
- Notion

## 1. Install
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

## 2. Gemini
Create a Gemini API key and put it in `.env`:
GEMINI_API_KEY=...

## 3. Gmail + Google Calendar
Create a Google Cloud project, enable Gmail API and Calendar API, configure OAuth consent, and create a Desktop OAuth 2.0 client.
Download the OAuth client JSON and save it as:
credentials.json

The app requests:
- Gmail readonly
- Calendar readonly

The first Google connection opens a browser for authorization and stores `token.json`.

## 4. Notion
Create a Notion internal integration and copy its token into `.env` as NOTION_API_TOKEN.
Share the target Notion page/database with the integration.
Set either NOTION_DATABASE_ID or NOTION_PAGE_ID.

## 5. Run
streamlit run app.py

## Notes
This hackathon version reads Gmail/Calendar and reads/writes a Notion page when configured.
It does NOT automatically send Gmail messages or modify Calendar events.
AI output should be reviewed by a human before acting on it.
