"""Remove the expected-member CSV gate from Movie Night's Streamlit app.

Run once from the directory containing app.py. Creates a timestamped backup.
"""
from pathlib import Path
from datetime import datetime
import ast
import shutil
import sys

app = Path(__file__).resolve().parent / 'app.py'
if not app.exists():
    sys.exit('Cannot find app.py. Put this script next to app.py and try again.')
source = app.read_text(encoding='utf-8')

start_marker = "expected_members = st.number_input('How many people are uploading CSVs (including you)?'"
end_marker = "mode = 'Upload ratings'"
start = source.find(start_marker)
end = source.find(end_marker, start) if start >= 0 else -1

if start < 0 or end < 0:
    if '# FLEXIBLE_GROUP_UPLOADS_V1' in source:
        print('Already installed. No changes needed.')
        sys.exit(0)
    sys.exit('Could not find the expected-member section in app.py. No files changed. Send me that part of app.py so I can adapt the patch.')

replacement = '''# FLEXIBLE_GROUP_UPLOADS_V1
# Any number of members may upload; the host can generate once at least one CSV exists.
if shared_uploads:
    st.success(f"{len(shared_uploads)} CSV file(s) uploaded. Ready to generate recommendations.")
else:
    st.info('Waiting for the first CSV upload.')
ratings = {person: BytesIO(data) for person, data in shared_uploads.items()}
people_valid = bool(shared_uploads)
'''
updated = source[:start] + replacement + source[end:]

# Also guard against an earlier installer using a distinct minimum-count gate.
try:
    ast.parse(updated, filename=str(app))
except SyntaxError as exc:
    sys.exit(f'Update did not pass syntax validation. No files changed: {exc}')

backup = app.with_name(f'app_before_flexible_uploads_{datetime.now():%Y%m%d_%H%M%S}.py')
shutil.copy2(app, backup)
app.write_text(updated, encoding='utf-8')
print('Updated app.py successfully!')
print(f'Backup: {backup.name}')
print('The host can now generate recommendations with any nonzero number of uploaded CSVs.')
