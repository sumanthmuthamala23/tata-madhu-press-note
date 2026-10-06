import os
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

# Custom Styling with Background Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Suranna&family=Ramabhadra&display=swap');
    
    /* Full App Page Background with Soft Telangana Pink Tint */
    .stApp {
        background: linear-gradient(135deg, #fff5f8 0%, #ffedf2 40%, #ffffff 100%);
        background-attachment: fixed;
    }
    
    /* Left Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #fff0f4;
        border-right: 1px solid #ffd1dc;
    }

    /* Official Letterhead Output Box */
    .press-box {
        background-color: #ffffff;
        border: 2px solid #b82329;
        border-radius: 10px;
        padding: 30px;
        box-shadow: 0 8px 24px rgba(184, 35, 41, 0.08);
        color: #111111;
        line-height: 1.85;
        font-family: 'Suranna', serif;
    }
    
    .press-header {
        text-align: center;
        border-bottom: 2px dashed #b82329;
        padding-bottom: 14px;
        margin-bottom: 22px;
    }
    
    .leader-title {
        color: #dc2626;
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        font-family: 'Ramabhadra', sans-serif;
    }
    
    .party-title {
        color: #374151;
        font-size: 15px;
        margin-top: 4px;
        font-weight: 600;
    }
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

def generate_press_note(client: genai.Client, parts: list, occasion: str, location: str):
    prompt_context = f"""
    సందర్భం (Occasion / Context): {occasion}
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
    
    occasion = st.selectbox(
        "ప్రకటన విభాగం / స్వభావం (Topic Scope)",
        [
            "రాష్ట్ర స్థాయి విధానాలు & ప్రభుత్వ వైఫల్యాలు (State Govt Policies / Criticisms)",
            "శాసనమండలి సమావేశాలు / స్పీచ్ (Legislative Council Proceedings)",
            "రైతు సంక్షేమం & వ్యవసాయ విధానాలు (Agriculture / Rythu Issues)",
            "పార్టీ రాజకీయాలు & జాతీయ అంశాలు (BRS Party / National Politics)",
            "ప్రజా సమస్యలు & విపత్తుల నిర్వహణ (Public Grievances / Inspections)",
            "మీడియా సమావేశం / కౌంటర్ అటాక్ (State Press Meet / Counter)",
            "సంతాపం / ప్రత్యేక శుభాకాంక్షలు (Condolences / Greetings)"
        ]
    )

# ----------------- MAIN UI -----------------
st.title("🎙️ ఎమ్మెల్సీ తాతా మధుసూదన్ - పత్రికా ప్రకటన జనరేటర్")
st.caption("వాయిస్ రికార్డింగ్, ఆడియో/వీడియో లేదా టెక్స్ట్ నోట్స్ ద్వారా మీడియా-రెడీ తెలుగు ప్రెస్ నోట్ రూపొందించండి.")

if not api_key_input:
    st.info("👈 దయచేసి ఎడమవైపు సైడ్‌బార్‌లో మీ Gemini API Keyని నమోదు చేయండి.")
    st.stop()

client = get_client(api_key_input)

# Input Tabs
tab1, tab2, tab3 = st.tabs(["🎤 లైవ్ రికార్డింగ్ (Mic)", "📁 ఆడియో / వీడియో అప్‌‌లోడ్", "✍️ సిట్యుయేషన్ నోట్స్ (Text)"])

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
    st.markdown("##### సందర్భం లేదా ముఖ్యమైన పాయింట్లు టైప్ చేయండి:")
    notes_text = st.text_area(
        "వివరాలు / పాయింట్లు",
        placeholder="ఉదాహరణ: రైతుల సమస్యలపై శాసనమండలిలో గళమెత్తిన ఎమ్మెల్సీ తాతా మధు. రుణమాఫీ వెంటనే పూర్తి చేయాలని డిమాండ్...",
        height=140
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
                press_note_telugu = generate_press_note(client, input_parts, occasion, location)
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
        <div style="border-top: 1px dashed #dc2626; margin-top: 25px; padding-top: 10px; text-align: right; font-size: 13px; color: #555;">
            విడుదల: ఎమ్మెల్సీ తాతా మధుసూదన్ గారి కార్యాలయం
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 టెక్స్ట్ ఫైల్‌‌గా డౌన్‌లోడ్ చేయండి",
            data=st.session_state["generated_note"],
            file_name=f"Tata_Madhu_Press_Note_{location.split()[0]}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        encoded_note = st.session_state["generated_note"][:1200]
        wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(encoded_note)}"
        st.link_button("📲 వాట్సాప్‌లో షేర్ చేయండి", wa_url, use_container_width=True)
