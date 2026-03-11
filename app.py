import streamlit as st
import pdfplumber
import os
import io
from groq import Groq

st.set_page_config(
    page_title="deck doctor",
    page_icon="🩺",
    layout="centered",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        max-width: 760px;
        padding-top: 2rem;
    }

    /* hero */
    .hero {
        background: linear-gradient(135deg, #0f173c 0%, #1a1f4e 60%, #2d1b69 100%);
        border-radius: 20px;
        padding: 40px 36px 32px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: "";
        position: absolute;
        width: 220px; height: 220px;
        background: radial-gradient(circle, rgba(99,84,230,0.35) 0%, transparent 70%);
        top: -60px; right: -60px;
        border-radius: 50%;
    }
    .hero::after {
        content: "";
        position: absolute;
        width: 150px; height: 150px;
        background: radial-gradient(circle, rgba(255,99,107,0.2) 0%, transparent 70%);
        bottom: -40px; left: 20px;
        border-radius: 50%;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(99,84,230,0.3);
        border: 1px solid rgba(99,84,230,0.5);
        color: #a99ef5;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 14px;
        text-transform: uppercase;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 8px 0;
        line-height: 1.2;
    }
    .hero-sub {
        color: #9da4c7;
        font-size: 1rem;
        margin: 0;
        line-height: 1.5;
    }
    .hero-pills {
        margin-top: 20px;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .pill {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12);
        color: #c5c9e8;
        font-size: 0.78rem;
        padding: 4px 12px;
        border-radius: 20px;
    }

    /* upload card */
    .upload-card {
        background: #f7f7ff;
        border: 2px dashed #c5bef7;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 16px;
    }
    .upload-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #3d3580;
        margin-bottom: 8px;
    }

    /* result card */
    .result-card {
        background: #ffffff;
        border: 1px solid #e8e6ff;
        border-radius: 16px;
        padding: 28px 28px;
        margin-top: 8px;
        box-shadow: 0 4px 24px rgba(99,84,230,0.07);
    }
    .result-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a1740;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* stButton primary */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6354e6, #8b5cf6) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.6rem 1.5rem !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(99,84,230,0.35) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(99,84,230,0.45) !important;
    }

    .stDownloadButton > button {
        border-radius: 10px !important;
        border: 1.5px solid #6354e6 !important;
        color: #6354e6 !important;
        font-weight: 500 !important;
    }

    /* inputs */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        border: 1.5px solid #ddd9ff !important;
        font-size: 0.93rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6354e6 !important;
        box-shadow: 0 0 0 3px rgba(99,84,230,0.12) !important;
    }

    /* file uploader */
    [data-testid="stFileUploader"] {
        border-radius: 12px !important;
    }

    h3 { color: #1a1740; font-weight: 700; }
    hr { border-color: #ede9ff; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-badge">AI-powered</div>
    <div class="hero-title">🩺 deck doctor</div>
    <p class="hero-sub">upload a pitch deck or pitchbook and get a structured review — the way a Managing Director would read it.</p>
    <div class="hero-pills">
        <span class="pill">pitch decks</span>
        <span class="pill">pitchbooks</span>
        <span class="pill">CIMs</span>
        <span class="pill">investment memos</span>
        <span class="pill">strategy docs</span>
    </div>
</div>
""", unsafe_allow_html=True)


def get_client():
    api_key = st.secrets.get("GROQ_API_KEY", None) if hasattr(st, "secrets") else None
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


SYSTEM_PROMPT = """You are a senior investment banker with 20 years of experience reviewing pitch decks and pitchbooks at Goldman Sachs and Morgan Stanley.

You review decks the way a Managing Director would — you look for:
- Narrative clarity and flow
- Data quality and whether numbers are defended
- What a skeptical investor or buyer would immediately question
- What is missing that should be there
- Whether the ask/conclusion is earned by the evidence

You are direct, specific, and useful. You do not give generic feedback. You reference the actual content of the deck."""

ANALYSIS_PROMPT = """Review this pitch deck/document. Provide a structured analysis with these exact sections:

## overall verdict
One sentence: is this deck ready to send, needs work, or needs significant revision? Give a rating: Strong / Solid / Needs Work / Major Revision Needed.

## narrative & flow (score /10)
Does the story hold together? Is there a clear problem → solution → evidence → ask structure? Where does it break down?

## data & evidence (score /10)
Are claims backed by data? Which numbers are defensible and which are asserted without support? What data is missing that a sophisticated reader would expect?

## what a skeptical MD would immediately question
List the 3-5 things a Managing Director or senior partner would push back on in the first read. Be specific.

## what is missing
What sections, data points, or arguments are absent that should be present for this type of document?

## slide-by-slide notes
For each major section or slide (inferred from the content), give 1-2 sentence specific feedback.

## the 3 things to fix first
If you had to prioritize, what are the 3 highest-impact changes to make before sending this?

---
DECK CONTENT:
{content}"""


uploaded_file = st.file_uploader(
    "upload your deck (.pdf)",
    type=["pdf"],
    help="pitchbooks, pitch decks, CIMs, investment memos — anything goes"
)

context = st.text_input(
    "context (optional)",
    placeholder="e.g. Series B SaaS fundraise, M&A sell-side mandate, internal strategy review",
    help="helps the AI calibrate its feedback to the right standard"
)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

if st.button("analyse deck", type="primary", use_container_width=True):
    if not uploaded_file:
        st.error("upload a PDF first")
    else:
        client = get_client()
        if not client:
            st.error("groq api key not configured")
            st.stop()

        with st.status("reading deck...") as status:
            try:
                pdf_bytes = uploaded_file.read()
                text_pages = []
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text and text.strip():
                            text_pages.append(f"[Page {i+1}]\n{text.strip()}")

                if not text_pages:
                    st.error("could not extract text from this PDF. it may be image-based — try a text-based PDF.")
                    st.stop()

                full_text = "\n\n".join(text_pages)

                # truncate if too long (groq context window)
                if len(full_text) > 24000:
                    full_text = full_text[:24000] + "\n\n[document truncated for analysis]"

                status.update(label=f"extracted {len(text_pages)} pages ✓", state="complete")
            except Exception as e:
                st.error(f"could not read PDF: {e}")
                st.stop()

        with st.status("running analysis...") as status:
            try:
                context_note = f"\nContext provided: {context}" if context else ""
                prompt = ANALYSIS_PROMPT.format(content=full_text) + context_note

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                )
                analysis = response.choices[0].message.content
                status.update(label="analysis complete ✓", state="complete")
            except Exception as e:
                st.error(f"analysis failed: {e}")
                st.stop()

        st.markdown(f"""
        <div style="display:flex; gap:12px; margin: 20px 0 8px 0; flex-wrap:wrap;">
            <div style="background:#f0edff; border-radius:10px; padding:10px 18px; flex:1; min-width:140px;">
                <div style="font-size:0.72rem; color:#7c6fd4; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">file</div>
                <div style="font-size:0.9rem; color:#1a1740; font-weight:500; margin-top:2px;">{uploaded_file.name}</div>
            </div>
            <div style="background:#f0edff; border-radius:10px; padding:10px 18px; flex:1; min-width:140px;">
                <div style="font-size:0.72rem; color:#7c6fd4; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">pages extracted</div>
                <div style="font-size:0.9rem; color:#1a1740; font-weight:500; margin-top:2px;">{len(text_pages)} pages</div>
            </div>
            <div style="background:#f0edff; border-radius:10px; padding:10px 18px; flex:1; min-width:140px;">
                <div style="font-size:0.72rem; color:#7c6fd4; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">model</div>
                <div style="font-size:0.9rem; color:#1a1740; font-weight:500; margin-top:2px;">llama 3.3 70b</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="result-title">🩺 deck review</div>', unsafe_allow_html=True)
        st.markdown(analysis)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.download_button(
            "download review as .txt",
            analysis,
            file_name=f"deck-review-{uploaded_file.name.replace('.pdf', '')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
