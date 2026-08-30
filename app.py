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
    
    /* FORCE BRUTE-FORCE OVERRIDE ON ALL INPUT FIELDS (Login and Journal textareas) */
    input, textarea, [data-baseweb="input"], [data-baseweb="textarea"], .stTextInput div, .stTextArea div {
        background-color: rgba(255, 255, 255, 0.6) !important;
        background: rgba(255, 255, 255, 0.6) !important;
        border: 2px solid #c29ffa !important;
        border-radius: 12px !important;
        color: #3d2e4f !important;
    }

    /* Force the actual text typed inside input boxes to be dark purple and readable */
    input[type="text"], input[type="password"], textarea {
        color: #3d2e4f !important;
        -webkit-text-fill-color: #3d2e4f !important;
    }
    
    /* FIX THE BORING LOGIN BOX CONTAINER */
    [data-testid="stForm"], form {
        background-color: rgba(255, 255, 255, 0.45) !important;
        border-radius: 24px !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 40px !important;
        box-shadow: 0px 10px 30px rgba(161, 140, 209, 0.2) !important;
    }
    
    /* High contrast placeholders */
    ::placeholder, .stTextArea textarea::placeholder {
        color: #5b4970 !important;
        opacity: 0.8 !important;
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
    
    /* Beautiful pastel buttons (Targets both Login and Save buttons) */
    div.stButton > button:first-child, form button[type="submit"], button[data-testid="baseButton-secondary"] {
        background: linear-gradient(90deg, #a18cd1 0%, #fbc2eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 28px !important;
        font-weight: bold !important;
        box-shadow: 0px 5px 15px rgba(161, 140, 209, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button:first-child:hover, form button[type="submit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0px 8px 20px rgba(161, 140, 209, 0.6) !important;
    }
    
    /* Custom Memory Card Styling */
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
        st.markdown(f"""
            <div class="memory-card">
                <div class="memory-date">🔮 Memory from {entry['timestamp']}</div>
                <p><strong>Insight:</strong> <em>{entry['summary']}</em></p>
                <hr style="border: 0; height: 1px; background: rgba(161, 140, 209, 0.2); margin: 12px 0;">
                <p>{entry['content']}</p>
            </div>
        """, unsafe_allow_html=True)
