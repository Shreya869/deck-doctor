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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { max-width: 760px; padding-top: 2rem; padding-bottom: 4rem; }

    /* ── animations ── */
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50%       { transform: translateY(-8px); }
    }
    @keyframes pulse-ring {
        0%   { box-shadow: 0 0 0 0 rgba(99,84,230,0.4); }
        70%  { box-shadow: 0 0 0 12px rgba(99,84,230,0); }
        100% { box-shadow: 0 0 0 0 rgba(99,84,230,0); }
    }
    @keyframes shimmer {
        0%   { background-position: -400px 0; }
        100% { background-position: 400px 0; }
    }
    @keyframes pill-float {
        0%   { transform: translateY(0px); opacity: 0.85; }
        50%  { transform: translateY(-3px); opacity: 1; }
        100% { transform: translateY(0px); opacity: 0.85; }
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }

    /* ── hero ── */
    .hero {
        background: linear-gradient(135deg, #0a0f2e 0%, #14184a 50%, #251060 100%);
        border-radius: 24px;
        padding: 44px 40px 36px;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
        animation: fadeSlideUp 0.6s ease both;
    }
    .hero::before {
        content: "";
        position: absolute;
        width: 280px; height: 280px;
        background: radial-gradient(circle, rgba(99,84,230,0.4) 0%, transparent 65%);
        top: -80px; right: -80px;
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    .hero::after {
        content: "";
        position: absolute;
        width: 180px; height: 180px;
        background: radial-gradient(circle, rgba(255,99,107,0.25) 0%, transparent 65%);
        bottom: -50px; left: -30px;
        border-radius: 50%;
        animation: float 8s ease-in-out infinite reverse;
    }
    .hero-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(99,84,230,0.25);
        border: 1px solid rgba(99,84,230,0.45);
        color: #b8afff;
        font-size: 0.7rem; font-weight: 700;
        letter-spacing: 0.12em;
        padding: 5px 14px;
        border-radius: 20px;
        margin-bottom: 16px;
        text-transform: uppercase;
        animation: fadeSlideUp 0.6s 0.1s ease both;
    }
    .badge-dot {
        width: 6px; height: 6px;
        background: #7c6ff5;
        border-radius: 50%;
        animation: pulse-ring 2s infinite;
        display: inline-block;
    }
    .hero-title {
        font-size: 2.6rem; font-weight: 800;
        color: #fff; margin: 0 0 10px 0; line-height: 1.15;
        animation: fadeSlideUp 0.6s 0.15s ease both;
    }
    .hero-sub {
        color: #8f98c4; font-size: 1rem; margin: 0; line-height: 1.6;
        animation: fadeSlideUp 0.6s 0.2s ease both;
        max-width: 520px;
    }
    .hero-pills {
        margin-top: 22px; display: flex; gap: 8px; flex-wrap: wrap;
        animation: fadeSlideUp 0.6s 0.25s ease both;
    }
    .pill {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.11);
        color: #bbc2e4; font-size: 0.76rem;
        padding: 5px 13px; border-radius: 20px;
        animation: pill-float 4s ease-in-out infinite;
        cursor: default;
        transition: background 0.2s, border-color 0.2s;
    }
    .pill:hover {
        background: rgba(99,84,230,0.2);
        border-color: rgba(99,84,230,0.4);
        color: #d0caff;
    }
    .pill:nth-child(2) { animation-delay: 0.3s; }
    .pill:nth-child(3) { animation-delay: 0.6s; }
    .pill:nth-child(4) { animation-delay: 0.9s; }
    .pill:nth-child(5) { animation-delay: 1.2s; }

    /* ── upload zone ── */
    .upload-zone {
        background: linear-gradient(135deg, #f8f7ff, #f3f0ff);
        border: 2px dashed #c4baf5;
        border-radius: 18px;
        padding: 28px 24px 20px;
        margin-bottom: 16px;
        transition: border-color 0.25s, background 0.25s;
        animation: fadeSlideUp 0.6s 0.3s ease both;
    }
    .upload-zone:hover {
        border-color: #8b7cf6;
        background: linear-gradient(135deg, #f3f0ff, #ede8ff);
    }
    .upload-label {
        font-size: 0.8rem; font-weight: 700; color: #5046a8;
        letter-spacing: 0.06em; text-transform: uppercase;
        margin-bottom: 10px;
    }

    /* ── context input ── */
    .context-wrap {
        animation: fadeSlideUp 0.6s 0.35s ease both;
    }
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1.5px solid #ddd9ff !important;
        font-size: 0.93rem !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #7c6ff5 !important;
        box-shadow: 0 0 0 3px rgba(99,84,230,0.13) !important;
    }

    /* ── CTA button ── */
    .cta-wrap {
        animation: fadeSlideUp 0.6s 0.4s ease both;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6354e6 0%, #9b5cf6 100%) !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.02em !important;
        padding: 0.75rem 2rem !important;
        color: white !important;
        box-shadow: 0 6px 20px rgba(99,84,230,0.38) !important;
        transition: all 0.22s ease !important;
        animation: pulse-ring 3s 1s infinite !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 10px 28px rgba(99,84,230,0.5) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0px) scale(0.99) !important;
    }

    /* ── meta chips ── */
    .meta-row {
        display: flex; gap: 10px; margin: 24px 0 12px; flex-wrap: wrap;
        animation: fadeSlideUp 0.5s ease both;
    }
    .meta-chip {
        background: linear-gradient(135deg, #f0edff, #e8e3ff);
        border: 1px solid #d4ceff;
        border-radius: 12px;
        padding: 10px 16px; flex: 1; min-width: 130px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .meta-chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(99,84,230,0.12);
    }
    .meta-chip-label {
        font-size: 0.68rem; color: #7c6fd4;
        font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.07em;
    }
    .meta-chip-value {
        font-size: 0.88rem; color: #1a1740;
        font-weight: 600; margin-top: 3px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    /* ── result card ── */
    .result-card {
        background: #fff;
        border: 1px solid #e5e0ff;
        border-radius: 20px;
        padding: 32px 32px;
        box-shadow: 0 8px 32px rgba(99,84,230,0.08);
        animation: fadeSlideUp 0.6s ease both;
    }
    .result-header {
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid #f0ecff;
    }
    .result-header-icon {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #6354e6, #9b5cf6);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem;
    }
    .result-header-text {
        font-size: 1.05rem; font-weight: 700; color: #1a1740;
    }
    .result-header-sub {
        font-size: 0.78rem; color: #9591b8; margin-top: 1px;
    }

    /* ── download button ── */
    .stDownloadButton > button {
        border-radius: 12px !important;
        border: 1.5px solid #7c6ff5 !important;
        color: #6354e6 !important;
        font-weight: 600 !important;
        background: white !important;
        transition: all 0.2s ease !important;
        padding: 0.55rem 1.2rem !important;
    }
    .stDownloadButton > button:hover {
        background: #f3f0ff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(99,84,230,0.15) !important;
    }

    /* ── file uploader ── */
    [data-testid="stFileUploader"] section {
        border-radius: 14px !important;
        border: none !important;
        background: transparent !important;
    }
    [data-testid="stFileUploader"] section > div {
        background: transparent !important;
    }

    h3 { color: #1a1740; font-weight: 700; }
    hr { border: none; border-top: 1px solid #ede9ff; margin: 20px 0; }

    /* ── success badge ── */
    .success-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: #ecfdf5; border: 1px solid #a7f3d0;
        color: #065f46; border-radius: 20px;
        font-size: 0.78rem; font-weight: 600;
        padding: 4px 12px; margin-bottom: 16px;
        animation: fadeIn 0.4s ease both;
    }
</style>
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
Does the story hold together? Is there a clear problem > solution > evidence > ask structure? Where does it break down?

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


# ── hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge"><span class="badge-dot"></span> AI-powered review</div>
    <div class="hero-title">🩺 deck doctor</div>
    <p class="hero-sub">upload a pitch deck or pitchbook and get a structured, honest review — the way a Managing Director would read it.</p>
    <div class="hero-pills">
        <span class="pill">pitch decks</span>
        <span class="pill">pitchbooks</span>
        <span class="pill">CIMs</span>
        <span class="pill">investment memos</span>
        <span class="pill">strategy docs</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── upload zone ───────────────────────────────────────────────────────────────
st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
st.markdown('<div class="upload-label">step 1 — upload your deck</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "drag and drop a PDF or click to browse",
    type=["pdf"],
    label_visibility="collapsed",
)
st.markdown('</div>', unsafe_allow_html=True)

# ── context input ─────────────────────────────────────────────────────────────
st.markdown('<div class="context-wrap">', unsafe_allow_html=True)
context = st.text_input(
    "step 2 — add context (optional)",
    placeholder="e.g. Series B SaaS fundraise, M&A sell-side mandate, internal strategy review",
    help="helps the AI calibrate its feedback to the right standard",
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── CTA ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="cta-wrap">', unsafe_allow_html=True)
analyse = st.button("analyse deck", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── logic ─────────────────────────────────────────────────────────────────────
if analyse:
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
                if len(full_text) > 24000:
                    full_text = full_text[:24000] + "\n\n[document truncated for analysis]"

                status.update(label=f"extracted {len(text_pages)} pages ✓", state="complete")
            except Exception as e:
                st.error(f"could not read PDF: {e}")
                st.stop()

        with st.status("analysing with MD-level lens...") as status:
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
                status.update(label="review ready ✓", state="complete")
            except Exception as e:
                st.error(f"analysis failed: {e}")
                st.stop()

        # meta chips
        st.markdown(f"""
        <div class="meta-row">
            <div class="meta-chip">
                <div class="meta-chip-label">file</div>
                <div class="meta-chip-value">{uploaded_file.name}</div>
            </div>
            <div class="meta-chip">
                <div class="meta-chip-label">pages read</div>
                <div class="meta-chip-value">{len(text_pages)} pages</div>
            </div>
            <div class="meta-chip">
                <div class="meta-chip-label">reviewer model</div>
                <div class="meta-chip-value">llama 3.3 70b</div>
            </div>
            <div class="meta-chip">
                <div class="meta-chip-label">context</div>
                <div class="meta-chip-value">{context if context else "general review"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # result card
        st.markdown("""
        <div class="result-card">
            <div class="result-header">
                <div class="result-header-icon">🩺</div>
                <div>
                    <div class="result-header-text">deck review</div>
                    <div class="result-header-sub">senior banker perspective — direct, specific, no fluff</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(analysis)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.download_button(
            "download review as .txt",
            analysis,
            file_name=f"deck-review-{uploaded_file.name.replace('.pdf', '')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
