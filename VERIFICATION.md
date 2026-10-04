# Verification on this machine

- Qt6/C++ Release build succeeded with `cmake --build build -j1`.
- KDE keyboard portal returned keyboard permission and the app reported `keyboardReady: true`.
- Global shortcut registration returned `shortcutsReady: true`; invoking the registered KDE toggle action changed recording to true; invoking cancel changed it back to false. Physical shortcut keypress was not independently observed.
- Real Wayland keyboard injection pasted `سلام، آزمایش ورودی صوتی فارسی` into the dedicated Qt QLineEdit test window; the target logged `INSERTED:` with the same text.
- Microphone capture with parec at 16 kHz, mono, signed 16-bit, latency 50ms produced 45,600 samples and nonzero peak amplitude (28,240).
- Smaller GPU-only worker processed a synthetic Persian speech sample and returned `device: cuda`, `model: small`, `peakRamMiB: 711`, then exited with code 0. Synthetic-speech transcription had errors; this is a pipeline test, not a human-speech accuracy measurement.
- Peak total GPU memory during the standalone worker test: 949 MiB. Idle GPU baseline before the test: 498 MiB. These are snapshots for this sample and are not maximum-resource guarantees.
- Legacy mic.py and dictation-toggle.py processes were stopped. RAM available rose from about 800 MiB to 1.7 GiB. Swap remained heavily occupied by the desktop workload.
- The finished project was launched in Qt Creator. No other desktop application was closed to free memory.

## Automatic speech end

- Silero VAD v6 already installed with faster-whisper is used directly through ONNX Runtime with one CPU thread. Whisper remains GPU-only.
- State checks passed: waiting for speech, a short pause, resumed speech, 2.016 seconds of silence after speech, and 10 seconds without speech.
- Actual VAD model test on synthetic Persian audio followed by silence emitted `speech-ended` and exited 0. Silence-only input emitted `no-speech` and exited 2.
- Qt Release build passed after integrating automatic recording completion.

## FastConformer CUDA

- Model: PersianML/Shenava-Koochik-v1.0-sherpa-onnx, fine-tuned FastConformer CTC export. This is not the unchanged NVIDIA checkpoint.
- Runtime: sherpa-onnx 1.13.8+cuda12.cudnn9.onnxruntime1.28.2 in a separate project venv. Added only missing cuRAND and CUDA Runtime; existing cuBLAS/cuDNN are reused.
- GPU execution confirmed by an nvidia-smi allocation owned by the worker PID; CPU fallback rejected.
- Public sample: https://huggingface.co/datasets/PartAI/PSRB/blob/main/Files/audio_1.wav ; reference in Labels.csv has the transcript in the audio_duration column due to shifted headers.
- Same 11.877-second, resampled 16kHz mono audio processed by both models. Space/punctuation-insensitive character error: FastConformer 14.2%, Whisper small 29.2%. One noisy multi-speaker sample only.
- FastConformer cold load plus inference 2.76 seconds; peak RSS 1013 MiB, GPU allocation after load 596 MiB (not peak).
- Qt Release build passed and FastConformer is now the default.
- Final end-to-end Qt test passed: TranscribeTestFile sent the human PCM through the new worker; GetStatus reported `device: cuda`, `model: fastconformer-fa-shenava-ctc`, and the dedicated QLineEdit target logged `INSERTED:` with the returned text. Cold load/inference in that run: 2.09 seconds; peak RSS 1016 MiB. The temporary target window was closed afterward.

## Conservative Persian dictionary correction

- Qt Release build passed; both ASR workers pass recognized text through the same standard-library/ctypes Hunspell corrector before returning JSON.
- Seven tests passed: actual Persian spelling corrections, preservation of names/valid colloquial words/identifiers/URLs/paths/code, disabling correction, personal protected words and explicit rules, ambiguous suggestions, contextual disambiguation, and dictionary failure fallback.
- Real application status after speech showed `device: cuda`, `originalText`, `text`, and `corrections`; raw text was preserved and the active Qt field received output. The requested benchmark diagnostic call was declined while the application was busy; this was not counted as a benchmark run.
- Automatic correction uses only one-letter confusions plus an allowlist/collocation gate. It does not provide full sentence semantics, and protecting every unknown proper name is not guaranteed. Users can explicitly protect terminology.
