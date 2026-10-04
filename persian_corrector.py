"""Conservative Persian dictionary correction using installed Hunspell, no ML model."""
import ctypes
import ctypes.util
import json
import re
from pathlib import Path
from runtime_paths import personal_dictionary_path

WORD = re.compile(r'[\u0621-\u063a\u0641-\u064a\u0671-\u06d3\u200c]+')
GROUPS = ('سصث', 'زذضظ', 'تط', 'قغخ', 'حه', 'اآ')
COMMON = set('''نقشه برنامه دستور متن کلمه معنی مفهوم فارسی ورودی خروجی صدا صوت تصویر پنجره دستگاه
حافظه تنظیمات ذخیره پردازش آزمایش نتیجه گزارش شروع پایان زمان نسخه فایل پوشه جمله گفتار
دیکشنری کتاب کتابخانه زبان صفحه نمایش شبکه سرور روتر اینترنت اتصال میکروفون ابزار
بررسی مناسب صحیح اشتباه تبدیل انتخاب تغییر مشکل اجازه اجرا نصب پروژه خدمت خدمت‌ها
کامپیوتر رایانه نرم‌افزار سخت‌افزار استفاده اطلاعات درخواست عملکرد مقدار کیفیت سرعت
عدد تعداد عبارت محاسبه نمودار محتوا نمونه پاسخ سوال سؤال کاربر سیستم لغت لغات'''.split())
CONTEXT = {
    'طبق': {'نقشه', 'برنامه', 'دستور'}, 'کادر': {'متن', 'ورودی'},
    'تبدیل': {'صدا', 'گفتار', 'متن'}, 'زبان': {'فارسی'}, 'ورودی': {'صوتی', 'متن'},
    'مصرف': {'حافظه'}, 'قطع': {'صدا', 'اتصال'}, 'ثبت': {'نتیجه', 'گزارش'},
    'تغییر': {'تنظیمات', 'نام'}, 'ذخیره': {'فایل', 'متن', 'اطلاعات'},
}

def normalize(word):
    return word.replace('ي', 'ی').replace('ك', 'ک')

class Dictionary:
    def __init__(self):
        self.lib = ctypes.CDLL(ctypes.util.find_library('hunspell-1.7') or 'libhunspell-1.7.so.0')
        self.lib.Hunspell_create.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.Hunspell_create.restype = ctypes.c_void_p
        self.lib.Hunspell_spell.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.lib.Hunspell_spell.restype = ctypes.c_int
        self.lib.Hunspell_destroy.argtypes = [ctypes.c_void_p]
        self.handle = self.lib.Hunspell_create(b'/usr/share/hunspell/fa_IR.aff', b'/usr/share/hunspell/fa_IR.dic')
        if not self.handle:
            raise RuntimeError('دیکشنری فارسی قابل خواندن نیست.')
        self.cache = {}

    def contains(self, word):
        if word not in self.cache:
            self.cache[word] = bool(self.lib.Hunspell_spell(self.handle, word.encode('utf-8')))
        return self.cache[word]

    def close(self):
        if self.handle:
            self.lib.Hunspell_destroy(self.handle)
            self.handle = None

    def candidates(self, word):
        result = set()
        # Only a single substitution in a restricted group of confusable letters.
        for i, letter in enumerate(word):
            for group in GROUPS:
                if letter in group:
                    for replacement in group:
                        candidate = word[:i] + replacement + word[i+1:]
                        if candidate != word and self.contains(candidate):
                            result.add(candidate)
        return result


def config_path():
    return personal_dictionary_path()


def correct_text(text, enabled=True):
    output = {'text': text, 'originalText': text, 'corrections': []}
    if not enabled or not text:
        return output
    dictionary = None
    try:
        path = config_path()
        config = json.loads(path.read_text()) if path.exists() else {}
        protected = {normalize(word) for word in config.get('words', []) if isinstance(word, str)}
        replacements = {normalize(key): value for key, value in config.get('replacements', {}).items()
                        if isinstance(key, str) and isinstance(value, str) and value.strip()}
        dictionary = Dictionary()
        protected_spans = [(m.start(), m.end()) for m in re.finditer(
            r'https?://\S+|www\.\S+|\S*/\S+|[\w.+-]+@[\w.-]+\.\w+|`[^`]*`', text)]
        matches = list(WORD.finditer(text))
        edits = []
        for index, match in enumerate(matches):
            if any(start < match.end() and match.start() < end for start, end in protected_spans):
                continue
            original = match.group()
            word = normalize(original)
            # Leave Persian fragments attached to Latin letters/digits (IDs) untouched.
            if (match.start() and text[match.start()-1].isalnum()) or (match.end() < len(text) and text[match.end()].isalnum()):
                continue
            if word in protected:
                continue
            replacement = replacements.get(word)
            reason = 'personal'
            if replacement is None:
                if len(word.replace('\u200c', '')) < 4 or dictionary.contains(word):
                    continue
                candidates = dictionary.candidates(word)
                previous = normalize(matches[index-1].group()) if index else ''
                if index and re.search(r'[^\s]', text[matches[index-1].end():match.start()]):
                    previous = ''
                contextual = candidates & CONTEXT.get(previous, set())
                if len(contextual) == 1:
                    candidate = next(iter(contextual))
                elif len(candidates) == 1 and next(iter(candidates)) in COMMON:
                    candidate = next(iter(candidates))
                else:
                    continue
                replacement, reason = candidate, 'dictionary'
            if replacement != original:
                edits.append((match.start(), match.end(), replacement))
                output['corrections'].append({'from': original, 'to': replacement, 'reason': reason})
        for start, end, replacement in reversed(edits):
            text = text[:start] + replacement + text[end:]
        output['text'] = text
    except Exception as error:
        # A dictionary failure must never lose the recognized text.
        output['text'] = output['originalText']
        output['corrections'] = []
        output['spellingWarning'] = str(error)
    finally:
        if dictionary:
            dictionary.close()
    return output
