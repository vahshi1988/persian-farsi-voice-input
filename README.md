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

در منوی کنار ساعت گزینهٔ «موتور FastConformer فارسی» فعال است. غیرفعال‌کردن آن موتور قبلی Whisper small را انتخاب می‌کند. میانبر و تشخیص پایان گفتار با Silero تغییر نکرده‌اند. Silero روی CPU، ولی تبدیل متن روی NVIDIA اجرا می‌شود.

آزمایش روی **یک نمونهٔ** محاوره‌ای پرنویز از PSRB، خطای کاراکتر پس از حذف فاصله و نشانه‌گذاری: FastConformer حدود ۱۴٫۲٪ و Whisper small حدود ۲۹٫۲٪. این نتیجه ارزیابی عمومی یا تضمین دقت برای صدای شما نیست. FastConformer نمونهٔ حدود ۱۲ ثانیه‌ای را با بارگذاری مدل در ۲٫۷۶ ثانیه پردازش کرد؛ اوج RSS حدود ۱۰۱۳ MiB و تخصیص GPU هنگام بارگذاری ۵۹۶ MiB بود. عدد GPU اندازه‌گیری اوج مصرف نیست. جزئیات در `FASTCONFORMER_TEST.json` قرار دارد.

اگر RAM قابل‌استفاده کمتر از ۱۵۰۰ MiB برای FastConformer یا ۱۱۰۰ MiB برای Whisper باشد، مدل بارگذاری نمی‌شود و برنامه درخواست بستن چند برنامه را نشان می‌دهد. این آستانه تضمین نمی‌کند که سایر برنامه‌ها همزمان حافظه مصرف نکنند. حداکثر ضبط ۶۰ ثانیه و زمان پردازش ۱۲۰ ثانیه است.

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
- تنظیمات در `personal_dictionary.json` کنار سورس پروژه ذخیره می‌شوند و از ضبط بعدی اعمال خواهند شد.

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

The default engine is **Persian FastConformer / Shenava Koochik CTC**: an improved ONNX version from the NVIDIA FastConformer family, not the original model's unmodified weights. Model source: https://huggingface.co/PersianML/Shenava-Koochik-v1.0-sherpa-onnx . The model is expected in `models/fastconformer-fa`, with its separate Python environment in `fastconformer-venv`. Inference uses sherpa-onnx with CUDA 12 / cuDNN 9. The application checks the worker's GPU allocation with `nvidia-smi`; silently falling back to CPU is not accepted. The worker exits after each transcription to release memory.

The system-tray menu has a **Persian FastConformer engine** option. Disabling it selects the previous Whisper small engine. The shortcut and Silero end-of-speech detection remain unchanged. Silero runs on the CPU, while transcription runs on NVIDIA.

On **one** noisy conversational PSRB sample, character error rate after removing spaces and punctuation was about 14.2% for FastConformer and 29.2% for Whisper small. This is not a general evaluation or a guarantee of accuracy for your audio. FastConformer processed an approximately 12-second sample in 2.76 seconds, including model loading; peak RSS was about 1013 MiB, and GPU allocation during loading was 596 MiB. The GPU figure is not a peak-usage measurement. See `FASTCONFORMER_TEST.json` for details.

If available RAM is below 1500 MiB for FastConformer or 1100 MiB for Whisper, the model is not loaded and the application asks you to close some applications. These thresholds do not guarantee that other applications will not consume memory concurrently. Maximum recording duration is 60 seconds and the processing timeout is 120 seconds.

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
- Settings are saved in `personal_dictionary.json` next to the project source and take effect on the next recording.

URLs, paths, email addresses, text inside backticks, and identifiers adjacent to Latin letters or digits are not corrected. Word correction works offline, requires no additional model, and is applied with both FastConformer and Whisper.
