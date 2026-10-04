"""Shared portable locations; environment overrides are documented in README."""
import os
from pathlib import Path

def project_root():
    here = Path(__file__).resolve().parent
    return here.parent if here.name == 'build' else here

def model_root():
    return Path(os.environ.get('VOICE_INPUT_MODEL_DIR', project_root() / 'models')).expanduser()

def personal_dictionary_path():
    override = os.environ.get('VOICE_INPUT_DICTIONARY')
    if override:
        return Path(override).expanduser()
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return config / 'voice-input/personal_dictionary.json'


def whisper_model_spec(name):
    """RAM thresholds are protective minimums, not hardware fit guarantees."""
    choices = {'small': 1100, 'large-v3-turbo': 3000}
    if name not in choices:
        raise ValueError('Unsupported Whisper model: ' + str(name))
    return model_root() / name, choices[name]
