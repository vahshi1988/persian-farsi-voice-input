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

## Portable publication and model selection

- Removed fixed home-directory desktop launchers; installer generates actual checkout paths and validates under temporary XDG directories.
- Added project-local Python setup, matching-ABI CUDA wheel selection, optional model download, MIT application-code license, and third-party attribution.
- Added XDG personal-dictionary storage and non-overwriting migration; private checkout dictionaries are ignored and removed from Git tracking.
- Eleven isolated dictionary/runtime/model-choice tests pass; Python compile checks and bash syntax checks pass; Qt Release build passes.
- FastConformer remains the default. The menu now offers Whisper small and large-v3-turbo, with explicit downloads and 1100/3000 MiB available-RAM gates respectively. Larger-model inference is not rerun on the low-RAM laptop; full fresh Python/CUDA installation is documented but was not repeated on this already-configured machine.

## Experimental local Persian/English mode

- Added persistent Persian/mixed language selection and optional Qwen3-ASR 0.6B INT8 using the existing sherpa-onnx CUDA environment. Whisper mixed mode uses multilingual transcription and never the translation task.
- The 853,425,113-byte model archive was downloaded on srv70, copied to the user's private Google Drive folder, downloaded to the laptop in parallel, and verified against SHA256 before extraction. No microphone recordings or recognized text were uploaded.
- Twenty-two tests pass, covering the audio bridge, language modes, preservation of Latin identifiers, model selection, missing weights, insufficient RAM, overlong Qwen recordings, and rejected execution without a verified CUDA allocation. Qt Release build passes.
- On two public samples from Perle-ai/ASR_Code_Switch, Qwen 0.6B INT8 and Whisper small both made substantial errors. Automatic Qwen language identification could select unrelated languages. Persian language hints and vocabulary cues did not resolve mixed-speech errors and could corrupt English-only output. See `BILINGUAL_TEST.json`; this small test is not a general accuracy evaluation.
- Qwen correctly transcribed one synthetic English-only sample containing Python, Linux and GitHub. In the Qt end-to-end test, the dedicated QLineEdit confirmed focus and logged `INSERTED: I use Python and Linux. Save the project to GitHub.`. The worker returned `device: cuda`, 700 MiB GPU allocation, 2010 MiB peak RSS and 8.96 seconds including model loading. This verifies local recognition and insertion, not human-speech accuracy or the physical recording shortcut.
- Qwen INT8 may execute some ONNX operators on CPU. A worker-owned NVIDIA allocation was observed, but this does not establish that every operator executes on CUDA.
- The test target was closed, Persian mode restored, and the updated application left running with FastConformer preferred. Qwen/mixed mode is labelled experimental, and the existing Persian default is retained because code-switching reliability was not demonstrated.

- Qwen recordings are capped at 30 seconds to leave room for decoded text within the bounded 1024-token cache; other engines retain the 60-second limit.
