import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
import time
from datetime import datetime, date, timedelta
import html as html_lib

# Mood tags: each maps a label (emoji + word, always shown together — never
# color alone, so colorblind users aren't relying on hue to tell moods apart)
# to a hex color used for the small dot indicator on saved memory cards.
MOOD_OPTIONS = {
    "😊 Happy": "#8BC34A",
    "😌 Calm": "#64B5F6",
    "😐 Neutral": "#B0A8C9",
    "😔 Sad": "#7986CB",
    "😤 Stressed": "#EF5350",
    "✨ Inspired": "#FFB74D",
}


def compute_streak(entries):
    """Consecutive-day streak, counted backward from the most recent entry.
    Still counts as 'alive' if the last entry was today or yesterday (so it
    doesn't zero out just because you haven't written yet today); breaks
    if there's a real gap of 2+ days."""
    if not entries:
        return 0
    entry_dates = sorted(
        {datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S").date() for e in entries},
        reverse=True,
    )
    most_recent = entry_dates[0]
    if (date.today() - most_recent).days > 1:
        return 0
    streak = 1
    expected = most_recent - timedelta(days=1)
    for d in entry_dates[1:]:
        if d == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif d < expected:
            break
    return streak

st.set_page_config(page_title="Personal Gemini Journal", page_icon="🔮", layout="centered")

# --- ADVANCED DREAMY & PASTEL CSS OVERHAUL ---
st.markdown("""
    <style>
    /* REMOVE STUBBORN BLACK TOP HEADER BAR */
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }

    /* Global App canvas gradient background */
    .stApp {
        background: linear-gradient(135deg, #e0c3fc 0%, #fbc2eb 100%) !important;
    }
    
    /* FORCE BRUTE-FORCE OVERRIDE ON ALL INPUT FIELDS */
    input, textarea, [data-baseweb="input"], [data-baseweb="textarea"], .stTextInput div, .stTextArea div {
        background-color: rgba(255, 255, 255, 0.6) !important;
        background: rgba(255, 255, 255, 0.6) !important;
        border: 2px solid #c29ffa !important;
        border-radius: 12px !important;
        color: #3d2e4f !important;
    }

    /* Force text inside inputs to be legible and dark purple */
    input[type="text"], input[type="password"], textarea {
        color: #3d2e4f !important;
        -webkit-text-fill-color: #3d2e4f !important;
    }
    
    /* Elegant bounding card frame layout wrapper specifically for our login cluster.
       Targets the div Streamlit generates for st.container(key="login_card"),
       which — unlike a raw st.markdown div — actually wraps its child widgets. */
    div[data-testid="stVerticalBlockBorderWrapper"].st-key-login_card,
    div.st-key-login_card {
        background-color: rgba(255, 255, 255, 0.45) !important;
        border-radius: 24px !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 40px !important;
        box-shadow: 0px 10px 30px rgba(161, 140, 209, 0.2) !important;
        margin-top: 20px;
    }
    
    /* Password show/hide toggle: replace Streamlit's default icon (a Material
       Symbols ligature that renders as raw "visibility" text if the icon
       font fails to load) with a CSS-drawn eye SVG. This never depends on
       an external font, so it can't fall back to text. */
    div[data-baseweb="input"] {
        position: relative !important;
    }
    div[data-baseweb="input"] button {
        font-size: 0 !important;
        color: transparent !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        position: absolute !important;
        right: 10px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        width: 20px !important;
        height: 20px !important;
        min-width: 0 !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236c538c' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z'/%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 18px 18px !important;
    }
    div[data-baseweb="input"] button svg {
        display: none !important;
    }
    /* The ligature text ("visibility") sits on a descendant element that sets
       its OWN font-size explicitly — an inherited font-size: 0 on the parent
       button does NOT override that. So we target every descendant directly. */
    div[data-baseweb="input"] button * {
        font-size: 0 !important;
        line-height: 0 !important;
        color: transparent !important;
        opacity: 0 !important;
    }
    /* Give the password field breathing room so typed text doesn't run under the icon */
    div[data-baseweb="input"]:has(button) input {
        padding-right: 36px !important;
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
    
    /* Beautiful pastel action buttons - Text color and fill forced to white */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #a18cd1 0%, #fbc2eb 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 35px !important;
        font-weight: bold !important;
        box-shadow: 0px 5px 15px rgba(161, 140, 209, 0.4) !important;
        transition: all 0.3s ease !important;
        display: inline-block !important;
        visibility: visible !important;
        font-size: 1rem !important;
        margin-top: 15px;
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0px 8px 20px rgba(161, 140, 209, 0.6) !important;
    }
    
    /* Custom Memory Card Styling — now a <details> element so it's
       collapsed by default and expands on click, no JS required, since
       <details>/<summary> is native browser behavior. */
    details.memory-card {
        background-color: rgba(255, 255, 255, 0.55) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(4px);
        padding: 16px 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0px 4px 10px rgba(161, 140, 209, 0.1) !important;
    }

    details.memory-card summary {
        cursor: pointer !important;
        font-weight: bold !important;
        color: #6c538c !important;
        font-size: 0.95rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        list-style: revert !important;   /* keep the native expand triangle */
    }

    details.memory-card .memory-body {
        margin-top: 12px !important;
    }

    /* Colored mood dot — always paired with the mood emoji + word in the
       text itself, never used as the only signal (accessibility: color
       alone can't be the sole carrier of meaning). */
    .mood-dot {
        display: inline-block !important;
        width: 10px !important;
        height: 10px !important;
        border-radius: 50% !important;
        flex-shrink: 0 !important;
    }

    /* Streak badge */
    .streak-badge {
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        background: rgba(255, 255, 255, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 20px !important;
        padding: 8px 18px !important;
        font-weight: bold !important;
        color: #6c538c !important;
        margin-bottom: 16px !important;
        box-shadow: 0px 4px 10px rgba(161, 140, 209, 0.1) !important;
    }
    
    /* Info alert element boxes */
    div[data-testid="stNotification"] {
        background-color: rgba(255, 255, 255, 0.4) !important;
        border: 1px solid rgba(161, 140, 209, 0.3) !important;
        border-radius: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- STRUCTURE-AGNOSTIC EYE ICON FIX ---
# The CSS selector approach (targeting div[data-baseweb="input"] button ...)
# never matched anything, which means the toggle button is NOT nested inside
# that div in this Streamlit version — it's positioned elsewhere in the tree.
# Instead of guessing the exact hierarchy again, this finds the icon by its
# actual text content ("visibility"), which is stable regardless of where
# Streamlit places it, and works even after Streamlit re-renders on rerun.
components.html("""
<script>
(function() {
    const doc = window.parent.document;

    if (!doc.getElementById('eye-icon-style')) {
        const style = doc.createElement('style');
        style.id = 'eye-icon-style';
        style.innerHTML = `
            .custom-eye-icon {
                font-size: 0 !important;
                color: transparent !important;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236c538c' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z'/%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3C/svg%3E") !important;
                background-repeat: no-repeat !important;
                background-position: center center !important;
                background-size: 18px 18px !important;
            }
        `;
        doc.head.appendChild(style);
    }

    function fixEyeIcons() {
        const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_ELEMENT);
        let el;
        while ((el = walker.nextNode())) {
            if (el.children.length === 0) {
                const text = (el.textContent || "").trim();
                if (text === "visibility" || text === "visibility_off") {
                    el.classList.add("custom-eye-icon");
                    const btn = el.closest("button");
                    if (btn) btn.classList.add("custom-eye-icon");
                }
            }
        }
    }

    fixEyeIcons();
    const observer = new MutationObserver(fixEyeIcons);
    observer.observe(doc.body, { childList: true, subtree: true });
})();
</script>
""", height=0)

# 1. Initialize Authentication session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# 2. Render Login Form if User is Not Authenticated
if not st.session_state.authenticated:
    
    # Proportional layout sizing configurations to prevent wide stretching
    col1, col2, col3 = st.columns([1, 5, 1])
    
    with col2:
        st.title("🔮 Personal Gemini Journal")
        # st.container(key=...) — unlike st.markdown('<div>...') — actually
        # wraps the widgets placed inside its `with` block in the real DOM,
        # so the CSS card styling wraps the form instead of floating empty.
        with st.container(key="login_card"):
            st.subheader("Login")

            input_user = st.text_input("Username")
            input_pass = st.text_input("Password", type="password")

            login_btn = st.button("Login")
    
    if login_btn:
        if 'credentials' in st.secrets and input_user in st.secrets['credentials']['usernames']:
            correct_pass = st.secrets['credentials']['usernames'][input_user]['password']
            if input_pass == correct_pass:
                st.session_state.authenticated = True
                st.session_state.username = input_user
                st.session_state.name = st.secrets['credentials']['usernames'][input_user]['name']
                st.rerun()
            else:
                st.error("Username/password is incorrect")
        else:
            st.error("Username/password is incorrect")
            
    st.stop()

# --- Everything below this line is secure and active within user validation context ---
username = st.session_state.username
name = st.session_state.name

with st.sidebar:
    st.write(f"✨ Welcome back, **{name}**")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

st.title("🔮 My Dreamy Gemini Journal")

if "journal_db" not in st.session_state:
    st.session_state.journal_db = {}
if username not in st.session_state.journal_db:
    st.session_state.journal_db[username] = []

_streak = compute_streak(st.session_state.journal_db[username])
if _streak > 0:
    st.markdown(
        f'<div class="streak-badge">🔥 {_streak} day{"s" if _streak != 1 else ""} streak</div>',
        unsafe_allow_html=True,
    )

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

client = get_gemini_client()

st.subheader("✍️ Capture Your Reflections")
entry_text = st.text_area(label="Reflection Input Window", label_visibility="collapsed", placeholder="Write down your starry thoughts here...", height=150)

# --- LIVE WORD COUNTER + AUTO-EXPAND ---
# This intentionally does NOT go through Python/session_state, because
# st.text_area only triggers a rerun on blur or Ctrl+Enter — a counter
# driven by Python would lag behind every keystroke, not feel "live".
# Instead: plain JS listens to the real <textarea>'s own `input` event,
# found by its placeholder text (which we control, unlike third-party
# icon markup), so it updates on every keystroke with zero rerun cost.
components.html("""
<script>
(function() {
    const doc = window.parent.document;
    const PLACEHOLDER = "Write down your starry thoughts here...";
    const MIN_HEIGHT = 150;   // matches the height= passed to st.text_area
    const MAX_HEIGHT = 500;   // cap so it can't grow forever

    function setup() {
        const textareas = doc.querySelectorAll('textarea[placeholder="' + PLACEHOLDER + '"]');
        textareas.forEach(ta => {
            if (ta.dataset.liveCounterAttached) return;
            ta.dataset.liveCounterAttached = "true";

            ta.style.resize = "none";           // manual resize would fight the auto-expand
            ta.style.overflowY = "hidden";
            ta.style.minHeight = MIN_HEIGHT + "px";
            ta.style.transition = "height 0.15s ease";

            const counter = doc.createElement("div");
            counter.style.cssText = "font-size:0.85rem;color:#6c538c;text-align:right;" +
                "margin-top:6px;margin-bottom:12px;font-family:'Helvetica Neue',Arial,sans-serif;";
            ta.parentElement.insertAdjacentElement("afterend", counter);

            function updateCounter() {
                const text = ta.value.trim();
                const words = text.length ? text.split(/\\s+/).length : 0;
                const chars = ta.value.length;
                counter.textContent = words + " words \\u00B7 " + chars + " characters";
            }

            function autoExpand() {
                ta.style.height = "auto";
                const next = Math.min(Math.max(ta.scrollHeight, MIN_HEIGHT), MAX_HEIGHT);
                ta.style.height = next + "px";
                ta.style.overflowY = ta.scrollHeight > MAX_HEIGHT ? "auto" : "hidden";
            }

            ta.addEventListener("input", () => { updateCounter(); autoExpand(); });
            updateCounter();
        });
    }

    setup();
    const observer = new MutationObserver(setup);
    observer.observe(doc.body, { childList: true, subtree: true });
})();
</script>
""", height=0)

selected_mood = st.radio(
    "How are you feeling?",
    options=list(MOOD_OPTIONS.keys()),
    horizontal=True,
)

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
                    "summary": response.text,
                    "mood": selected_mood,
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
        # .get() with a default handles entries saved before the mood
        # feature existed, so old data doesn't crash the page.
        mood_label = entry.get("mood", "😐 Neutral")
        mood_color = MOOD_OPTIONS.get(mood_label, "#B0A8C9")

        # Escaping here matters: this content is interpolated into raw HTML
        # via unsafe_allow_html=True. Without escaping, a journal entry
        # containing something like "<script>...</script>" would execute
        # as real HTML/JS every time this page renders — a stored XSS hole.
        safe_content = html_lib.escape(entry["content"]).replace("\n", "<br>")
        safe_summary = html_lib.escape(entry["summary"])
        safe_timestamp = html_lib.escape(entry["timestamp"])
        safe_mood_label = html_lib.escape(mood_label)

        st.markdown(f"""
            <details class="memory-card">
                <summary>
                    <span class="mood-dot" style="background-color:{mood_color};"></span>
                    {safe_mood_label} &nbsp;·&nbsp; 🔮 {safe_timestamp}
                </summary>
                <div class="memory-body">
                    <p><strong>Insight:</strong> <em>{safe_summary}</em></p>
                    <hr style="border: 0; height: 1px; background: rgba(161, 140, 209, 0.2); margin: 12px 0;">
                    <p>{safe_content}</p>
                </div>
            </details>
        """, unsafe_allow_html=True)
