# Holden Bailey, 2026

_registrants:dict = {}

def register(name:str | None = None) -> None:
    pf = # (prior frame)
    if name is None: name = pf.replace('_', ' ').title()
    _registrants[pf] = name