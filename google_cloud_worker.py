#!/usr/bin/env python3
"""Google Cloud Speech-to-Text worker, compatible with the Qt JSON protocol."""
import ctypes
import json
import os
import signal
import sys
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

    credential_path = request.get('credentialPath') or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not credential_path or not Path(credential_path).is_file():
        raise RuntimeError('فایل اعتبارنامه Google Cloud تنظیم نشده یا وجود ندارد.')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

    language_mode = request.get('languageMode', 'fa')
    language_code = 'fa-IR' if language_mode == 'fa' else 'fa-IR'
    alternative_languages = ['en-US'] if language_mode == 'mixed' else []

    reply(status='ارسال صدا به Google Cloud Speech-to-Text…')
    from google.cloud import speech

    client = speech.SpeechClient()
    config_kwargs = dict(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code,
        enable_automatic_punctuation=True,
    )
    if alternative_languages:
        config_kwargs['alternative_language_codes'] = alternative_languages
    config = speech.RecognitionConfig(**config_kwargs)

    if len(audio_data) > 960000:
        # Long audio (>30s): use long_running_recognize
        reply(status='صدای طولانی؛ پردازش ابری ممکن است چند ثانیه طول بکشد…')
        operation = client.long_running_recognize(
            config=config,
            audio=speech.RecognitionAudio(content=audio_data),
        )
        response = operation.result(timeout=120)
    else:
        response = client.recognize(
            config=config,
            audio=speech.RecognitionAudio(content=audio_data),
        )

    parts = []
    detected_language = language_code
    for result in response.results:
        if result.alternatives:
            parts.append(result.alternatives[0].transcript)
            if hasattr(result, 'language_code') and result.language_code:
                detected_language = result.language_code
    text = ' '.join(parts).strip()

    if not text:
        raise RuntimeError('گفتاری تشخیص داده نشد.')

    reply(**correct_text(text, request.get('correctSpelling', True)),
          device='cloud', model='google-cloud-stt',
          languageMode=language_mode, detectedLanguage=detected_language)

except Exception as error:
    reply(error=str(error))
    sys.exit(1)
