#!/usr/bin/env python3
"""Record PCM; stop after speech followed by two seconds of non-speech."""
import argparse
import ctypes
import json
import os
import selectors
import signal
import subprocess
import sys
from pathlib import Path

stopping = False

def stop(*_):
    global stopping
    stopping = True

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
ctypes.CDLL(None).prctl(1, signal.SIGTERM)
if os.getppid() == 1:
    sys.exit(1)

def emit(event):
    print(json.dumps({'event': event}), flush=True)

class SpeechEnd:
    def __init__(self):
        self.frames = self.voice_frames = self.silence_frames = 0
        self.started = False

    def feed(self, probability):
        self.frames += 1
        # Hysteresis avoids treating weak trailing syllables as silence.
        voice = probability >= (0.35 if self.started else 0.5)
        if voice:
            self.voice_frames += 1
            self.silence_frames = 0
            if self.voice_frames >= 7:  # >=224 ms of speech
                self.started = True
        else:
            if not self.started:
                self.voice_frames = 0
            self.silence_frames += 1
        if self.started and self.silence_frames >= 63:  # 2.016 seconds
            return 'speech-ended'
        if not self.started and self.frames >= 313:  # 10 seconds
            return 'no-speech'
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--input-pcm', help='Offline diagnostic input instead of microphone')
    args = parser.parse_args()
    import numpy as np
    import onnxruntime as ort
    model_path = Path(np.__file__).parent.parent / 'faster_whisper/assets/silero_vad_v6.onnx'
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    options.enable_cpu_mem_arena = False
    session = ort.InferenceSession(str(model_path), options, providers=['CPUExecutionProvider'])
    h = np.zeros((1, 1, 128), dtype=np.float32)
    c = h.copy()
    context = np.zeros((1, 64), dtype=np.float32)
    detector = SpeechEnd()
    process = None
    selector = selectors.DefaultSelector()
    result = None
    pending = b''
    try:
        if args.input_pcm:
            stream = open(args.input_pcm, 'rb')
        else:
            def child_setup():
                ctypes.CDLL(None).prctl(1, signal.SIGTERM)
            process = subprocess.Popen(['parec', '--raw', '--format=s16le', '--rate=16000',
                                        '--channels=1', '--latency-msec=50'],
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                       preexec_fn=child_setup)
            stream = process.stdout
            selector.register(stream, selectors.EVENT_READ)
        with open(args.output, 'wb') as output:
            emit('ready')
            while not stopping:
                if process and not selector.select(timeout=0.1):
                    if process.poll() is not None:
                        raise RuntimeError('ارتباط میکروفون قطع شد.')
                    continue
                chunk = stream.read1(1024)
                if not chunk:
                    if args.input_pcm:
                        break
                    raise RuntimeError('میکروفون صدایی ارسال نکرد.')
                output.write(chunk)
                pending += chunk
                while len(pending) >= 1024:
                    frame = np.frombuffer(pending[:1024], dtype='<i2').astype(np.float32) / 32768.0
                    pending = pending[1024:]
                    inputs = np.concatenate((context, frame.reshape(1, -1)), axis=1)
                    probability, h, c = session.run(None, {'input': inputs, 'h': h, 'c': c})
                    context = frame[-64:].reshape(1, -1)
                    result = detector.feed(float(probability.reshape(-1)[0]))
                    if result:
                        break
                if result:
                    break
            output.flush()
        if result:
            emit(result)
        if result == 'no-speech':
            print('گفتاری تشخیص داده نشد؛ ضبط لغو شد.', file=sys.stderr)
            return 2
        return 0
    finally:
        selector.close()
        if process:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if 'stream' in locals():
            stream.close()

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
