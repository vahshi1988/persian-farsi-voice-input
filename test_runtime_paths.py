import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import runtime_paths

class RuntimePathsTest(unittest.TestCase):
    def test_xdg_dictionary_is_outside_checkout(self):
        with patch.dict(os.environ, {'XDG_CONFIG_HOME':'/tmp/config-test'}, clear=True):
            self.assertEqual(runtime_paths.personal_dictionary_path(), Path('/tmp/config-test/voice-input/personal_dictionary.json'))

    def test_explicit_paths(self):
        with patch.dict(os.environ, {'VOICE_INPUT_DICTIONARY':'/tmp/user.json', 'VOICE_INPUT_MODEL_DIR':'/tmp/asr-models'}):
            self.assertEqual(runtime_paths.personal_dictionary_path(), Path('/tmp/user.json'))
            self.assertEqual(runtime_paths.model_root(), Path('/tmp/asr-models'))

    def test_model_selection_and_memory_thresholds(self):
        with patch.dict(os.environ, {'VOICE_INPUT_MODEL_DIR':'/tmp/asr-models'}):
            self.assertEqual(runtime_paths.whisper_model_spec('small'), (Path('/tmp/asr-models/small'), 1100))
            self.assertEqual(runtime_paths.whisper_model_spec('large-v3-turbo'), (Path('/tmp/asr-models/large-v3-turbo'), 3000))
            with self.assertRaises(ValueError):
                runtime_paths.whisper_model_spec('../invalid')

    def test_source_and_build_layout(self):
        with patch.object(runtime_paths, '__file__', '/tmp/checkout/runtime_paths.py'):
            self.assertEqual(runtime_paths.project_root(), Path('/tmp/checkout'))
        with patch.object(runtime_paths, '__file__', '/tmp/checkout/build/runtime_paths.py'):
            self.assertEqual(runtime_paths.project_root(), Path('/tmp/checkout'))

if __name__ == '__main__':
    unittest.main()
