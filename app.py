import streamlit as st

from src.services.ocr_service import get_ocr_service
from src.services.extraction_service import ExtractionService
from src.services.validation_service import ErrorValidationService
from src.services.rag_service import RAGService

st.set_page_config(page_title="AI Support Technical Assistant", layout="centered")

st.markdown("""
<style>
.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 7rem;
}

h1 {
    font-size: 34px !important;
    font-weight: 700 !important;
    margin-bottom: 4px !important;
}

.subtitle {
    color: #6b7280;
    font-size: 15px;
    margin-bottom: 30px;
}

[data-testid="stChatMessage"] {
    border-radius: 14px;
    padding: 8px 14px;
    margin-bottom: 14px;
}

[data-testid="stChatInput"] {
    border-radius: 14px;
}

.source-card {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 14px 16px;
    margin-top: 10px;
    background: #fafafa;
}

.source-title {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 6px;
}

.source-meta {
    color: #6b7280;
    font-size: 13px;
}

.source-path {
    color: #4b5563;
    font-size: 13px;
    margin-top: 4px;
}

.answer-title {
    font-size: 14px;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 8px;
}

div[data-testid="stImage"] img {
    border-radius: 12px;
    max-height: 360px;
    object-fit: contain;
}
</style>
""", unsafe_allow_html=True)

OUT_OF_SCOPE_MESSAGE = "I cant help with unknown errors or non-technical issues. Please provide a technical error message or attach a screenshot of the error."

@st.cache_resource
def load_services():
    return {
        "ocr": get_ocr_service(),
        "extractor": ExtractionService(),
        "validator": ErrorValidationService(),
        "rag": RAGService()
    }

services = load_services()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("AI Support Technical Assistant")
st.markdown('<div class="subtitle">Technical error analysis using OCR, knowledge base and AI.</div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("image"):
            st.image(message["image"], width="stretch")

        st.markdown(message["content"])

        if message.get("citations"):
            st.markdown("#### Sources")

            for citation in message["citations"]:
                st.markdown(
                    f"""
                    <div class="source-card">
                        <div class="source-title">[{citation['source_id']}] {citation['title']}</div>
                        <div class="source-meta">Similarity: {citation['score']:.3f} · Chunk {citation['chunk_index']}</div>
                        <div class="source-path">Source: {citation['source_url']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

submission = st.chat_input(
    "Enter an error or attach a screenshot",
    accept_file=True,
    file_type=["png", "jpg", "jpeg", "webp"]
)

if submission:
    user_text = submission.text.strip() if submission.text else ""
    uploaded_file = submission.files[0] if submission.files else None
    image_bytes = uploaded_file.getvalue() if uploaded_file else None
    display_text = user_text if user_text else "Uploaded screenshot."

    st.session_state.messages.append({
        "role": "user",
        "content": display_text,
        "image": image_bytes
    })

    with st.chat_message("user"):
        if image_bytes:
            st.image(image_bytes, width="stretch")

        st.markdown(display_text)

    with st.chat_message("assistant"):
        try:
            if image_bytes:
                with st.spinner("Reading screenshot..."):
                    error_text = services["ocr"].extract_text(image_bytes)

                extracted = services["extractor"].extract(error_text)
                validation = services["validator"].validate(error_text, extracted)

                if not validation.is_valid:
                    st.markdown(OUT_OF_SCOPE_MESSAGE)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": OUT_OF_SCOPE_MESSAGE
                    })

                    st.stop()

                user_note = user_text

            else:
                if not user_text:
                    st.markdown(OUT_OF_SCOPE_MESSAGE)
                    st.stop()

                extracted = services["extractor"].extract(user_text)
                validation = services["validator"].validate(user_text, extracted)

                if not validation.is_valid:
                    st.markdown(OUT_OF_SCOPE_MESSAGE)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": OUT_OF_SCOPE_MESSAGE
                    })

                    st.stop()

                error_text = user_text
                user_note = ""

            with st.spinner("Analyzing error..."):
                result = services["rag"].solve(error_text=error_text, user_note=user_note)

            st.markdown(result.answer)

            if result.citations:
                st.markdown("Sources")

                for citation in result.citations:
                    st.markdown(
                        f"""
                        <div class="source-card">
                            <div class="source-title">[{citation.source_id}] {citation.title}</div>
                            <div class="source-meta">Similarity: {citation.score:.3f} · Chunk {citation.chunk_index}</div>
                            <div class="source-path">Source: {citation.source_url}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            st.session_state.messages.append({
                "role": "assistant",
                "content": result.answer,
                "citations": [citation.model_dump() for citation in result.citations]
            })

        except Exception as exc:
            st.error(f"Processing error: {exc}")