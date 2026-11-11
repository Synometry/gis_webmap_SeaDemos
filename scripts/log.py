# Holden Bailey, 2026

from pathlib import Path
from datetime import datetime
import inspect

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
    print(f'[{t_str}] [{name}] {msg}')
    
if __name__ == '__main__':
    # test
    register()
    print(_registrants)
    log('Hi', 'and', 'hello', 'world!')