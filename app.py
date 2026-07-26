import json
import os
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from audio_recorder_streamlit import audio_recorder

from practice_generator import focus_words_from_profile, generate_practice_content
from speech_analyzer import MAX_REFERENCE_WORDS, STOP_WORDS, SpeechAnalyzer, tokenize

MAX_UPLOAD_BYTES = 25 * 1024 * 1024

st.set_page_config(page_title="NeuroSpeech Coach", page_icon="🎙️", layout="wide")
st.title("🎙️ NeuroSpeech Coach")
st.caption(
    "Independent speech-recognition feedback for practice — not a pronunciation "
    "assessment, clinical diagnosis, or speech-therapy substitute."
)

MODEL_OPTIONS = {
    "Small English — recommended for Streamlit Cloud": "small.en",
    "Base English — fastest and lightest": "base.en",
    "Distil Large V3 — English, higher accuracy, heavier": "distil-large-v3",
    "Turbo — multilingual, experimental on free cloud": "turbo",
    "Large V3 — multilingual, likely too heavy for free cloud": "large-v3",
}


def save_audio(data: bytes, suffix: str) -> str:
    suffix = suffix if suffix.startswith(".") else f".{suffix}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as file:
        file.write(data)
        return file.name


def update_practice_profile(result: dict, reference: str) -> None:
    """Track repeated review words for this browser session, not as model training."""
    profile = st.session_state.practice_profile
    expected_words = {word for word in tokenize(reference) if word not in STOP_WORDS}
    flagged_expected = {
        item.get("expected", item["word"])
        for item in result["flagged_words"]
        if item.get("expected", item["word"]) not in {"Not expected", "Not detected"}
    }

    for word in expected_words:
        stats = profile.setdefault(word, {"attempts": 0, "review_count": 0})
        stats["attempts"] += 1
        if word in flagged_expected:
            stats["review_count"] += 1


def render_spoken_practice(text: str) -> None:
    """Add browser-based text-to-speech without sending practice text to an API."""
    if not text:
        return
    # The practice generator only produces normalized focus words, but escape a
    # closing script tag as a defense-in-depth measure before embedding JSON.
    spoken_text = json.dumps(text).replace("</", "<\\/")
    components.html(
        f"""
        <div style="display:flex;gap:.5rem;align-items:center;font-family:sans-serif">
          <button id="speak" type="button">▶ Generate spoken practice</button>
          <button id="stop" type="button">■ Stop</button>
          <label for="rate">Speed</label>
          <select id="rate">
            <option value="0.8">Slow</option>
            <option value="1" selected>Normal</option>
            <option value="1.15">Fast</option>
          </select>
        </div>
        <script>
          const practiceText = {spoken_text};
          const speak = document.getElementById("speak");
          const stop = document.getElementById("stop");
          const rate = document.getElementById("rate");

          speak.addEventListener("click", () => {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(practiceText);
            utterance.lang = "en-US";
            utterance.rate = Number(rate.value);
            window.speechSynthesis.speak(utterance);
          }});
          stop.addEventListener("click", () => window.speechSynthesis.cancel());
        </script>
        """,
        height=55,
    )

    # Free-speech findings cannot establish a "wrong" word, but can still be
    # added as optional practice targets.
    if not expected_words:
        for item in result["flagged_words"]:
            word = item["word"]
            stats = profile.setdefault(word, {"attempts": 0, "review_count": 0})
            stats["review_count"] += 1


@st.cache_resource(show_spinner=False, max_entries=2)
def get_analyzer(model_name: str) -> SpeechAnalyzer:
    return SpeechAnalyzer(model_name=model_name)


for key, default in {
    "result": None,
    "result_input": None,
    "practice_profile": {},
    "practice_words": "",
    "generated_practice": "",
    "reference_text": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.pop("use_generated_practice", False):
    st.session_state.reference_text = st.session_state.generated_practice

with st.sidebar:
    st.header("Settings")
    selected_label = st.selectbox("Whisper model", list(MODEL_OPTIONS), index=0)
    selected_model = MODEL_OPTIONS[selected_label]
    threshold = st.slider("Review threshold", 0.20, 0.90, 0.55, 0.01)
    maximum = st.slider("Maximum review words", 3, 20, 10)

    if selected_model.endswith(".en") or selected_model == "distil-large-v3":
        language = "en"
        st.caption("This model is configured for English transcription.")
    else:
        language_choice = st.selectbox(
            "Transcription language",
            ["Detect automatically", "English"],
        )
        language = None if language_choice == "Detect automatically" else "en"

    if selected_model in {"large-v3", "turbo"}:
        st.warning("This model may exceed Streamlit Community Cloud limits.")
    elif selected_model == "distil-large-v3":
        st.info("The first model download can take several minutes.")
    else:
        st.success("Cloud-friendly model selected.")

mode = st.radio(
    "Practice mode", ["Read a reference passage", "Free speech"], horizontal=True
)

reference = ""
if mode == "Read a reference passage":
    reference = st.text_area(
        "Paste exactly what you plan to read",
        height=130,
        placeholder="The bright blue bird flew across the quiet garden.",
        key="reference_text",
    )
    reference_count = len(tokenize(reference))
    st.caption(f"{reference_count}/{MAX_REFERENCE_WORDS} reference words")
    if reference_count > MAX_REFERENCE_WORDS:
        st.error(f"Use at most {MAX_REFERENCE_WORDS} reference words.")
else:
    st.info(
        "Free-speech mode identifies words the transcription was less certain about. "
        "It cannot confirm a pronunciation error."
    )

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
        "Upload audio (maximum 25 MB)",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
    )
    if uploaded is not None:
        audio_bytes = uploaded.getvalue()
        audio_suffix = Path(uploaded.name).suffix or ".wav"
        st.audio(audio_bytes)

if audio_bytes and len(audio_bytes) > MAX_UPLOAD_BYTES:
    st.error("This recording is larger than 25 MB. Please upload a shorter recording.")
    audio_bytes = None

ready = bool(audio_bytes) and (
    mode == "Free speech"
    or (bool(reference.strip()) and len(tokenize(reference)) <= MAX_REFERENCE_WORDS)
)

if st.button("Analyze my speech", type="primary", disabled=not ready, use_container_width=True):
    audio_path = None
    try:
        audio_path = save_audio(audio_bytes, audio_suffix)
        with st.status("Loading model and analyzing speech...", expanded=True) as status:
            analyzer = get_analyzer(selected_model)
            result = analyzer.analyze(
                audio_path=audio_path,
                mode=mode,
                reference=reference.strip(),
                threshold=threshold,
                maximum=maximum,
                language=language,
            )
            result["model"] = selected_model
            result["language_setting"] = language or "automatic detection"
            st.session_state.result = result
            st.session_state.result_input = (mode, reference, len(audio_bytes), selected_model, language)
            update_practice_profile(result, reference)
            focus_words = focus_words_from_profile(st.session_state.practice_profile)
            if focus_words:
                st.session_state.generated_practice = generate_practice_content(
                    focus_words, "beginner", max(3, len(focus_words)), "paragraph"
                )
                st.session_state.practice_words = ", ".join(focus_words)
            status.update(label="Analysis complete", state="complete", expanded=False)
    except Exception as error:
        st.session_state.result = None
        st.error(f"Analysis failed: {error}")
        st.info("Try the Small English or Base English model, or use a shorter recording.")
    finally:
        if audio_path:
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
    col3.metric("Words to review", len(result["flagged_words"]))
    col4.metric("Speech rate", f'{result["words_per_minute"]:.0f} WPM')
    st.caption(
        f'Model: {result["model"]} | Language: {result["language"]} '
        f'({result["language_probability"]:.0%}) | '
        f'Setting: {result["language_setting"]}'
    )

    st.subheader("Words to review")
    st.caption(
        "These are transcription mismatches or low-confidence words, not verified "
        "pronunciation mistakes. Review them by listening back and practising slowly."
    )
    if not result["flagged_words"]:
        st.success("No clear transcription mismatches or low-confidence content words were found.")

    for item in result["flagged_words"]:
        with st.container(border=True):
            st.markdown(f'### {item["word"]}')
            if result["mode"] == "Read a reference passage":
                st.write(f'Expected: **{item.get("expected", item["word"])}**')
                st.write(f'Whisper heard: **{item.get("heard", "Not detected")}**')
            st.write(f'Transcription confidence: **{item["confidence"]:.0%}**')
            st.caption(item["reason"])
            st.info(f'Say “{item["word"]}” slowly once, then at normal speed three times.')

    report = {**result, "practice_profile": st.session_state.practice_profile}
    st.download_button(
        "Download JSON report",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name="speech_analysis.json",
        mime="application/json",
        use_container_width=True,
    )

st.divider()
st.subheader("Practice Generator")
st.caption(
    "Enter words yourself, or analyse a recording to automatically fill this "
    "with words that repeatedly need review in this browser session."
)
auto_focus_words = focus_words_from_profile(st.session_state.practice_profile)
if auto_focus_words:
    st.caption("Automatically suggested words: " + ", ".join(auto_focus_words))

practice_input = st.text_input(
    "Focus words (separate with commas or spaces)",
    placeholder="rhythm, comfortable, clear",
    key="practice_words",
)
practice_words = [
    word for word in tokenize(practice_input.replace(",", " ")) if word not in STOP_WORDS
]
level_col, style_col, count_col = st.columns(3)
practice_level = level_col.selectbox("Level", ["beginner", "intermediate", "advanced"])
practice_style = style_col.selectbox("Format", ["paragraph", "sentences"])
practice_count = count_col.slider("Practice sentences", 3, 12, 5)

if st.button("Generate practice", type="primary", use_container_width=True):
    if not practice_words:
        st.warning("Enter at least one focus word, or analyse a recording first.")
    else:
        st.session_state.generated_practice = generate_practice_content(
            practice_words, practice_level, practice_count, practice_style
        )

if st.session_state.generated_practice:
    st.text_area("Generated practice", st.session_state.generated_practice, height=150)
    st.caption("Listen in your browser. No practice text is sent to a text-to-speech service.")
    render_spoken_practice(st.session_state.generated_practice)
    if st.button("Use generated practice as my next reference"):
        st.session_state.use_generated_practice = True
        st.rerun()
