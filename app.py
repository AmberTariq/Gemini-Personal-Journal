import streamlit as st
import streamlit.components.v1 as components
import requests
import html as html_lib
from datetime import datetime, date, timedelta
from google import genai
from google.genai import types
from google.cloud import firestore

# --- MOOD CONFIGURATION ---
MOOD_OPTIONS = {
    "😊 Happy": "#8BC34A",
    "😌 Calm": "#64B5F6",
    "😐 Neutral": "#B0A8C9",
    "😔 Sad": "#7986CB",
    "😤 Stressed": "#EF5350",
    "✨ Inspired": "#FFB74D",
}

st.set_page_config(page_title="Personal Gemini Journal", page_icon="🔮", layout="centered")

# --- DREAMY PASTEL UI THEME ---
st.markdown("""
    <style>
    header[data-testid="stHeader"] { display: none !important; }
    .stApp { background: linear-gradient(135deg, #e0c3fc 0%, #fbc2eb 100%) !important; }
    
    input, textarea, [data-baseweb="input"], [data-baseweb="textarea"] {
        background-color: rgba(255, 255, 255, 0.6) !important;
        border: 2px solid #c29ffa !important;
        border-radius: 12px !important;
        color: #3d2e4f !important;
    }
    input[type="text"], input[type="password"], textarea {
        color: #3d2e4f !important;
        -webkit-text-fill-color: #3d2e4f !important;
    }
    div.st-key-auth_card, div.st-key-reflection_card {
        background-color: rgba(255, 255, 255, 0.45) !important;
        border-radius: 24px !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 32px !important;
        box-shadow: 0px 10px 30px rgba(161, 140, 209, 0.2) !important;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #a18cd1 0%, #fbc2eb 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 10px 30px !important;
        font-weight: bold !important;
        box-shadow: 0px 5px 15px rgba(161, 140, 209, 0.4) !important;
    }
    details.memory-card {
        background-color: rgba(255, 255, 255, 0.55) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        padding: 16px 20px !important;
        margin-bottom: 12px !important;
    }
    details.memory-card summary {
        cursor: pointer !important;
        font-weight: bold !important;
        color: #6c538c !important;
    }
    .mood-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FIREBASE REST AUTHENTICATION ---
FIREBASE_API_KEY = st.secrets.get("FIREBASE_WEB_API_KEY", "")

def firebase_auth(email, password, mode="signInWithPassword"):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:{mode}?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    res = requests.post(url, json=payload)
    return res.json()

# --- INITIALIZE FIRESTORE & GEMINI ---
@st.cache_resource
def get_db():
    return firestore.Client()

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets.get("GEMINI_API_KEY"))

# --- SESSION INITIALIZATION ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# --- AUTHENTICATION VIEW ---
if not st.session_state.user_id:
    col1, col2, col3 = st.columns([1, 5, 1])
    with col2:
        st.title("🔮 Personal Gemini Journal")
        with st.container(key="auth_card"):
            tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
            
            with tab_login:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.button("Log In"):
                    if email and password:
                        res = firebase_auth(email, password, "signInWithPassword")
                        if "localId" in res:
                            st.session_state.user_id = res["localId"]
                            st.session_state.user_email = res["email"]
                            st.rerun()
                        else:
                            st.error(res.get("error", {}).get("message", "Authentication Failed"))
                    else:
                        st.warning("Please fill all fields.")
            
            with tab_signup:
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password (min 6 chars)", type="password", key="signup_pass")
                if st.button("Create Account"):
                    if new_email and new_password:
                        res = firebase_auth(new_email, new_password, "signUp")
                        if "localId" in res:
                            st.success("Account created! Please log in.")
                        else:
                            st.error(res.get("error", {}).get("message", "Sign up failed"))
                    else:
                        st.warning("Please fill all fields.")
    st.stop()

# --- AUTHENTICATED USER CONTEXT ---
user_id = st.session_state.user_id
user_email = st.session_state.user_email
db = get_db()
client = get_gemini_client()

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"✨ Logged in as: **{user_email}**")
    if st.button("Logout"):
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.rerun()
    st.markdown("---")

# Fetch Firestore entries isolated to current user
entries_ref = db.collection("users").document(user_id).collection("journal_entries")
entries_docs = entries_ref.order_by("created_at", direction=firestore.Query.DESCENDING).stream()
user_entries = [doc.to_dict() for doc in entries_docs]

st.title("🔮 My Dreamy Gemini Journal")

with st.container(key="reflection_card"):
    st.subheader("✍️ Capture Your Reflections")
    entry_text = st.text_area("Reflection Input", placeholder="Write down your starry thoughts here...", height=140, label_visibility="collapsed")
    selected_mood = st.radio("How are you feeling?", options=list(MOOD_OPTIONS.keys()), horizontal=True)

    if st.button("Securely Save & Summarize"):
        if not entry_text.strip():
            st.error("Please enter a reflection before saving.")
        else:
            with st.spinner("Letting Gemini read the stars..."):
                try:
                    config = types.GenerateContentConfig(
                        system_instruction="You are an empathetic journal reflection assistant. Provide a warm, uplifting, concise 1-2 sentence reflection/summary.",
                        temperature=0.4
                    )
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=entry_text,
                        config=config
                    )
                    
                    # Persist to Google Cloud Firestore
                    doc_data = {
                        "content": entry_text,
                        "summary": response.text,
                        "mood": selected_mood,
                        "created_at": datetime.utcnow(),
                        "timestamp_str": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    entries_ref.add(doc_data)
                    st.success("Your reflection has been safely stored in Firestore!")
                    st.info(f"✨ **Gemini Reflection:** {response.text}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing entry: {str(e)}")

# --- DISPLAY STORED MEMORIES ---
st.markdown("---")
st.subheader(f"📚 Saved Memories ({len(user_entries)})")
if not user_entries:
    st.info("No entries saved in your Firestore timeline yet.")
else:
    for entry in user_entries:
        mood_label = entry.get("mood", "😐 Neutral")
        mood_color = MOOD_OPTIONS.get(mood_label, "#B0A8C9")
        safe_content = html_lib.escape(entry.get("content", "")).replace("\n", "<br>")
        safe_summary = html_lib.escape(entry.get("summary", ""))
        safe_time = html_lib.escape(entry.get("timestamp_str", ""))

        st.markdown(f"""
            <details class="memory-card">
                <summary>
                    <span class="mood-dot" style="background-color:{mood_color};"></span>
                    {mood_label} &nbsp;·&nbsp; 🔮 {safe_time}
                </summary>
                <div style="margin-top:10px;">
                    <p><strong>Insight:</strong> <em>{safe_summary}</em></p>
                    <hr style="border:0;height:1px;background:rgba(161,140,209,0.2);margin:8px 0;">
                    <p>{safe_content}</p>
                </div>
            </details>
        """, unsafe_allow_html=True)
