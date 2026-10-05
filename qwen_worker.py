#!/usr/bin/env python3
"""One-shot local Qwen3-ASR INT8 worker using the existing sherpa-onnx CUDA runtime."""
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
from runtime_paths import qwen_model_spec
from worker import available_ram_mib


def reply(**fields):
    print(json.dumps(fields, ensure_ascii=False), flush=True)


def cuda_allocation_mib():
    output = subprocess.check_output(
        ['nvidia-smi', '--query-compute-apps=pid,used_gpu_memory', '--format=csv,noheader,nounits'], text=True)
    for line in output.splitlines():
        fields = [part.strip() for part in line.split(',')]
        if fields[0] == str(os.getpid()):
            return int(fields[1])
    raise RuntimeError('اجرای NVIDIA تأیید نشد؛ برگشت به CPU مجاز نیست.')


def transcribe_request(request):
    mode = request.get('languageMode', 'mixed')
    if mode not in ('fa', 'mixed'):
        raise ValueError('حالت زبان گفتار نامعتبر است.')
    audio_path = Path(request['path'])
    size = audio_path.stat().st_size
    if size < 32000:
        raise RuntimeError('ضبط خیلی کوتاه است؛ دست‌کم یک ثانیه صحبت کنید.')
    # Keep audio plus output tokens inside the bounded 1024-token KV cache.
    if size > 30 * 32000:
        raise RuntimeError('مدل Qwen برای هر نوبت ضبط حداکثر ۳۰ ثانیه را می‌پذیرد.')
    name = request.get('model', 'qwen3-asr-0.6b')
    model_path, minimum_ram = qwen_model_spec(name)
    if available_ram_mib() < minimum_ram:
        raise RuntimeError(f'مدل Qwen دست‌کم {minimum_ram} MiB RAM آزاد لازم دارد؛ چند برنامه را ببندید.')
    required = ['conv_frontend.onnx', 'encoder.int8.onnx', 'decoder.int8.onnx',
                'tokenizer/vocab.json', 'tokenizer/merges.txt', 'tokenizer/tokenizer_config.json']
    if any(not (model_path / file).is_file() for file in required):
        raise RuntimeError('مدل Qwen INT8 دانلود نشده؛ scripts/download_models.py --qwen را اجرا کنید.')

    reply(status='بارگذاری Qwen3-ASR INT8 روی NVIDIA…')
    import numpy as np
    import sherpa_onnx
    if not hasattr(sherpa_onnx.OfflineRecognizer, 'from_qwen3_asr'):
        raise RuntimeError('نسخهٔ sherpa-onnx از Qwen پشتیبانی نمی‌کند؛ scripts/setup.sh را اجرا کنید.')
    start = time.monotonic()
    recognizer = sherpa_onnx.OfflineRecognizer.from_qwen3_asr(
        conv_frontend=str(model_path / 'conv_frontend.onnx'),
        encoder=str(model_path / 'encoder.int8.onnx'), decoder=str(model_path / 'decoder.int8.onnx'),
        tokenizer=str(model_path / 'tokenizer'), num_threads=2, provider='cuda',
        max_total_len=1024, max_new_tokens=512, temperature=1e-6, seed=42)
    # Mixed speech uses automatic language identification. A Persian hint in
    # mixed mode can corrupt English-only speech, so it is reserved for fa mode.
    gpu_memory = cuda_allocation_mib()
    samples = np.fromfile(audio_path, dtype='<i2').astype(np.float32) / 32768.0
    stream = recognizer.create_stream()
    if mode == 'fa':
        stream.set_option('language', 'Persian')
    stream.accept_waveform(16000, samples)
    reply(status='تشخیص گفتار فارسی و انگلیسی…', device='cuda', model=name)
    recognizer.decode_stream(stream)
    return dict(correct_text(stream.result.text.strip(), request.get('correctSpelling', True)),
                device='cuda', model=name, languageMode=mode,
                seconds=round(time.monotonic() - start, 2), gpuMemoryMiB=gpu_memory,
                peakRamMiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024)


def main():
    ctypes.CDLL(None).prctl(1, signal.SIGTERM)
    if os.getppid() == 1:
        return 1
    try:
        reply(**transcribe_request(json.loads(sys.stdin.readline())))
        return 0
    except Exception as error:
        reply(error=str(error))
        return 1


if __name__ == '__main__':
    sys.exit(main())
