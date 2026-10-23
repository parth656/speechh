# NeuroSpeech Coach Testing

## Automated checks

The README documents these local checks:

```bash
python -m py_compile app.py speech_analyzer.py practice_generator.py
python -m unittest -v
```

Run them after modifying the analysis, practice-generation, or application code.

## Manual test matrix

| Scenario | Expected behavior |
|---|---|
| Clear reference passage | Transcript is aligned against the reference |
| Wrong or missing word | Marked for review, not called a confirmed pronunciation error |
| Free speech with low confidence | Suggested review words are highlighted |
| Noisy or silent audio | Clear message or limited result, not an unhandled crash |
| File over 25 MB | Upload is rejected with a helpful message |
| Passage over 300 words | Input is constrained or a clear validation error is shown |
| Large model on low-memory host | Helpful resource guidance is shown |
| Browser TTS unavailable | UI explains that the local voice is unavailable |

## Interpretation

Transcript matching and confidence are proxies for practice, not validated pronunciation metrics. Keep that distinction visible in UI labels, reports, and documentation.
