"""Helpers for applying evidence-backed Ghidra labels to generated functions."""
import json
import re
from pathlib import Path


def confirmed_function_names(root: Path) -> dict[str, str]:
    """Return title labels and registration-stub names keyed by XBE VA."""
    root = Path(root)
    names = json.loads((root / 'tools/ghidra/obiwan_function_names.json').read_text())
    registrations = json.loads(
        (root / 'tools/ghidra/obiwan_script_registrations.json').read_text()
    )['registrations']
    for entry in registrations:
        command = entry['name']
        if not command:
            continue
        identifier = re.sub(r'[^A-Za-z0-9_]', '_', command)
        if not identifier or identifier[0].isdigit():
            identifier = '_' + identifier
        names[entry['stub_va']] = f'obiwan_register_script_{identifier}'

    # Runtime collisions are deliberate: the runtime owns the Xbe_* labels.
    names.update(json.loads((root / 'tools/ghidra/runtime_name_overrides.json').read_text()))
    return names
