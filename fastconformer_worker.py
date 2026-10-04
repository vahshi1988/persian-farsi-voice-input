#!/usr/bin/env python3
"""One-shot CUDA FastConformer CTC worker, compatible with the Qt JSON protocol."""
import ctypes
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path
from persian_corrector import correct_text
from runtime_paths import model_root

ctypes.CDLL(None).prctl(1, signal.SIGTERM)
if os.getppid() == 1:
    sys.exit(1)

def reply(**fields):
    print(json.dumps(fields, ensure_ascii=False), flush=True)

try:
    request = json.loads(sys.stdin.readline())
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:') and int(line.split()[1]) < 1500 * 1024:
            raise RuntimeError('RAM آزاد کمتر از ۱٫۵ گیگابایت است؛ چند برنامه را ببندید.')
    audio_path = Path(request['path'])
    import numpy as np
    import sherpa_onnx
    model_dir = model_root() / 'fastconformer-fa'
    if not (model_dir / 'model.onnx').is_file():
        raise RuntimeError('مدل FastConformer فارسی هنوز دانلود نشده است.')
    reply(status='بارگذاری FastConformer فارسی روی NVIDIA…')
    start = time.monotonic()
    recognizer = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
        model=str(model_dir / 'model.onnx'), tokens=str(model_dir / 'tokens.txt'),
        num_threads=2, provider='cuda', debug=False,
    )
    # Reject a silent CPU fallback: this process must own a CUDA allocation.
    gpu_info = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_gpu_memory',
                                        '--format=csv,noheader,nounits'], text=True)
    gpu_memory = None
    for gpu_line in gpu_info.splitlines():
        fields = [field.strip() for field in gpu_line.split(',')]
        if fields[0] == str(os.getpid()):
            gpu_memory = int(fields[1])
    if gpu_memory is None:
        raise RuntimeError('اجرای NVIDIA تأیید نشد؛ برگشت به CPU مجاز نیست.')
    samples = np.fromfile(audio_path, dtype='<i2').astype(np.float32) / 32768.0
    if len(samples) < 16000:
        raise RuntimeError('ضبط کوتاه است؛ دست‌کم یک ثانیه صحبت کنید.')
    stream = recognizer.create_stream()
    stream.accept_waveform(16000, samples)
    recognizer.decode_stream(stream)
    reply(**correct_text(stream.result.text.strip(), request.get("correctSpelling", True)), device='cuda', model='fastconformer-fa-shenava-ctc',
          seconds=round(time.monotonic()-start, 2), gpuMemoryMiB=gpu_memory,
          peakRamMiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024)
except Exception as error:
    reply(error=str(error))
    sys.exit(1)
