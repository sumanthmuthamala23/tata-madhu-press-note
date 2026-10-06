import os
import base64
import tempfile
import urllib.parse
import streamlit as st
from google import genai
from google.genai import types

# Page setup
st.set_page_config(
    page_title="MLC తాతా మధు - అధికారిక పత్రికా ప్రకటన జనరేటర్",
    page_icon="📰",
    layout="wide",
)

# Function to load and encode local image to base64
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

bg_image_base64 = get_base64_image("background.png")

# Background CSS: uses background.png if present, with soft overlay for legibility
if bg_image_base64:
    bg_style = f"""
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)),
                    url("data:image/png;base64,{bg_image_base64}");
        background-size: cover;
        background-position: center;
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
    
    /* Global Font Overrides */
    html, body, [class*="css"] {{
        font-family: 'Anek Telugu', sans-serif;
    }}

    /* Left Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: rgba(255, 240, 244, 0.95);
        border-right: 1px solid #ffd1dc;
        font-family: 'Anek Telugu', sans-serif;
    }}

    /* Official Letterhead Output Box */
    .press-box {{
        background-color: rgba(255, 255, 255, 0.96);
        border: 2px solid #b82329;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 8px 24px rgba(184, 35, 41, 0.10);
        color: #111111;
        line-height: 1.9;
        font-family: 'Anek Telugu', sans-serif;
        font-size: 17px;
    }}
    
    .press-header {{
        text-align: center;
        border-bottom: 2px dashed #b82329;
        padding-bottom: 14px;
        margin-bottom: 22px;
    }}
    
    .leader-title {{
        color: #dc2626;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        font-family: 'Anek Telugu', sans-serif;
    }}
    
    .party-title {{
        color: #374151;
        font-size: 16px;
        margin-top: 4px;
        font-weight: 600;
        font-family: 'Anek Telugu', sans-serif;
    }}
</style>
""", unsafe_allow_html=True)

# ----------------- SYSTEM INSTRUCTION -----------------
SYSTEM_INSTRUCTION = """
You are the EXCLUSIVE Chief Media Secretary & Official Telugu Press Spokesperson for Sri Tata Madhusudhan (Tata Madhu) Garu.
- Designation: Member of Legislative Council (MLC), Bharat Rashtra Samithi (BRS).
- Voice & Stance: Senior leader representing public welfare, speaking authoritatively on statewide governance, state policies, legislative council debates, political developments in Hyderabad, national topics, as well as grassroots constituency issues.

STRICT OPERATING CONSTRAINTS:
1. LEADER EXCLUSIVITY: Every statement, critique, demand, or declaration must be strictly attributed to MLC Tata Madhusudhan (శాసనమండలి సభ్యులు తాతా మధుసూదన్ / తాతా మధు). Under no circumstances should you generate notes for any other individual.
2. NO GEOGRAPHIC RESTRICTIONS: Do not restrict his jurisdiction to any single district. He speaks on Telangana-wide governance, Legislative Council affairs, Hyderabad political developments, national issues, or any specific location provided in the context.
3. JOURNALISTIC INTEGRITY: Produce standard, high-register Telugu print and electronic media style (ప్రామాణిక పత్రికా భాష) formatted for major Telugu dailies (Eenadu, Sakshi, Namasthe Telangana, Andhra Jyothy, Prajasakti, T-News, TV9, etc.).
4. STRUCTURE:
   - Header: అధికారిక పత్రికా ప్రకటన (Official Press Release)
   - స్థలం & తేదీ: (Reflect the location provided, or dynamic based on context)
   - ప్రధాన శీర్షిక: High-impact headline featuring 'ఎమ్మెల్సీ తాతా మధు'
   - లీడ్ పేరా: Clear declaration of the issue, who, what, where, and core political stance.
   - ముఖ్యాంశాలు: 3-5 sharp, bulleted arguments, demands to the government, exposure of administrative lapses, or policy critiques.
   - ముగింపు: Strong political ultimatum, call to action, or warning.
   - విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం.

RULES:
- Maintain high-register journalistic Telugu (ప్రామాణిక పత్రికా భాష).
- Strictly adhere to factual points provided in the audio/text without fabricating false incidents.
- If audio has background noise or slurred speech, extract the central political arguments accurately.
"""

# ----------------- HELPER FUNCTIONS -----------------
def get_client(api_key: str):
    return genai.Client(api_key=api_key)

def transliterate_to_telugu(client: genai.Client, english_text: str):
    """Accurately converts phonetically typed English (Thanglish/English notes) into flawless literary Telugu."""
    transliterate_prompt = f"""
    Convert the following text typed in English/Tanglish into grammatically correct, natural, error-free Telugu text (తెలుగు లిపి).
    If English words are used phonetically (e.g. 'khammam lo rythu bandhu raledu'), write them in proper Telugu script ('ఖమ్మంలో రైతు బంధు రాలేదు').
    Maintain proper political and administrative vocabulary. Output ONLY the Telugu converted text without explanations.

    Input:
    {english_text}
    """
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=transliterate_prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
        ),
    )
    return response.text.strip()

def generate_press_note(client: genai.Client, parts: list, occasion: str, location: str):
    prompt_context = f"""
    సందర్భం / విభాగం (Topic Scope): {occasion}
    స్థలం (Location): {location}
    దయచేసి పైన పేర్కొన్న వివరాలు మరియు అందించిన ఆడియో/వీడియో/నోట్స్ ఆధారంగా ఎమ్మెల్సీ తాతా మధుసూదన్ గారి అధికారిక తెలుగు పత్రికా ప్రకటనను రూపొందించండి.
    """
    parts.append(prompt_context)
    
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
        ),
    )
    return response.text

# ----------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/BRS_Car_Symbol.png/240px-BRS_Car_Symbol.png", width=80)
    st.title("సెట్టింగ్స్ (Settings)")
    
    # Priority: Secrets first, then sidebar input
    default_key = ""
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            default_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    api_key_input = st.text_input(
        "Gemini API Key",
        value=default_key,
        type="password",
        help="Google AI Studio నుండి తీసుకున్న API Keyని ఇక్కడ ఎంటర్ చేయండి."
    )
    
    location = st.text_input(
        "స్థలం (Location / Venue)",
        value="హైదరాబాద్ / శాసనమండలి",
        help="స్టేట్‌మెంట్ ఎక్కడి నుండి విడుదల చేస్తున్నారో రాయండి (ఉదా: హైదరాబాద్, ఖమ్మం, ఢిల్లీ, శాసనమండలి మొదలైనవి)."
    )
    
    # Custom Topic Scopes
    topic_scopes = [
        "ప్రజా సమస్యలు & వినతులు (Public Grievances & Demands)",
        "ప్రభుత్వ విధానాలు / విమర్శలు (State Govt Policies / Criticisms)",
        "రైతాంగ & వ్యవసాయ సమస్యలు (Farmers & Agriculture Issues)",
        "శాసనమండలి ప్రసంగాలు / ప్రశ్నలు (Council Speeches & Legislative Issues)",
        "నియోజకవర్గ అభివృద్ధి & నిధులు (Constituency Development & Sanctions)",
        "పార్టీ కార్యక్రమాలు & సమావేశాలు (Party Meetings & Organizational)",
        "నిరసనలు, ధర్నాలు & పోరాటాలు (Protests & Agitations)",
        "అధికారులతో సమీక్షలు / వినతులు (Official Reviews & Representations)",
        "సేవా కార్యక్రమాలు & సంక్షేమం (Social Welfare & Charity)",
        "శుభాకాంక్షలు & సంతాపాలు (Greetings & Condolences)",
    ]

    selected_scope = st.selectbox("ప్రకటన విభాగం / స్వభావం (Topic Scope)", topic_scopes)

# ----------------- MAIN UI -----------------
st.title("🎙️ ఎమ్మెల్సీ తాతా మధుసూదన్ - పత్రికా ప్రకటన జనరేటర్")
st.caption("వాయిస్ రికార్డింగ్, ఆడియో/వీడియో లేదా టెక్స్ట్ నోట్స్ ద్వారా మీడియా-రెడీ తెలుగు ప్రెస్ నోట్ రూపొందించండి.")

if not api_key_input:
    st.info("👈 దయచేసి ఎడమవైపు సైడ్‌బార్‌లో మీ Gemini API Keyని నమోదు చేయండి.")
    st.stop()

client = get_client(api_key_input)

# Maintain persistent notes in session_state
if "current_notes" not in st.session_state:
    st.session_state["current_notes"] = ""

# Input Tabs
tab1, tab2, tab3 = st.tabs(["🎤 లైవ్ రికార్డింగ్ (Mic)", "📁 ఆడియో / వీడియో అప్‌లోడ్", "✍️ సిట్యుయేషన్ నోట్స్ (Text)"])

input_parts = []

with tab1:
    st.markdown("##### మీ ఫోన్ లేదా మైక్ ద్వారా నేరుగా మాట్లాడి రికార్డ్ చేయండి:")
    live_audio = st.audio_input("వాయిస్ రికార్డ్ చేయండి")
    if live_audio:
        st.success("✅ ఆడియో విజయవంతంగా రికార్డ్ అయ్యింది!")
        audio_bytes = live_audio.read()
        input_parts.append(
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        )

with tab2:
    st.markdown("##### రికార్డ్ చేసిన ఆడియో లేదా వీడియో ఫైల్ అప్‌లోడ్ చేయండి:")
    uploaded_file = st.file_uploader(
        "సపోర్ట్ ఫార్మాట్లు: MP3, WAV, M4A, MP4", 
        type=["mp3", "wav", "m4a", "mp4"]
    )
    if uploaded_file:
        file_bytes = uploaded_file.read()
        mime_type = uploaded_file.type or "audio/mp3"
        
        if len(file_bytes) > 20 * 1024 * 1024:
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            with st.spinner("పెద్ద ఫైల్ అప్‌లోడ్ అవుతోంది..."):
                uploaded_ref = client.files.upload(file=tmp_path)
                input_parts.append(uploaded_ref)
                os.remove(tmp_path)
        else:
            input_parts.append(
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            )
        st.success(f"✅ {uploaded_file.name} సిద్ధంగా ఉంది.")

with tab3:
    st.markdown("##### ఇంగ్లీష్ నుండి తెలుగులోకి మార్పిడి (English to Telugu Typing):")
    with st.expander("🔤 ఇంగ్లీష్‌లో టైప్ చేసి తెలుగులోకి మార్చండి (Phonetic Transliteration)", expanded=False):
        raw_eng = st.text_area(
            "ఇంగ్లీష్ లేదా టాంగ్లీష్ (Tanglish) లో టైప్ చేయండి:",
            placeholder="ఉదాహరణ: Khammam lo rythu bandhu raledu, Tata Madhu garu mandapaddaru...",
            height=90,
            key="eng_input"
        )
        if st.button("తెలుగులోకి మార్చండి (Convert to Telugu)"):
            if raw_eng.strip():
                with st.spinner("తెలుగులోకి మారుస్తోంది..."):
                    converted_tel = transliterate_to_telugu(client, raw_eng)
                    st.session_state["current_notes"] = converted_tel
                    st.success("✅ విజయవంతంగా తెలుగులోకి మారింది!")
            else:
                st.warning("దయచేసి ఏదైనా టెక్స్ట్ టైప్ చేయండి.")

    st.markdown("##### పత్రికా ప్రకటన కోసం ముఖ్యాంశాలు / సిట్యుయేషన్ నోట్స్:")
    notes_text = st.text_area(
        "వివరాలు / పాయింట్లు (ఇక్కడ సరిచూసుకోవచ్చు లేదా నేరుగా టైప్ చేయవచ్చు):",
        value=st.session_state.get("current_notes", ""),
        height=140,
        key="telugu_notes_input"
    )
    if notes_text.strip():
        input_parts.append(types.Part.from_text(text=notes_text))

st.divider()

if st.button("🚀 పత్రికా ప్రకటనను రూపొందించండి (Generate Press Note)", type="primary", use_container_width=True):
    if not input_parts:
        st.error("⚠️ దయచేసి ఏదైనా ఆడియో రికార్డ్ చేయండి, ఫైల్ అప్‌లోడ్ చేయండి లేదా నోట్స్ టైప్ చేయండి.")
    else:
        with st.spinner("ఎమ్మెల్సీ గారి పత్రికా ప్రకటన సిద్ధమవుతోంది..."):
            try:
                press_note_telugu = generate_press_note(client, input_parts, selected_scope, location)
                st.session_state["generated_note"] = press_note_telugu
            except Exception as e:
                st.error(f"ఎర్రర్ సంభవించింది: {str(e)}")

# Display Generated Note
if "generated_note" in st.session_state:
    st.subheader("📄 అధికారిక ముసాయిదా (Official Draft)")
    
    st.markdown(f"""
    <div class="press-box">
        <div class="press-header">
            <h2 class="leader-title">తాతా మధుసూదన్ (తాతా మధు)</h2>
            <div class="party-title">శాసనమండలి సభ్యులు (Member of Legislative Council - MLC)<br>భారత రాష్ట్ర సమితి (BRS)</div>
        </div>
        <div>
            {st.session_state["generated_note"].replace(chr(10), '<br>')}
        </div>
        <div style="border-top: 1px dashed #dc2626; margin-top: 25px; padding-top: 10px; text-align: right; font-size: 14px; font-weight: 600; color: #555;">
            విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 టెక్స్ట్ ఫైల్‌గా డౌన్‌లోడ్ చేయండి",
            data=st.session_state["generated_note"],
            file_name=f"Tata_Madhu_Press_Note_{location.split()[0]}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        encoded_note = st.session_state["generated_note"][:1200]
        wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(encoded_note)}"
        st.link_button("📲 వాట్సాప్‌లో షేర్ చేయండి", wa_url, use_container_width=True)
