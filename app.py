import streamlit as st
import streamlit_authenticator as stauth
from google import genai
from google.genai import types
import time

st.set_page_config(page_title="Personal Gemini Journal", page_icon="🔮", layout="centered")

# --- ADVANCED DREAMY & PASTEL CSS OVERHAUL ---
st.markdown("""
    <style>
    /* Global App canvas gradient background */
    .stApp {
        background: linear-gradient(135deg, #e0c3fc 0%, #fbc2eb 100%) !important;
    }
    
    /* STUBBORN TEXT BOX REFACTOR */
    .stTextArea textarea, 
    div[data-testid="stTextArea"] > div,
    div[data-testid="stTextArea"] > div > div {
        background-color: rgba(255, 255, 255, 0.5) !important;
        border: 2px solid #c29ffa !important;
        border-radius: 16px !important;
        color: #3d2e4f !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .stTextArea textarea {
        color: #3d2e4f !important;
        font-size: 1.05rem !important;
    }
    
    /* High contrast placeholders */
    .stTextArea textarea::placeholder {
        color: #5b4970 !important;
        opacity: 1.0 !important;
        font-weight: 500 !important;
    }
    
    /* Active focus state when the user is typing */
    .stTextArea textarea:focus, div[data-testid="stTextArea"] > div:focus-within {
        border-color: #a18cd1 !important;
        box-shadow: 0 0 10px rgba(161, 140, 209, 0.5) !important;
    }
    
    /* PREMIUM SIDEBAR: High-end frosted glass styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(224, 195, 252, 0.6) 0%, rgba(251, 194, 235, 0.6) 100%) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.4) !important;
    }
    
    /* Font styles across elements */
    h1, h2, h3, p, label, span, .stMarkdown {
        color: #4A3E56 !important;
        font-family: 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* Beautiful pastel action buttons */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #a18cd1 0%, #fbc2eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 28px !important;
        font-weight: bold !important;
        box-shadow: 0px 5px 15px rgba(161, 140, 209, 0.4) !important;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0px 8px 20px rgba(161, 140, 209, 0.6) !important;
    }
    
    /* NEW: Custom Memory Card Styling (Replaces the broken expander) */
    .memory-card {
        background-color: rgba(255, 255, 255, 0.55) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(4px);
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0px 4px 10px rgba(161, 140, 209, 0.1) !important;
    }
    
    .memory-date {
        font-weight: bold !important;
        color: #6c538c !important;
        font-size: 0.95rem !important;
        margin-bottom: 8px !important;
    }
    
    /* Info alert element boxes */
    div[data-testid="stNotification"] {
        background-color: rgba(255, 255, 255, 0.4) !important;
        border: 1px solid rgba(161, 140, 209, 0.3) !important;
        border-radius: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'credentials' not in st.secrets:
    st.error("Missing '.streamlit/secrets.toml' file!")
    st.stop()

# User Authentication Setup
authenticator = stauth.Authenticate(
    st.secrets['credentials'].to_dict(),
    st.secrets['cookie']['name'],
    st.secrets['cookie']['key'],
    st.secrets['cookie']['expiry_days']
)

authenticator.login()

if st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
    st.stop()
elif st.session_state["authentication_status"] is None or not st.session_state["authentication_status"]:
    st.warning('Please login to access your secure journal.')
    st.stop()

username = st.session_state["username"]
name = st.session_state["name"]

with st.sidebar:
    st.write(f"✨ Welcome back, **{name}**")
    authenticator.logout('Logout', 'sidebar')

st.title("🔮 My Dreamy Gemini Journal")

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

client = get_gemini_client()

if "journal_db" not in st.session_state:
    st.session_state.journal_db = {}
if username not in st.session_state.journal_db:
    st.session_state.journal_db[username] = []

st.subheader("✍️ Capture Your Reflections")
entry_text = st.text_area(label="Reflection Input Window", label_visibility="collapsed", placeholder="Write down your starry thoughts here...", height=150)

if st.button("Securely Save & Summarize"):
    if not entry_text.strip():
        st.error("Please write something first.")
    else:
        with st.spinner("Letting Gemini read the stars..."):
            try:
                config = types.GenerateContentConfig(
                    system_instruction="You are a secure journal summary bot. Provide a highly concise, warm, empathetic one-sentence summary of the user's entry.",
                    temperature=0.4
                )
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=entry_text,
                    config=config
                )
                
                entry_data = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "content": entry_text,
                    "summary": response.text
                }
                st.session_state.journal_db[username].append(entry_data)
                st.success("Your thoughts have been safely archived.")
                st.info(f"✨ **Gemini Reflection:** {response.text}")
            except Exception as e:
                st.error(f"Secure processing error: {str(e)}")

st.markdown("---")
st.subheader("📚 Saved Memories")
user_entries = st.session_state.journal_db[username]
if not user_entries:
    st.info("No entries saved in this timeline yet.")
else:
    for entry in reversed(user_entries):
        # Render a custom styled HTML block card container
        st.markdown(f"""
            <div class="memory-card">
                <div class="memory-date">🔮 Memory from {entry['timestamp']}</div>
                <p><strong>Insight:</strong> <em>{entry['summary']}</em></p>
                <hr style="border: 0; height: 1px; background: rgba(161, 140, 209, 0.2); margin: 12px 0;">
                <p>{entry['content']}</p>
            </div>
        """, unsafe_allow_html=True)
