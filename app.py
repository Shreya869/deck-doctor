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
    .main { max-width: 750px; }
    h1 { font-size: 1.8rem; font-weight: 700; }
    .subtitle { color: #888; font-size: 0.95rem; margin-top: -10px; margin-bottom: 30px; }
    .score-box { padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🩺 deck doctor")
st.markdown('<p class="subtitle">upload a pitch deck or pitchbook → get a structured AI review in seconds</p>', unsafe_allow_html=True)


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

        st.markdown("---")
        st.markdown("### deck review")
        st.markdown(analysis)

        st.markdown("---")
        st.download_button(
            "download review as .txt",
            analysis,
            file_name=f"deck-review-{uploaded_file.name.replace('.pdf', '')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
