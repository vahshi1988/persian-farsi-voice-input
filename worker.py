#!/usr/bin/env python3
"""One-shot, GPU-only local dictation worker. Exits after each recording."""
import ctypes
import json
import os
import resource
import signal
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from persian_corrector import correct_text
from runtime_paths import whisper_model_spec

# Prevent an orphaned GPU worker if the Qt application is closed or killed.
ctypes.CDLL(None).prctl(1, signal.SIGTERM)
if os.getppid() == 1:
    sys.exit(1)

def reply(**fields):
    print(json.dumps(fields, ensure_ascii=False), flush=True)

def available_ram_mib():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) // 1024
    return 0

try:
    request = json.loads(sys.stdin.readline())
    audio = Path(request['path']).read_bytes()
    if len(audio) < 32000:
        raise RuntimeError('ضبط خیلی کوتاه است؛ دست‌کم یک ثانیه صحبت کنید.')
    model_name = request.get('model', 'small')
    model_path, minimum_ram = whisper_model_spec(model_name)
    if available_ram_mib() < minimum_ram:
        raise RuntimeError(f'مدل {model_name} دست‌کم {minimum_ram} MiB RAM آزاد لازم دارد؛ مدل سبک‌تر را انتخاب کنید.')
    if not (model_path / 'model.bin').is_file():
        flag = '--quality' if model_name == 'large-v3-turbo' else '--whisper'
        raise RuntimeError(f'مدل {model_name} دانلود نشده؛ scripts/download_models.py {flag} را اجرا کنید.')
    reply(status=f'بارگذاری Whisper {model_name} روی NVIDIA…')
    from faster_whisper import WhisperModel
    model = WhisperModel(str(model_path), device='cuda', compute_type='int8_float16',
                         num_workers=1, cpu_threads=2, local_files_only=True)
    reply(status=f'پردازش روی NVIDIA با {model_name} / INT8…', device='cuda', model=model_name)
    with tempfile.TemporaryDirectory(prefix='voice-input-') as folder:
        wav_path = os.path.join(folder, 'speech.wav')
        with wave.open(wav_path, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(audio[:len(audio) // 2 * 2])
        segments, _ = model.transcribe(wav_path, language=request.get('language', 'fa'),
                                       beam_size=5 if model_name == 'large-v3-turbo' else 1, vad_filter=True, condition_on_previous_text=False)
        text = ' '.join(segment.text.strip() for segment in segments).strip()
        reply(**correct_text(text, request.get("correctSpelling", True)), device='cuda', model=model_name, peakRamMiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024)
except Exception as error:
    reply(error=str(error))
