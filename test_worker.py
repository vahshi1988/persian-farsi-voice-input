import contextlib
import io
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

import persian_corrector
import worker


class WorkerLanguageTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.audio = self.root / 'audio.pcm'
        self.audio.write_bytes(b'\0\0' * 16000)
        (self.root / 'model.bin').touch()
        self.config = self.root / 'dictionary.json'
        self.config.write_text('{"words": [], "replacements": {}}')
        self.model = Mock()
        self.factory = Mock(return_value=self.model)
        self.model.transcribe.side_effect = self.transcribe
        self.options = None

    def tearDown(self):
        self.folder.cleanup()

    def transcribe(self, wav_path, **options):
        # Verify the real worker's audio bridge and language options together.
        with wave.open(wav_path) as wav:
            self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate()), (1, 2, 16000))
            self.assertEqual(wav.getnframes(), 16000)
        self.options = options
        segments = iter([types.SimpleNamespace(text='طبق نخشه با Python و GitHub کار کن.')])
        return segments, types.SimpleNamespace(language='fa')

    def run_request(self, **fields):
        request = {'path': str(self.audio), 'model': 'small', **fields}
        module = types.SimpleNamespace(WhisperModel=self.factory)
        with patch.dict('sys.modules', {'faster_whisper': module}), \
                patch.object(worker, 'available_ram_mib', return_value=4000), \
                patch.object(worker, 'whisper_model_spec', return_value=(self.root, 1100)), \
                patch.object(persian_corrector, 'config_path', return_value=self.config), \
                contextlib.redirect_stdout(io.StringIO()):
            return worker.transcribe_request(request)

    def test_mixed_speech_is_transcribed_and_latin_words_survive_correction(self):
        result = self.run_request(languageMode='mixed', language='fa')
        self.assertIsNone(self.options['language'])
        self.assertTrue(self.options['multilingual'])
        self.assertEqual(self.options['task'], 'transcribe')
        self.assertEqual(result['text'], 'طبق نقشه با Python و GitHub کار کن.')
        self.assertEqual(result['originalText'], 'طبق نخشه با Python و GitHub کار کن.')
        self.assertEqual(result['corrections'], [{'from': 'نخشه', 'to': 'نقشه', 'reason': 'dictionary'}])
        self.assertEqual(result['languageMode'], 'mixed')
        self.assertEqual(self.factory.call_args.kwargs['device'], 'cuda')
        self.assertTrue(self.factory.call_args.kwargs['local_files_only'])

    def test_legacy_persian_request_keeps_language_locked(self):
        self.run_request()
        self.assertEqual(self.options['language'], 'fa')
        self.assertFalse(self.options['multilingual'])
        self.assertEqual(self.options['task'], 'transcribe')

    def test_mixed_mode_does_not_override_the_selected_whisper_model(self):
        self.run_request(languageMode='mixed', model='large-v3-turbo')
        self.assertEqual(self.options['beam_size'], 5)

    def test_invalid_language_mode_is_rejected_before_loading_a_model(self):
        with self.assertRaises(ValueError):
            self.run_request(languageMode='translate')
        self.factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
