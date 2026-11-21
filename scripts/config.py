# config.py
# Holden Bailey 2026
#
# Manages configuration settings for the scripts in this directory

from pathlib import Path
import atexit
import types
import log
log.register()

_config_path = Path('./scripts/config.txt')
_config_path.touch()

# (doubles as defaults)
_idict = {
    'write_to_file': 'true'
}
with _config_path.open('rt') as conf_file:
    for line in conf_file.readlines():
        key, val = [side.strip('\'\"').strip() for side in line.split(':')]
        if key in _idict.keys(): _idict[key] = val
log.log(f'Loaded configuration from \"{_config_path}\"')

# Configuration Settings
def write_to_file() -> bool: return str.lower(_idict['write_to_file']) == 'true'
def set_write_to_file(val: bool) -> None:
    _idict['write_to_file'] = str(val)
    log.set_write_to_file(val)

# *unrelated to public function
def _write_to_file() -> None:
    log.log('Writing config to disk...')
    with _config_path.open('wt') as conf_file:
        conf_file.write('\n'.join([f'{k}: {v}' for k, v in _idict.items()]))
    log.log(f'Saved config to \"{_config_path}\"')

atexit.register(_write_to_file)