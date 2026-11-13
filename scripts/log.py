# Holden Bailey, 2026

from pathlib import Path
from datetime import datetime
import inspect

config = {
    'write_to_file': 'True',
    'log_dir':'logs/'
}

write_to_file = config['write_to_file'].lower() == 'true'

if write_to_file:
    logFile = Path(config['log_dir'], 'log.txt')
    oldFile = Path(f'{logFile}'.replace('.txt', '.old.txt'))
    if logFile.exists():
        oldFile.unlink()
        logFile.rename(oldFile)
    else: logFile.touch()

def write(*s: str) -> None:
    with logFile.open('a', encoding='UTF-8') as f:
        f.write('\n'.join(s) + '\n')

_registrants:dict = {}

def module_name_to_fancy(mod: str) -> str:
    return mod.replace('_', ' ').title().strip()

def register(name:str | None = None) -> None:
    pfi = inspect.stack()[1]
    pf = inspect.getmodule(pfi.frame).__name__
    if name is None: name = module_name_to_fancy(pf)
    _registrants[pf] = name
    
def log(*messages: str):
    t_str = datetime.now().strftime('%y:%m:%d %I:%M:%S %p')
    pfi = inspect.stack()[1]
    pf = inspect.getmodule(pfi.frame).__name__
    if not pf in _registrants.keys():
        name = module_name_to_fancy(pf)
    else:
        name = _registrants[pf]
    msg = ' '.join([str(m) for m in messages])
    log_prefix = f'[{t_str}] [{name}]'
    for line in msg.splitlines():
        log_line = log_prefix + ' ' + line
        print(log_line)
        if write_to_file: write(log_line)
    
if __name__ == '__main__':
    # test
    register()
    print(_registrants)
    log('Hi', 'and', 'hello', 'world!')