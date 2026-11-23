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

# raw value dict (doubles as defaults)
_idict = {
    'write_to_file': 'true',
    'dir_external_data': './ext_data'
}

# Configuration Settings
def write_to_file() -> bool: return str.lower(_idict['write_to_file']) == 'true'
def set_write_to_file(val: bool) -> None:
    _idict['write_to_file'] = str(val)
    log.set_write_to_file(val)
    
def dir_external_data() -> Path: return Path(_idict['dir_external_data'])
def set_dir_external_data(val: Path) -> None:
    _idict['dir_external_data'] = str(val)

with _config_path.open('rt') as conf_file:
    for line in conf_file.readlines():
        key, val = [side.strip('\'\"').strip() for side in line.split(':')]
        globals()[f'set_{key}']
log.log(f'Loaded configuration from \"{_config_path}\"')

# *unrelated to public function
def _write_to_file() -> None:
    log.log('Writing config to disk...')
    with _config_path.open('wt') as conf_file:
        conf_file.write('\n'.join([f'{k}: {v}' for k, v in _idict.items()]))
    log.log(f'Saved config to \"{_config_path}\"')

atexit.register(_write_to_file)