import contextlib
import io
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
import persian_corrector
import qwen_worker


class QwenWorkerTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.audio = self.root / 'speech.pcm'
        self.audio.write_bytes(b'\0\0' * 16000)
        for name in ['conv_frontend.onnx', 'encoder.int8.onnx', 'decoder.int8.onnx',
                     'tokenizer/vocab.json', 'tokenizer/merges.txt', 'tokenizer/tokenizer_config.json']:
            p = self.root / name; p.parent.mkdir(exist_ok=True); p.touch()
        self.config = self.root / 'dictionary.json'
        self.config.write_text('{"words": [], "replacements": {}}')
        self.stream = Mock()
        self.stream.result = types.SimpleNamespace(text='از Python و GitHub استفاده کن.')
        self.recognizer = Mock()
        self.recognizer.create_stream.return_value = self.stream
        self.factory = Mock(return_value=self.recognizer)

    def tearDown(self):
        self.folder.cleanup()

    def run_request(self, **fields):
        sherpa = types.SimpleNamespace(OfflineRecognizer=types.SimpleNamespace(from_qwen3_asr=self.factory))
        with patch.dict('sys.modules', {'sherpa_onnx': sherpa}), \
                patch.object(qwen_worker, 'available_ram_mib', return_value=4000), \
                patch.object(qwen_worker, 'qwen_model_spec', return_value=(self.root, 2200)), \
                patch.object(qwen_worker, 'cuda_allocation_mib', return_value=600), \
                patch.object(persian_corrector, 'config_path', return_value=self.config), \
                contextlib.redirect_stdout(io.StringIO()):
            return qwen_worker.transcribe_request({'path': str(self.audio), **fields})

    def test_mixed_request_keeps_scripts_and_uses_local_onnx_cuda(self):
        result = self.run_request(languageMode='mixed')
        self.assertEqual(result['text'], 'از Python و GitHub استفاده کن.')
        self.assertEqual(result['corrections'], [])
        self.assertEqual(result['gpuMemoryMiB'], 600)
        self.assertEqual(self.factory.call_args.kwargs['provider'], 'cuda')
        self.assertEqual(self.factory.call_args.kwargs['decoder'], str(self.root/'decoder.int8.onnx'))
        rate, samples = self.stream.accept_waveform.call_args.args
        self.assertEqual(rate, 16000)
        self.assertEqual(samples.shape, (16000,))
        self.assertEqual(samples.dtype, np.float32)
        self.recognizer.decode_stream.assert_called_once_with(self.stream)
        self.stream.set_option.assert_not_called()

    def test_persian_mode_still_preserves_latin_words(self):
        result = self.run_request(languageMode='fa')
        self.assertEqual(result['text'], 'از Python و GitHub استفاده کن.')
        self.stream.set_option.assert_called_once_with('language', 'Persian')

    def test_insufficient_ram_rejects_loading(self):
        with patch.object(qwen_worker, 'available_ram_mib', return_value=1000), \
                self.assertRaisesRegex(RuntimeError, 'RAM'):
            qwen_worker.transcribe_request({'path': str(self.audio)})
        self.factory.assert_not_called()

    def test_cpu_fallback_is_rejected_before_decoding(self):
        with patch.object(qwen_worker, 'cuda_allocation_mib', side_effect=RuntimeError('NVIDIA unavailable')):
            # The inner run_request patch is intentionally avoided for the GPU-failure path.
            sherpa = types.SimpleNamespace(OfflineRecognizer=types.SimpleNamespace(from_qwen3_asr=self.factory))
            with patch.dict('sys.modules', {'sherpa_onnx': sherpa}), \
                    patch.object(qwen_worker, 'available_ram_mib', return_value=4000), \
                    patch.object(qwen_worker, 'qwen_model_spec', return_value=(self.root, 2200)), \
                    contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, 'NVIDIA'):
                qwen_worker.transcribe_request({'path': str(self.audio)})
        self.recognizer.decode_stream.assert_not_called()

    def test_missing_weights_fail_before_loading_a_model(self):
        (self.root/'decoder.int8.onnx').unlink()
        with self.assertRaisesRegex(RuntimeError, 'download_models.py --qwen'):
            self.run_request()
        self.factory.assert_not_called()

    def test_invalid_language_mode_does_not_load_a_model(self):
        with self.assertRaises(ValueError):
            self.run_request(languageMode='translate')
        self.factory.assert_not_called()

    def test_long_audio_is_rejected_before_loading(self):
        self.audio.write_bytes(b'\0' * (31 * 32000))
        with self.assertRaisesRegex(RuntimeError, '۳۰'):
            self.run_request()
        self.factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
