"""Run once next to app.py to add multi-device group rooms to Movie Night."""
from pathlib import Path
import shutil

folder = Path(__file__).resolve().parent
app = folder / 'app.py'
if not app.is_file():
    raise SystemExit('Place this file next to app.py, then run it again.')

helper = r'''"""Shared SQLite storage for Movie Night rooms (one shared server required)."""
import os
import secrets
import sqlite3
from pathlib import Path

DB = Path(os.environ.get('MOVIE_NIGHT_DB_PATH', str(Path(__file__).resolve().parent / 'movie_rooms.sqlite3')))
MAX_CSV_BYTES = 25 * 1024 * 1024
MAX_MEMBERS = 12


def connection():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB), timeout=20)
    db.execute('PRAGMA busy_timeout=20000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS rooms (code TEXT PRIMARY KEY, host_key TEXT NOT NULL)')
    db.execute("""CREATE TABLE IF NOT EXISTS uploads (
        code TEXT NOT NULL, name TEXT NOT NULL, csv BLOB NOT NULL,
        PRIMARY KEY (code, name), FOREIGN KEY(code) REFERENCES rooms(code))""")
    return db


def create_room():
    with connection() as db:
        for _ in range(10):
            code = secrets.token_hex(3).upper()
            key = secrets.token_urlsafe(18)
            try:
                db.execute('INSERT INTO rooms VALUES (?, ?)', (code, key))
                return code, key
            except sqlite3.IntegrityError:
                pass
    raise RuntimeError('Could not create a unique room code.')


def exists(code):
    with connection() as db:
        return db.execute('SELECT 1 FROM rooms WHERE code=?', (code,)).fetchone() is not None


def is_host(code, key):
    with connection() as db:
        return db.execute('SELECT 1 FROM rooms WHERE code=? AND host_key=?', (code, key)).fetchone() is not None


def members(code):
    with connection() as db:
        return [row[0] for row in db.execute('SELECT name FROM uploads WHERE code=? ORDER BY name', (code,))]


def upload(code, name, csv):
    if len(csv) > MAX_CSV_BYTES:
        raise ValueError('CSV is too large (25 MB limit).')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM rooms WHERE code=?', (code,)).fetchone():
            raise ValueError('Group code does not exist.')
        count = db.execute('SELECT COUNT(*) FROM uploads WHERE code=?', (code,)).fetchone()[0]
        current = db.execute('SELECT 1 FROM uploads WHERE code=? AND name=?', (code, name)).fetchone()
        if count >= MAX_MEMBERS and not current:
            raise ValueError('This group is full (12 members).')
        db.execute('INSERT OR REPLACE INTO uploads (code, name, csv) VALUES (?, ?, ?)', (code, name, csv))


def get_uploads(code):
    with connection() as db:
        return dict(db.execute('SELECT name, csv FROM uploads WHERE code=? ORDER BY name', (code,)))


def delete_room(code, key):
    if not is_host(code, key):
        raise ValueError('Invalid host key.')
    with connection() as db:
        db.execute('DELETE FROM uploads WHERE code=?', (code,))
        db.execute('DELETE FROM rooms WHERE code=? AND host_key=?', (code, key))
'''

replacement = r'''st.subheader('1 · Create or join a group')
st.caption('Everyone must open the SAME hosted website. A localhost link works only on your own computer.')
room_action = st.radio('Group access', ['Create group', 'Join group', 'Host an existing group'], horizontal=True)

if room_action == 'Create group':
    if st.button('Create new group'):
        code, key = group_rooms.create_room()
        st.session_state['group_code'] = code
        st.session_state['group_host_key'] = key
    if st.session_state.get('group_code') and st.session_state.get('group_host_key'):
        st.success('Your group is ready!')
        st.code(st.session_state['group_code'])
        st.warning('Save your HOST KEY below privately. Anyone with it can run recommendations or delete the room.')
        st.code(st.session_state['group_host_key'])
        st.info('Share only the group code and your website URL with friends. Then select “Host an existing group” to run recommendations.')
    st.stop()

code = st.text_input('Group code', value=st.session_state.get('group_code', ''),
                     placeholder='e.g. A1B2C3').strip().upper()
if not code or not group_rooms.exists(code):
    st.info('Enter a valid group code to continue.')
    st.stop()

if room_action == 'Join group':
    st.write('Upload your own Letterboxd ratings CSV. Other group members cannot see your file through this page.')
    display_name = st.text_input('Your name (unique within this group)')
    upload_file = st.file_uploader('Your ratings CSV', type=['csv'], key=f'group_csv_{code}')
    if st.button('Submit my ratings', disabled=not (display_name.strip() and upload_file)):
        person = re.sub(r'[^a-z0-9]+', '_', display_name.lower().strip()).strip('_')
        person = person.removesuffix('_rating').removesuffix('_pred') if hasattr(person, 'removesuffix') else person
        if not person:
            st.error('Please enter a name containing letters or numbers.')
        else:
            try:
                csv_bytes = upload_file.getvalue()
                header = pd.read_csv(BytesIO(csv_bytes), nrows=0)
                missing_cols = {'Name', 'Year', 'Rating'} - set(header.columns)
                if missing_cols:
                    raise ValueError('Missing columns: ' + ', '.join(sorted(missing_cols)))
                group_rooms.upload(code, person, csv_bytes)
                st.success('Your ratings were saved! The host can now include you.')
            except Exception as exc:
                st.error(str(exc))
    st.write('Members who uploaded: ' + (', '.join(group_rooms.members(code)) or 'None yet'))
    st.stop()

host_key = st.text_input('Private host key', value=st.session_state.get('group_host_key', ''), type='password')
if not group_rooms.is_host(code, host_key):
    st.info('Enter the host key created with this group.')
    st.stop()
st.success(f'Hosting group {code}')
if st.button('Refresh member list'):
    st.rerun()
shared_uploads = group_rooms.get_uploads(code)
st.write('Ready: ' + (', '.join(shared_uploads) or 'No uploads yet'))
ratings = {person: BytesIO(data) for person, data in shared_uploads.items()}
people_valid = bool(ratings)
mode = 'Upload ratings'
with st.expander('Delete this group and its uploaded CSV files'):
    confirm_delete = st.checkbox('I understand all uploads in this group will be deleted')
    if st.button('Delete group permanently', disabled=not confirm_delete):
        group_rooms.delete_room(code, host_key)
        st.session_state.pop('group_code', None)
        st.session_state.pop('group_host_key', None)
        st.rerun()

'''

source = app.read_text(encoding='utf-8')
if 'import group_rooms' in source:
    raise SystemExit('Group rooms already appear to be installed. No changes made.')
start = source.find("st.subheader('1 · Add your group')")
end = source.find("st.subheader('2 · Run the recommendation workflow')")
if start < 0 or end < 0 or end <= start:
    raise SystemExit('Could not find the expected section of app.py. No changes made.')
# Ensure existing backend can read in-memory BytesIO uploads (it uses getvalue()).
source = source.replace('import streamlit as st\n', 'import streamlit as st\nimport group_rooms\n', 1)
start = source.find("st.subheader('1 · Add your group')")
end = source.find("st.subheader('2 · Run the recommendation workflow')")
source = source[:start] + replacement + source[end:]
backup = folder / 'app_before_groups.py'
if backup.exists():
    raise SystemExit('app_before_groups.py already exists; rename it before running this installer.')
shutil.copy2(app, backup)
(folder / 'group_rooms.py').write_text(helper, encoding='utf-8')
app.write_text(source, encoding='utf-8')
print('Installed group rooms in app.py')
print('Backup:', backup)
print('Created group_rooms.py (shared SQLite storage)')
print('Run: python -m streamlit run app.py')
