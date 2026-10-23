# NeuroSpeech Coach

A Streamlit speech-practice tool that records or uploads audio, transcribes it with Faster-Whisper, and highlights words worth reviewing. It can create a new practice passage from words that repeatedly need review during the current browser session and read passages aloud using browser speech synthesis.

> Transcript confidence and transcript mismatches are **not** pronunciation scores. Results are affected by recording quality, noise, accent, and speech-recognition errors. This app is not a clinical diagnosis or a replacement for a speech-language professional.

## How feedback works

### Reference-passage practice

The app transcribes the recording without supplying the expected passage to Whisper, then aligns the independent transcript with the reference. This avoids priming the recognizer toward the expected words. Words are marked as matching or needing review based on transcript agreement—not verified articulation correctness.

### Free speech

The app highlights content words with low transcription confidence as suggestions for review. Low confidence does not prove that a word was mispronounced.

### Personal practice

A small in-browser profile tracks words that repeatedly need review and can help generate practice passages. It does not train or fine-tune Whisper and does not promise to cure a speech difficulty. Browser speech synthesis depends on the user's browser and installed voices.

## Recommended deployment

The existing implementation recommends `base.en` for Streamlit Community Cloud because it has relatively low memory requirements. Larger models can exceed the memory limit of a free deployment. Verify available model identifiers against the installed Faster-Whisper version.

## Files

```text
app.py
speech_analyzer.py
practice_generator.py
test_speech_analyzer.py
requirements.txt
packages.txt
.gitignore
README.md
```

## Run locally

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Validate the code

```bash
python -m py_compile app.py speech_analyzer.py practice_generator.py
python -m unittest -v
```

## Deploy to Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a Streamlit Community Cloud app for this repository.
3. Select `app.py` as the main file.
4. Deploy and start with `base.en`.
5. Check logs after the first model download and analysis.

## Practical limits

- Audio uploads are limited to 25 MB.
- Reference passages are limited to 300 words.
- English-only models run in English mode; multilingual models may support language detection or an explicit language setting.
- The first analysis can be slower while model files are downloaded.

## Privacy and responsible use

Treat recordings as sensitive. Explain whether audio is kept in memory, stored, or sent to any external service. Do not use transcript agreement to make clinical, educational, hiring, or other high-stakes judgments.
