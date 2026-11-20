# Holden Bailey, 2026

from pathlib import Path
from datetime import datetime
import inspect
import shutil

def out_width(): return shutil.get_terminal_size().columns

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
    _output('INFO', *messages)

def error(*messages: str):
    _output('ERROR', *messages)

def _output(context: str, *messages: str):
    t_str = datetime.now().strftime('%y:%m:%d %I:%M:%S %p')
    pfi = inspect.stack()[2]
    pf = inspect.getmodule(pfi.frame).__name__
    if not pf in _registrants.keys():
        name = module_name_to_fancy(pf)
    else:
        name = _registrants[pf]
    log_prefix = f'[{t_str}] [{name}] {context}'
    
    # tabulation for nested list of message columns (not rows)
    if all([isinstance(m, list) for m in messages]):
        messages = [
            [str(item) for item in col] for col in messages
        ]
        maxima = [
            max([len(i) for i in col]) for col in messages
        ]
        for i in range(len(messages[0])):
            line = ''.join([col[i] + ' ' * (mx + 1 - len(col[i])) for col, mx in zip(messages, maxima)])
            _handle_formatted(log_prefix, line)
    else:
        msg = ' '.join([str(m) for m in messages])
        for line in msg.splitlines():
            _handle_formatted(log_prefix, line)

def _handle_formatted(prefix: str, message: str):
    log_line = prefix + ': ' + message
    print(log_line[:out_width()])
    if write_to_file: write(log_line)

if __name__ == '__main__':
    # test
    register()
    print(_registrants)
    log('Hi', 'and', 'hello', 'world!')
    log(['one', 'two', 'three', 'seventeen', 'two', 'three'], ['one','one','one','one','one','one'])