# NeuroSpeech Coach

A Streamlit practice tool that records or uploads speech, transcribes it with Faster-Whisper, and highlights words worth reviewing. It can also build a new practice passage from words that have repeatedly needed review during the current browser session.

> Important: transcription confidence and transcript mismatches are **not** pronunciation scores. They can be affected by recording quality, noise, accent, and speech-recognition errors. This app is not a clinical diagnosis or a replacement for a speech-language professional.

## How feedback works

For reference-passage practice, the app transcribes the audio **without giving Whisper the expected passage**, then aligns the independent transcript with the reference. This avoids priming the recognizer toward words that the speaker was expected to say.

For free speech, the app highlights content words with low transcription confidence. These are suggestions to review, not confirmed mistakes.

The personal practice feature stores a small in-browser profile of words that repeatedly need review. It does not train, fine-tune, or modify Whisper, and it cannot promise to correct a speech difficulty quickly.

## Recommended deployment model

Use **Small English (`small.en`)** on Streamlit Community Cloud. It provides a practical balance between accuracy, download size, memory use, and CPU speed.

The heavier models are optional:

- `base.en`: fastest and lightest fallback
- `small.en`: recommended cloud model
- `distil-large-v3`: better English accuracy but heavier
- `turbo`: advanced multilingual model; experimental on free cloud
- `large-v3`: maximum accuracy but normally too heavy for free cloud

## Files

```text
.
├── app.py
├── speech_analyzer.py
├── practice_generator.py
├── test_speech_analyzer.py
├── requirements.txt
├── packages.txt
├── .gitignore
└── README.md
```

## Run locally

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Check the Python files

```bash
python -m py_compile app.py speech_analyzer.py
python -m unittest -v
```

## Deploy to Streamlit Community Cloud

1. Push all project files to GitHub.
2. Open Streamlit Community Cloud.
3. Select the repository and `app.py` as the main file.
4. Deploy or reboot the application.
5. Keep `small.en` selected initially.

The first analysis can take longer because the selected Whisper model must be downloaded.

## Practical limits

- Uploads are limited to 25 MB.
- Reference passages are limited to 300 words so word-by-word review remains responsive.
- English-only Whisper models are kept in English mode. Multilingual models can either detect language automatically or be set to English.
