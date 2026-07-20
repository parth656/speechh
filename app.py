import json
import os
import tempfile
from pathlib import Path

import streamlit as st
from audio_recorder_streamlit import audio_recorder

from speech_analyzer import SpeechAnalyzer

st.set_page_config(
    page_title="NeuroSpeech Coach",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ NeuroSpeech Coach")
st.caption("Speech-recognition feedback for practice. This is not a clinical diagnosis.")

MODEL_OPTIONS = {
    "Small English — recommended for Streamlit Cloud": "small.en",
    "Base English — fastest and lightest": "base.en",
    "Distil Large V3 — higher accuracy, heavier": "distil-large-v3",
    "Turbo — advanced multilingual, experimental on free cloud": "turbo",
    "Large V3 — maximum accuracy, likely too heavy for free cloud": "large-v3",
}


def save_audio(data: bytes, suffix: str) -> str:
    suffix = suffix if suffix.startswith(".") else f".{suffix}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as file:
        file.write(data)
        return file.name


@st.cache_resource(show_spinner=False, max_entries=1)
def get_analyzer(model_name: str) -> SpeechAnalyzer:
    return SpeechAnalyzer(model_name=model_name)


if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.header("Settings")
    selected_label = st.selectbox("Whisper model", list(MODEL_OPTIONS), index=0)
    selected_model = MODEL_OPTIONS[selected_label]
    threshold = st.slider("Review threshold", 0.20, 0.90, 0.55, 0.01)
    maximum = st.slider("Maximum focus words", 3, 20, 10)

    if selected_model in {"large-v3", "turbo"}:
        st.warning("This model may exceed Streamlit Community Cloud limits.")
    elif selected_model == "distil-large-v3":
        st.info("Good accuracy, but the first model download may take several minutes.")
    else:
        st.success("Cloud-friendly model selected.")

mode = st.radio(
    "Practice mode",
    ["Read a reference passage", "Free speech"],
    horizontal=True,
)

reference = ""
if mode == "Read a reference passage":
    reference = st.text_area(
        "Paste exactly what you plan to read",
        height=130,
        placeholder="The bright blue bird flew across the quiet garden.",
    )
else:
    st.info("Free-speech mode flags low-confidence content words; it cannot confirm pronunciation errors.")

record_tab, upload_tab = st.tabs(["Record speech", "Upload recording"])
audio_bytes = None
audio_suffix = ".wav"

with record_tab:
    recorded = audio_recorder(
        text="",
        recording_color="#dc2626",
        neutral_color="#2563eb",
        pause_threshold=3.0,
        sample_rate=16000,
    )
    if recorded:
        audio_bytes = recorded
        st.audio(recorded, format="audio/wav")

with upload_tab:
    uploaded = st.file_uploader(
        "Upload audio",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
    )
    if uploaded is not None:
        audio_bytes = uploaded.getvalue()
        audio_suffix = Path(uploaded.name).suffix or ".wav"
        st.audio(audio_bytes)

ready = bool(audio_bytes) and (
    mode == "Free speech" or bool(reference.strip())
)

if st.button(
    "Analyze my speech",
    type="primary",
    disabled=not ready,
    use_container_width=True,
):
    audio_path = save_audio(audio_bytes, audio_suffix)
    try:
        with st.status("Loading model and analyzing speech...", expanded=True) as status:
            analyzer = get_analyzer(selected_model)
            result = analyzer.analyze(
                audio_path=audio_path,
                mode=mode,
                reference=reference.strip(),
                threshold=threshold,
                maximum=maximum,
            )
            result["model"] = selected_model
            st.session_state.result = result
            status.update(label="Analysis complete", state="complete", expanded=False)
    except Exception as error:
        st.session_state.result = None
        st.error(f"Analysis failed: {error}")
        st.info("If the model is too heavy, select Small English or Base English and try again.")
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            pass

result = st.session_state.result
if result:
    st.divider()
    st.subheader("Transcript")
    st.write(result["text"] or "No speech was detected.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Duration", f'{result["duration"]:.1f}s')
    col2.metric("Words", result["word_count"])
    col3.metric("Review words", len(result["flagged_words"]))
    col4.metric("Speech rate", f'{result["words_per_minute"]:.0f} WPM')

    st.caption(
        f'Model: {result["model"]} | '
        f'Language: {result["language"]} '
        f'({result["language_probability"]:.0%})'
    )

    st.subheader("Words to review")
    if not result["flagged_words"]:
        st.success("No clear word mismatches or low-confidence content words were found.")

    for item in result["flagged_words"]:
        with st.container(border=True):
            st.markdown(f'### {item["word"]}')
            if mode == "Read a reference passage":
                st.write(f'Expected: **{item.get("expected", item["word"])}**')
                st.write(f'Whisper heard: **{item.get("heard", "Not detected")}**')
            st.write(f'Recognition confidence: **{item["confidence"]:.0%}**')
            st.caption(item["reason"])
            st.info(f'Say “{item["word"]}” slowly once, then at normal speed three times.')

    st.download_button(
        "Download JSON report",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name="speech_analysis.json",
        mime="application/json",
        use_container_width=True,
    )
