# NeuroSpeech Coach

A beginner-friendly Streamlit application that records or uploads speech, transcribes it with Faster-Whisper, and shows words that may need review.

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
```

## Deploy to Streamlit Community Cloud

1. Push all project files to GitHub.
2. Open Streamlit Community Cloud.
3. Select the repository and `app.py` as the main file.
4. Deploy or reboot the application.
5. Keep `small.en` selected initially.

The first analysis can take longer because the selected Whisper model must be downloaded.

## Important limitation

The confidence score comes from speech recognition. It is useful for practice feedback, but it is not a medical or speech-language diagnosis.
