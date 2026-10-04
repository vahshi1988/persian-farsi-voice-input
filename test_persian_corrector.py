import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import persian_corrector as corrector

class CorrectionTest(unittest.TestCase):
    def test_real_dictionary_and_punctuation(self):
        result = corrector.correct_text('طبق نخشه جلو بریم؛ حافضه پر شد.')
        self.assertEqual(result['text'], 'طبق نقشه جلو بریم؛ حافظه پر شد.')
        self.assertEqual(len(result['corrections']), 2)
        self.assertEqual(result['originalText'], 'طبق نخشه جلو بریم؛ حافضه پر شد.')

    def test_names_identifiers_and_valid_colloquial_words_preserved(self):
        text = 'محمد ثارا غمت نباش GPU1660 apiنخشه نخشه123 https://example.com/نخشه /home/نخشه `نخشه`'
        self.assertEqual(corrector.correct_text(text)['text'], text)

    def test_disabled_is_exact_identity(self):
        text = 'طبق نخشه جلو بریم'
        self.assertEqual(corrector.correct_text(text, False)['text'], text)

    def test_personal_words_and_explicit_mapping(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'words.json'
            path.write_text(json.dumps({'words':['نخشه'], 'replacements':{'نخشه':'نقشه', 'حافضه':'حافظه'}}))
            with patch.object(corrector, 'config_path', return_value=path):
                self.assertEqual(corrector.correct_text('نخشه و حافضه')['text'], 'نخشه و حافظه')

    def test_ambiguous_candidates_are_preserved(self):
        with patch.object(corrector.Dictionary, 'candidates', return_value={'نقشه','حافظه'}):
            self.assertEqual(corrector.correct_text('نخشه')['text'], 'نخشه')

    def test_context_can_disambiguate(self):
        with patch.object(corrector.Dictionary, 'contains', return_value=False), patch.object(
                corrector.Dictionary, 'candidates', return_value={'صوتی','سوتی'}):
            self.assertEqual(corrector.correct_text('ورودی ثوتی')['text'], 'ورودی صوتی')

    def test_dictionary_failure_never_loses_text(self):
        with patch.object(corrector, 'Dictionary', side_effect=RuntimeError('unavailable')):
            result = corrector.correct_text('طبق نخشه')
            self.assertEqual(result['text'], 'طبق نخشه')
            self.assertIn('spellingWarning', result)

if __name__ == '__main__':
    unittest.main()
