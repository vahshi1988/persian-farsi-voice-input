#!/usr/bin/env python3
"""Generate user-specific launchers, never hard-code the author's home directory."""
import argparse
import os
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--autostart', action='store_true', help='Enable launch on Plasma login')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
binary = root / 'build/voice-input'
if not binary.is_file():
    parser.error('Build the application first: scripts/setup.sh')
# Desktop Entry Exec escaping, including literal percent field codes.
quoted = str(binary).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
base = '''[Desktop Entry]
Type=Application
Name=Persian Voice Input
Name[fa]=ورودی صوتی فارسی
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Accessibility;
'''
config_home = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))
personal = config_home/'voice-input/personal_dictionary.json'
legacy = root/'personal_dictionary.json'
if legacy.exists() and not personal.exists():
    personal.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy, personal)
data = Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))
launcher = data/'applications/local.voiceinput.desktop'
launcher.parent.mkdir(parents=True, exist_ok=True)
launcher.write_text(base+f'Exec="{quoted}" --setup\nStartupNotify=true\n')
print(launcher)
if args.autostart:
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))
    startup = config/'autostart/local.voiceinput.desktop'
    startup.parent.mkdir(parents=True, exist_ok=True)
    startup.write_text(base+f'Exec="{quoted}" --background --setup\nOnlyShowIn=KDE;\nStartupNotify=false\nX-KDE-autostart-phase=2\n')
    print(startup)
