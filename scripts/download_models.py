#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime_paths import model_root
from huggingface_hub import snapshot_download

parser = argparse.ArgumentParser(description='Download public ASR models; no audio is uploaded.')
parser.add_argument('--whisper', action='store_true', help='Also download optional Whisper small fallback')
parser.add_argument('--quality', action='store_true', help='Also download the optional larger Whisper large-v3-turbo model')
parser.add_argument('--qwen', action='store_true', help='Download local Qwen3-ASR 0.6B INT8 for the existing sherpa-onnx runtime')
args = parser.parse_args()
root = model_root()
snapshot_download('PersianML/Shenava-Koochik-v1.0-sherpa-onnx', local_dir=root/'fastconformer-fa',
                  allow_patterns=['model.onnx', 'tokens.txt', 'README.md', 'LICENSE'], token=False)
if args.whisper:
    snapshot_download('Systran/faster-whisper-small', local_dir=root/'small',
                      allow_patterns=['*.json', 'model.bin', 'vocabulary.*', 'README.md', 'LICENSE'], token=False)

if args.quality:
    snapshot_download('dropbox-dash/faster-whisper-large-v3-turbo', local_dir=root/'large-v3-turbo',
                      allow_patterns=['*.json', 'model.bin', 'vocabulary.*', 'README.md', 'LICENSE'], token=False)

if args.qwen:
    snapshot_download('csukuangfj2/sherpa-onnx-qwen3-asr-0.6B-int8-2026-03-25',
                      local_dir=root/'qwen3-asr-0.6b-onnx-int8',
                      allow_patterns=['conv_frontend.onnx', 'encoder.int8.onnx', 'decoder.int8.onnx',
                                      'tokenizer/*', 'README.md', 'LICENSE'], token=False)
