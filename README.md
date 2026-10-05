# Persian/Farsi Voice Input

الفاظ رکیک به هیچ عنوان در این پروژه بلاک نشده‌اند و بلاک نمی‌شوند؛ هیچ فیلتر یا سانسوری برای آن‌ها اعمال نمی‌شود.

Profanity is not blocked in this project and will not be blocked; no profanity filtering or censorship is applied.

## نصب روی دستگاه دیگر / Install on another machine

هدف: **Linux x86_64، KDE Plasma/Wayland، Python 3.10+، کارت NVIDIA با درایور سازگار CUDA 12**. برنامه هنوز برای Windows/macOS یا دسکتاپ‌های دیگر تست نشده است. کد MIT است؛ مدل‌ها و دیکشنری‌های خارجی مجوزهای خودشان را دارند و در مخزن بازنشر نمی‌شوند.

Ubuntu/Debian prerequisites (install the NVIDIA driver through your distribution separately):

```bash
sudo apt install cmake g++ qt6-base-dev python3-venv pulseaudio-utils hunspell-fa libhunspell-1.7-0
nvidia-smi
```

در Plasma، `xdg-desktop-portal-kde`، سرویس میانبرهای KDE و Klipper باید در نشست کاربر موجود باشند. بسته‌های Python و مدل‌ها چند گیگابایت فضای دیسک/دانلود می‌خواهند؛ نصب‌کننده درایور NVIDIA و بستهٔ سیستمی نصب نمی‌کند.

```bash
git clone https://github.com/vahshi1988/persian-farsi-voice-input.git
cd persian-farsi-voice-input
./scripts/setup.sh                 # Python .venv, CUDA runtime, FastConformer model, Qt build
# ./scripts/setup.sh --whisper     # optional Whisper small fallback too
./build/voice-input --setup
python3 scripts/install_desktop.py --autostart
```

Grant the KDE keyboard permission yourself. The app transcribes locally; first-time setup downloads public models and packages. The setup command selects the CUDA wheel matching your Python ABI through the official sherpa-onnx wheel index; if no compatible wheel exists, installation fails instead of compiling CUDA or changing your driver. Launchers point to this checkout, so regenerate them if you move it. They start after **Plasma login**, not before graphical login.

### مسیرهای قابل تنظیم / Runtime overrides

- `.venv/bin/python` is the default interpreter for capture and ASR.
- `VOICE_INPUT_PYTHON`: capture/Whisper interpreter override.
- `VOICE_INPUT_FAST_PYTHON`: FastConformer/Qwen sherpa-onnx interpreter override.
- `VOICE_INPUT_MODEL_DIR`: models directory (default: `models` next to this checkout).
- `VOICE_INPUT_DICTIONARY`: personal dictionary file override.
- Personal words normally live in `$XDG_CONFIG_HOME/voice-input/personal_dictionary.json` (default `~/.config/voice-input/…`); they are never committed. `personal_dictionary.example.json` shows the format. The desktop installer migrates an existing checkout dictionary only when the destination does not exist.
- Existing installations may still use `fastconformer-venv` and the earlier Whisper environment; these are compatibility fallbacks, not prerequisites for a new installation.

Tests and model download can also be run independently:

```bash
.venv/bin/python -m unittest discover
.venv/bin/python scripts/download_models.py --whisper
```

Third-party sources/licenses: [FastConformer/Shenava model](https://huggingface.co/PersianML/Shenava-Koochik-v1.0-sherpa-onnx), [optional Whisper model](https://huggingface.co/Systran/faster-whisper-small), [Qwen3-ASR model](https://huggingface.co/Qwen/Qwen3-ASR-0.6B), [faster-whisper/Silero integration](https://github.com/SYSTRAN/faster-whisper), [sherpa-onnx CUDA installation](https://k2-fsa.github.io/sherpa/onnx/python/install.html). Review their licenses before redistributing models or binaries. The project MIT license covers this repository's application code.

---

# ورودی صوتی فارسی برای KDE/Wayland

[فارسی](#ورودی-صوتی-فارسی-برای-kdewayland) | [English](#persian-voice-input-for-kdewayland)

برنامهٔ Qt 6 / C++ با پروژهٔ CMake قابل بازکردن در Qt Creator.

## اجرا

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j1
./build/voice-input --setup
```

در KDE مجوز کنترل **صفحه‌کلید** را تأیید کنید. این مجوز برای فرستادن میانبر چسباندن متن لازم است؛ برنامه تصویری از صفحه نمی‌گیرد. پنجره را ببندید تا برنامه کنار ساعت بماند.

- داخل کادر مقصد کلیک کنید؛ `Ctrl+Alt+W` ضبط را شروع می‌کند.
- پس از گفتار، حدود دو ثانیه سکوت باعث پایان خودکار ضبط و درج متن در کادر فعال می‌شود. همان میانبر برای پایان دستی نیز کار می‌کند.
- مکث کوتاه ضبط را متوقف نمی‌کند؛ ده ثانیه بدون شروع گفتار، ضبط را لغو می‌کند. تشخیص گفتار با مدل کوچک محلی Silero VAD است؛ این مدل هنگام ضبط روی CPU کار می‌کند و Whisper برای تبدیل متن همچنان فقط روی NVIDIA اجرا می‌شود.
- تا پایان پردازش کادر مقصد را عوض نکنید؛ متن به کادری می‌رود که هنگام ارسال فعال است.
- `Ctrl+Alt+Escape` ضبط یا پردازش را لغو می‌کند.
- در ترمینال حالت `Ctrl+Shift+V` را از منوی آیکن کنار ساعت فعال کنید.
- بستن پنجره برنامه را متوقف نمی‌کند؛ برای پایان از منوی کنار ساعت «خروج» را بزنید.

این روش با کادرهای متنی که Paste را می‌پذیرند کار می‌کند؛ اجرای تمام برنامه‌های لینوکس به‌صورت جداگانه بررسی نشده است. متن در Clipboard قرار می‌گیرد و ممکن است Klipper آن را در تاریخچه نگه دارد. آخرین متن فقط تا زمان خروج در برنامه باقی می‌ماند؛ فایل صدای موقت بعد از پردازش حذف می‌شود.

## حافظه و GPU

موتور پیش‌فرض اکنون **FastConformer فارسی / Shenava Koochik CTC** است: نسخهٔ ONNX بهبود‌یافته از خانوادهٔ FastConformer NVIDIA، نه وزن‌های دست‌نخوردهٔ مدل اصلی. منبع مدل: https://huggingface.co/PersianML/Shenava-Koochik-v1.0-sherpa-onnx . مدل در `models/fastconformer-fa` و محیط جدا در `fastconformer-venv` است. اجرای CUDA 12 / cuDNN 9 با sherpa-onnx انجام می‌شود. وجود تخصیص GPU متعلق به worker با nvidia-smi کنترل می‌شود؛ برگشت خاموش به CPU پذیرفته نمی‌شود. worker بعد از هر پردازش خارج می‌شود تا حافظه آزاد شود.

در منوی کنار ساعت، «انتخاب موتور گفتار» سه حالت FastConformer فارسی، Whisper small و Whisper large-v3-turbo دارد. انتخاب برای ضبط بعدی ذخیره می‌شود. میانبر و تشخیص پایان گفتار با Silero تغییر نکرده‌اند. Silero روی CPU، ولی تبدیل متن روی NVIDIA اجرا می‌شود.

آزمایش روی **یک نمونهٔ** محاوره‌ای پرنویز از PSRB، خطای کاراکتر پس از حذف فاصله و نشانه‌گذاری: FastConformer حدود ۱۴٫۲٪ و Whisper small حدود ۲۹٫۲٪. این نتیجه ارزیابی عمومی یا تضمین دقت برای صدای شما نیست. FastConformer نمونهٔ حدود ۱۲ ثانیه‌ای را با بارگذاری مدل در ۲٫۷۶ ثانیه پردازش کرد؛ اوج RSS حدود ۱۰۱۳ MiB و تخصیص GPU هنگام بارگذاری ۵۹۶ MiB بود. عدد GPU اندازه‌گیری اوج مصرف نیست. جزئیات در `FASTCONFORMER_TEST.json` قرار دارد.

اگر RAM قابل‌استفاده کمتر از ۱۵۰۰ MiB برای FastConformer یا ۱۱۰۰ MiB برای Whisper باشد، مدل بارگذاری نمی‌شود و برنامه درخواست بستن چند برنامه را نشان می‌دهد. این آستانه تضمین نمی‌کند که سایر برنامه‌ها همزمان حافظه مصرف نکنند. حداکثر ضبط ۶۰ ثانیه و زمان پردازش ۱۲۰ ثانیه است؛ برای Qwen حداکثر ضبط ۳۰ ثانیه و مهلت پردازش ۲۴۰ ثانیه است.

وابستگی‌های همین دستگاه: Qt6 Widgets/DBus/Network، KDE kglobalaccel و Klipper، XDG RemoteDesktop portal، `parec`، محیط Python موجود در `~/.local/share/whisper/venv` و کتابخانه‌های NVIDIA آن محیط.

میانبر قدیمی `whisper-dictation.desktop / _launch` به همین برنامه منتقل شده؛ میانبر متعلق به سایر برنامه‌ها بازنویسی نمی‌شود. برای برگشت، در تنظیمات Shortcuts KDE میانبر «ورودی صوتی» را پاک کنید و Ctrl+Alt+W را به Whisper Dictation بدهید.

## تشخیص و آزمایش

```bash
qdbus6 local.voiceinput.Controller /VoiceInput local.voiceinput.Controller.GetStatus
./build/voice-input --test-target --auto-exit
```

`GetStatus` وضعیت مجوز، میانبر، ضبط و مشخصات آخرین پردازش را نشان می‌دهد. برای آزمایش درج در کادر آزمایشی از `TestPaste` استفاده می‌شود؛ این فرمان سه ثانیه فرصت انتخاب کادر مقصد می‌دهد:

```bash
qdbus6 local.voiceinput.Controller /VoiceInput local.voiceinput.Controller.TestPaste 'سلام، آزمایش فارسی'
```

مراجع پیاده‌سازی:
- https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html
- https://github.com/SYSTRAN/faster-whisper

## اصلاح واژه‌های فارسی

بعد از تشخیص گفتار و پیش از درج، دیکشنری نصب‌شدهٔ Hunspell (`/usr/share/hunspell/fa_IR.*`) واژه‌ها را بررسی می‌کند. واژه‌های معتبر دست‌نخورده می‌مانند. تنها یک حرف از گروه‌های محدودِ مشابه تغییر می‌کند، آن هم وقتی جایگزین دیکشنری یکتا و در فهرست واژه‌های رایج باشد، یا ترکیب واژهٔ قبلی یک جایگزین مشخص بدهد. این بخش مدل زبانی و درک معنای کامل جمله نیست؛ واژهٔ اشتباهِ دارای معنی و بیشتر خطاهای حذف/شکستن کلمه را اصلاح نمی‌کند. فهرست رایج محدود است تا اسم‌ها و اصطلاحات کمتر آسیب ببینند؛ حفاظت از هر اسم ناشناخته تضمین نمی‌شود.

در منوی کنار ساعت «اصلاح محافظه‌کارانهٔ واژه‌ها» را می‌توان خاموش کرد. پنجرهٔ برنامه تب‌های «متن اصلاح‌شده» و «متن خام» و فهرست تغییرها دارد؛ هر دو متن قابل کپی هستند. اگر دیکشنری یا فایل تنظیمات خراب باشد، متن خام حفظ و هشدار نمایش داده می‌شود.

از «واژه‌ها و اصلاحات شخصی» استفاده کنید:

- اسم‌ها و اصطلاحات محافظت‌شده: هر واژه یک خط؛ این واژه‌ها حتی با وجود قانون اصلاح شخصی عوض نمی‌شوند.
- اصلاح دلخواه: هر خط مانند `نخشه=نقشه`؛ سمت چپ یک واژه و سمت راست جایگزین دلخواه است. این قانون صریح می‌تواند واژهٔ معتبر را هم عوض کند.
- تنظیمات در `~/.config/voice-input/personal_dictionary.json` ذخیره می‌شوند و از ضبط بعدی اعمال خواهند شد.

نشانی‌های اینترنتی، مسیرها، ایمیل، متن میان backtick و شناسه‌های چسبیده به حروف لاتین/عدد اصلاح نمی‌شوند. مرحلهٔ اصلاح به اینترنت یا نصب مدل جدید نیاز ندارد و از طریق هر دو موتور FastConformer و Whisper اجرا می‌شود.

---

<a id="persian-voice-input-for-kdewayland"></a>
# Persian Voice Input for KDE/Wayland

[فارسی](#ورودی-صوتی-فارسی-برای-kdewayland) | [English](#persian-voice-input-for-kdewayland)

A Qt 6 / C++ application with a CMake project that can be opened in Qt Creator.

## Build and run

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j1
./build/voice-input --setup
```

In KDE, grant permission to control the **keyboard**. This permission is needed to send the paste shortcut; the application does not capture screenshots. Close the window to keep the application running in the system tray.

- Click the destination text field and press `Ctrl+Alt+W` to start recording.
- After you finish speaking, about two seconds of silence automatically ends the recording and inserts the text into the active field. The same shortcut can also stop recording manually.
- Short pauses do not stop recording. Ten seconds without detected speech cancels it. Speech activity is detected locally with the small Silero VAD model, which runs on the CPU during recording. Whisper transcription still runs only on NVIDIA GPUs.
- Keep the destination field focused until processing finishes; the text is sent to whichever field is active when it is submitted.
- Press `Ctrl+Alt+Escape` to cancel recording or processing.
- In terminal mode, enable `Ctrl+Shift+V` from the system-tray menu.
- Closing the window does not stop the application. To exit, use **Quit** from the system-tray menu.

This works with text fields that accept paste; not every Linux application has been tested individually. Text is placed on the clipboard, and Klipper may retain it in its history. The application keeps the latest text only until it exits, and removes the temporary audio file after processing.

## Speech recognition, memory, and GPU

The default engine is **Persian FastConformer / Shenava Koochik CTC**: an improved ONNX version from the NVIDIA FastConformer family, not the original model's unmodified weights. Model source: https://huggingface.co/PersianML/Shenava-Koochik-v1.0-sherpa-onnx . The model is expected in `models/fastconformer-fa`, with Python dependencies in `.venv` (the existing `fastconformer-venv` remains a compatibility fallback). Inference uses sherpa-onnx with CUDA 12 / cuDNN 9. The application checks the worker's GPU allocation with `nvidia-smi`; silently falling back to CPU is not accepted. The worker exits after each transcription to release memory.

The tray **Speech engine selection** submenu provides FastConformer, Whisper small, and Whisper large-v3-turbo. The selection is saved for the next recording. The shortcut and Silero end-of-speech detection remain unchanged. Silero runs on the CPU, while transcription runs on NVIDIA.

On **one** noisy conversational PSRB sample, character error rate after removing spaces and punctuation was about 14.2% for FastConformer and 29.2% for Whisper small. This is not a general evaluation or a guarantee of accuracy for your audio. FastConformer processed an approximately 12-second sample in 2.76 seconds, including model loading; peak RSS was about 1013 MiB, and GPU allocation during loading was 596 MiB. The GPU figure is not a peak-usage measurement. See `FASTCONFORMER_TEST.json` for details.

If available RAM is below 1500 MiB for FastConformer or 1100 MiB for Whisper, the model is not loaded and the application asks you to close some applications. These thresholds do not guarantee that other applications will not consume memory concurrently. Maximum recording duration is 60 seconds, or 30 seconds for Qwen to stay within its bounded token cache. The processing timeout is 120 seconds, or 240 seconds for Qwen.

Dependencies for the original machine include Qt6 Widgets/DBus/Network, KDE kglobalaccel and Klipper, the XDG RemoteDesktop portal, `parec`, the Python environment at `~/.local/share/whisper/venv`, and that environment's NVIDIA libraries.

The old `whisper-dictation.desktop / _launch` shortcut was transferred to this application; shortcuts belonging to other applications are not overwritten. To revert, remove the **Voice Input** shortcut in KDE's Shortcuts settings and assign `Ctrl+Alt+W` to Whisper Dictation.

## Status and testing

```bash
qdbus6 local.voiceinput.Controller /VoiceInput local.voiceinput.Controller.GetStatus
./build/voice-input --test-target --auto-exit
```

`GetStatus` reports permission, shortcut, recording state, and details of the latest transcription. To test insertion into a text field, use `TestPaste`; the command gives you three seconds to select the destination field:

```bash
qdbus6 local.voiceinput.Controller /VoiceInput local.voiceinput.Controller.TestPaste 'Hello, Persian test'
```

Implementation references:
- https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html
- https://github.com/SYSTRAN/faster-whisper

## Persian word correction

After speech recognition and before insertion, the installed Hunspell dictionary (`/usr/share/hunspell/fa_IR.*`) checks words. Valid words are left unchanged. At most one character from a limited set of similar characters is changed, and only when the dictionary has a unique alternative that is on the common-word list, or the preceding word makes one alternative unambiguous. This is not a language model and does not understand the meaning of entire sentences; it cannot correct a wrong-but-valid word or most word deletion and word-splitting errors. The common-word list is intentionally limited to reduce changes to names and terminology, but it cannot protect every unknown name.

**Conservative word correction** can be disabled in the system-tray menu. The application window has **Corrected text** and **Raw text** tabs, as well as a list of changes; both texts can be copied. If the dictionary or settings file is invalid, the raw text is preserved and a warning is shown.

Use **Personal words and corrections** to customize behavior:

- **Protected names and terms:** enter one word per line. These words are never changed, even if a personal correction rule matches.
- **Custom corrections:** enter one rule per line, such as `نخشه=نقشه`; the left side is the word to replace and the right side is its replacement. An explicit rule can also replace a valid word.
- Settings are saved in `~/.config/voice-input/personal_dictionary.json` and take effect on the next recording.

URLs, paths, email addresses, text inside backticks, and identifiers adjacent to Latin letters or digits are not corrected. Word correction works offline, requires no additional model, and is applied with both FastConformer and Whisper.


## گفتار ترکیبی فارسی و انگلیسی / Mixed Persian and English speech

از منوی کنار ساعت، **زبان گفتار → فارسی و انگلیسی (آزمایشی)** را انتخاب کنید. زبان گفتار خودکار تشخیص داده می‌شود و کار مدل `transcribe` است؛ گفتار انگلیسی به فارسی ترجمه نمی‌شود. واژه‌های لاتینِ تشخیص‌داده‌شده، مانند `Python` و `GitHub`، در مرحلهٔ اصلاح املای فارسی دست‌نخورده می‌مانند. انتخاب زبان ذخیره می‌شود.

این حالت از **Qwen3-ASR 0.6B INT8** با همان محیط CUDA مربوط به sherpa-onnx استفاده می‌کند؛ نصب PyTorch یا دانلود دوبارهٔ کتابخانه‌های CUDA لازم نیست. اگر موتور انتخابی FastConformer باشد، حالت ترکیبی Qwen را اجرا می‌کند و با برگشت به **فارسی**، FastConformer فعال می‌شود. با انتخاب یک موتور Whisper، همان موتور استفاده می‌شود. در حالت ترکیبی، Qwen زبان را خودکار تشخیص می‌دهد؛ در حالت «فارسی» راهنمای زبان Persian به آن داده می‌شود.

```bash
.venv/bin/python scripts/download_models.py --qwen
# Existing installation on the original machine:
# ./fastconformer-venv/bin/python scripts/download_models.py --qwen
```

مدل ONNX INT8 حدود ۱ گیگابایت حجم دارد و از [مدل تبدیل‌شدهٔ sherpa-onnx](https://huggingface.co/csukuangfj2/sherpa-onnx-qwen3-asr-0.6B-int8-2026-03-25) دانلود می‌شود؛ مدل اصلی [Qwen3-ASR](https://huggingface.co/Qwen/Qwen3-ASR-0.6B) با مجوز Apache 2.0 منتشر شده است. برای نصب از آرشیو تأییدشده، پوشهٔ `qwen3-asr-0.6b-onnx-int8` را داخل `models/` استخراج کنید. پردازش کاملاً محلی است؛ هیچ صدا یا متن تشخیص‌داده‌شده‌ای به سرویس ابری فرستاده نمی‌شود.

**این گزینه آزمایشی است و برای گفتار ترکیبی هنوز قابل اتکا ارزیابی نشده است.** روی دو نمونهٔ عمومی فارسی و انگلیسی، Qwen 0.6B INT8 خطاهای زیاد و تشخیص اشتباه زبان داشت؛ همان مدل یک نمونهٔ مصنوعی انگلیسی را درست نوشت. Whisper small هم روی دو نمونهٔ ترکیبی ضعیف بود. نتایج در `BILINGUAL_TEST.json` هستند؛ این آزمایش کوچک ارزیابی عمومی نیست. پیش‌فرض فارسی FastConformer حفظ شده است.

دقت واژه‌های انگلیسی میان جملهٔ فارسی، مخصوصاً با لهجه، به مدل و صدا وابسته است؛ تشخیص زبان تضمین نمی‌کند هر واژه با املای مطلوب شناسایی شود. برای اصطلاحی که همیشه با حروف فارسی نوشته می‌شود، می‌توانید در «واژه‌ها و اصلاحات شخصی» جایگزینی صریحی مثل `پایتون=Python` ثبت کنید؛ این نگاشت فقط انتخاب خود کاربر است و تبدیل عمومیِ همهٔ واژه‌های فارسی به انگلیسی انجام نمی‌شود.

Choose **Speech language → Persian and English (experimental)** from the tray. The selection persists. With FastConformer preferred, mixed mode runs **Qwen3-ASR 0.6B INT8**, while Persian mode returns to FastConformer. A selected Whisper model runs directly. Qwen identifies languages automatically in mixed mode and receives a Persian language hint in Persian mode. The ONNX model is about 1 GB and reuses the sherpa-onnx CUDA environment; no PyTorch installation is required. Download it with `scripts/download_models.py --qwen`, or extract a verified archive so that `models/qwen3-asr-0.6b-onnx-int8/` contains the three ONNX files and `tokenizer/`. Recognized Latin words pass through Persian spelling correction unchanged. All processing remains local. This option is experimental: Qwen 0.6B INT8 and Whisper small both performed poorly on two public Persian/English samples. Qwen correctly transcribed one synthetic English-only sample. See `BILINGUAL_TEST.json`; these limited tests do not establish general accuracy. FastConformer remains the Persian default. Code-switching accuracy depends on the model, accent and audio; optional personal replacements such as `پایتون=Python` can enforce individual terms.

API references: [sherpa-onnx Qwen3-ASR](https://k2-fsa.github.io/sherpa/onnx/qwen3-asr/pretrained.html), [faster-whisper multilingual transcription](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/transcribe.py).

## انتخاب مدل برای دستگاه قوی‌تر / Larger-model option

از منوی کنار ساعت **انتخاب موتور گفتار** استفاده کنید. مدل پیش‌فرض بدون تغییر FastConformer فارسی است. دستگاه‌های قوی‌تر می‌توانند مدل بزرگ‌تر Whisper large-v3-turbo را دانلود و انتخاب کنند:

```bash
.venv/bin/python scripts/download_models.py --quality
# Alternatively include it during first setup:
# ./scripts/setup.sh --quality
```

| Engine | Available RAM checked before load | Notes |
|---|---:|---|
| FastConformer Persian | 1500 MiB | Default Persian-specific model |
| Qwen3-ASR 0.6B INT8 | 2200 MiB | Local multilingual ONNX; optional `--qwen` download |
| Whisper small | 1100 MiB | Lowest RAM threshold; optional `--whisper` download |
| Whisper large-v3-turbo | 3000 MiB | Larger model, beam size 5; optional `--quality` download |

These checks measure **available RAM**, not total installed RAM. They are conservative startup gates, not guarantees of fitting in memory; NVIDIA VRAM and other running applications also matter. All ASR modes request CUDA and exit after each recording. Qwen INT8 can include ONNX operators executed on the CPU when CUDA kernels are unavailable; its worker verifies a CUDA allocation, which does not prove every operator runs on the GPU. Workers fail when CUDA is unavailable or a Qwen/FastConformer CUDA allocation cannot be verified. Selecting an unavailable model gives a download instruction rather than silently switching engines. Larger Whisper may improve recognition over small, but is not guaranteed to outperform Persian FastConformer for your speech; compare the same recordings. Large-model inference has not been rerun on the original low-RAM laptop as part of this portability change.
