"""Rename visible Movie Night branding to Boxd Togther (exact requested spelling)."""
from pathlib import Path
from datetime import datetime
import shutil

folder = Path(__file__).resolve().parent
replacements = [
    ('MOVIE NIGHT', 'BOXD TOGTHER'),
    ('MOVIENIGHT', 'BOXD TOGTHER'),
    ('Movie Night', 'Boxd Togther'),
    ('movie night', 'Boxd Togther'),
]
changed = []
for name in ('app.py', 'cinematic_ui.py'):
    path = folder / name
    if not path.exists():
        continue
    old = path.read_text(encoding='utf-8')
    new = old
    for before, after in replacements:
        new = new.replace(before, after)
    if new == old:
        print(f'{name}: no branding text to change')
        continue
    if name.endswith('.py'):
        compile(new, str(path), 'exec')
    backup = folder / f'{path.stem}_before_boxd_togther_{datetime.now():%Y%m%d_%H%M%S}.py'
    shutil.copy2(path, backup)
    path.write_text(new, encoding='utf-8')
    changed.append(name)
    print(f'Updated {name} (backup: {backup.name})')
if not changed:
    print('No files updated. Put this script beside app.py and try again.')
else:
    print('Branding changed to Boxd Togther. Restart Streamlit to view it.')
