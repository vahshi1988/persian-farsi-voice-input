#!/usr/bin/env python3
"""Google Web Speech API (free, no credentials) worker, compatible with the Qt JSON protocol."""
import ctypes
import json
import os
import signal
import sys
import wave
import tempfile
from pathlib import Path
from persian_corrector import correct_text

ctypes.CDLL(None).prctl(1, signal.SIGTERM)
if os.getppid() == 1:
    sys.exit(1)

def reply(**fields):
    print(json.dumps(fields, ensure_ascii=False), flush=True)

try:
    request = json.loads(sys.stdin.readline())
    audio_path = Path(request['path'])
    audio_data = audio_path.read_bytes()
    if len(audio_data) < 32000:
        raise RuntimeError('ضبط خیلی کوتاه است؛ دست‌کم یک ثانیه صحبت کنید.')

    language_mode = request.get('languageMode', 'fa')
    language_code = 'fa-IR' if language_mode == 'fa' else 'fa-IR'

    reply(status='ارسال صدا به Google Web Speech API (رایگان)…')
    import speech_recognition as sr

    with tempfile.TemporaryDirectory(prefix='voice-input-') as folder:
        wav_path = os.path.join(folder, 'speech.wav')
        with wave.open(wav_path, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(audio_data[:len(audio_data) // 2 * 2])

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language=language_code)

    if not text:
        raise RuntimeError('گفتاری تشخیص داده نشد.')

    reply(**correct_text(text, request.get('correctSpelling', True)),
          device='cloud', model='google-free-web-speech',
          languageMode=language_mode)

except sr.UnknownValueError:
    reply(error='گفتاری تشخیص داده نشد.')
    sys.exit(1)
except sr.RequestError as e:
    reply(error=f'خطای ارتباط با Google: {e}')
    sys.exit(1)
except Exception as error:
    reply(error=str(error))
    sys.exit(1)
