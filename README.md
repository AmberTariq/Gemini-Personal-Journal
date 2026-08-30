# 🔮 My Dreamy Gemini Journal

**My Dreamy Gemini Journal** is a secure, ambient, and highly personalized digital diary designed for daily reflections. Built using **Python** and **Streamlit**, this application leverages the advanced **Gemini 3.5 Flash** engine via Google AI Studio to deliver an intelligent, context-aware journaling experience wrapped inside a responsive, tailored user interface.

---

## 🚀 Key Features

* **Advanced AI Reflection**: Powered by the **Gemini 3.5 Flash** engine, providing instant, empathetic, and deeply contextual feedback on your journal entries.
* **Security-First Architecture**: Engineered with strict cloud security principles configured via system instructions to act like a rigid security barrier.
* **Absolute Multi-Tenant Isolation**: Complete database and memory containment guarantees that User A can never cross-contaminate or view User B's private logs.
* **Adaptive Pastel UI**: Features a resolution-independent **Lavender Dusk** theme optimized seamlessly for both mobile and desktop screens.
* **Live Analytics**: Features real-time word and character counters alongside an interactive mood tracking selector (Happy, Calm, Neutral, Sad, Stressed, Inspired).

---

## 🛠️ Tech Stack

* **Frontend & UI Framework:** [Streamlit](https://streamlit.io/)
* **Core Language:** [Python](https://www.python.org/)
* **LLM Engine:** [Google AI Studio (Gemini 3.5 Flash)](https://ai.google.dev/)

---

## 📦 Getting Started

### Prerequisites
Make sure you have Python 3.9+ installed on your system.

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/my-dreamy-gemini-journal.git
cd my-dreamy-gemini-journal
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the root directory and add your Gemini API Key:
```env
GEMINI_API_KEY=your_api_key_here
```

### 4. Run the Application
```bash
streamlit run app.py
```

---

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
