import os
import time
import base64
import tempfile
import urllib.parse
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Page setup
st.set_page_config(
    page_title="MLC తాతా మధు - ప్రెస్ నోట్ జనరేటర్",
    page_icon="📰",
    layout="wide",
)

# Background Image Base64 Converter
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

bg_image_base64 = get_base64_image("background.png")

if bg_image_base64:
    bg_style = f"""
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)),
                    url("data:image/png;base64,{bg_image_base64}");
        background-size: cover;
        background-position: center top;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    """
else:
    bg_style = """
    .stApp {
        background: linear-gradient(135deg, #fff5f8 0%, #ffedf2 40%, #ffffff 100%);
        background-attachment: fixed;
    }
    """

# Custom Styling with Anek Telugu Font
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Anek+Telugu:wght@300;400;500;600;700;800&display=swap');
    
    {bg_style}
    
    html, body, [class*="css"], .stMarkdown, p, span, div, input, textarea, button {{
        font-family: 'Anek Telugu', sans-serif !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: rgba(255, 242, 245, 0.96) !important;
        border-right: 1.5px solid #ffccd5;
    }}

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }}

    /* Official Press Note Container */
    .press-box {{
        background-color: #ffffff;
        border: 2px solid #b82329;
        border-radius: 12px;
        padding: 32px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        color: #111111;
        line-height: 1.9;
        font-size: 18px;
    }}
    
    .press-header {{
        text-align: center;
        border-bottom: 2px dashed #b82329;
        padding-bottom: 16px;
        margin-bottom: 24px;
    }}
    
    .leader-title {{
        color: #dc2626;
        font-size: 30px;
        font-weight: 800;
        margin: 0;
    }}
    
    .party-title {{
        color: #374151;
        font-size: 17px;
        margin-top: 6px;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# ----------------- SYSTEM INSTRUCTION -----------------
SYSTEM_INSTRUCTION = """
You are the EXCLUSIVE Chief Media Secretary & Official Telugu Press Spokesperson for Sri Tata Madhusudhan (Tata Madhu) Garu.
- Designation: Member of Legislative Council (MLC), Bharat Rashtra Samithi (BRS).
- Voice & Tone: Senior legislative leader representing the public interest, authoritative, articulate, and politically assertive.

STRICT CONSTRAINTS:
1. LEADER EXCLUSIVITY: Every statement, critique, demand, or declaration must be strictly attributed to MLC Tata Madhusudhan (శాసనమండలి సభ్యులు తాతా మధుసూదన్ / తాతా మధు).
2. NO JURISDICTION BOUNDARIES: Do not limit him to any single district. He issues statements on state policies, legislative council debates, Hyderabad affairs, national topics, and grassroots public grievances.
3. STANDARD JOURNALISTIC TELUGU: Write in high-standard news Telugu (ప్రామాణిక పత్రికా భాష) formatted for Telugu daily newspapers (Eenadu, Sakshi, Namasthe Telangana, Andhra Jyothy, etc.).
4. STRUCTURE:
   - Header: అధికారిక పత్రికా ప్రకటన
