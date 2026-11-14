"""Upgrade Movie Night group rooms to automatic host access via a private bookmark URL.
Run once beside app.py and group_rooms.py, after add_group_rooms.py.
"""
from pathlib import Path
import shutil

folder = Path(__file__).resolve().parent
app = folder / 'app.py'
helper = folder / 'group_rooms.py'
if not app.exists() or not helper.exists():
    raise SystemExit('First install add_group_rooms.py in the same folder as app.py.')
source = app.read_text(encoding='utf-8')
start_marker = "st.subheader('1 · Create or join a group')"
end_marker = "st.subheader('2 · Run the recommendation workflow')"
start = source.find(start_marker)
end = source.find(end_marker)
if start == -1 or end == -1 or end < start:
    raise SystemExit('Could not locate the group-room section. No files changed.')
if 'AUTO_HOST_BOOKMARK_V1' in source:
    raise SystemExit('Automatic host access is already installed.')

new_section = '''# AUTO_HOST_BOOKMARK_V1
st.subheader('1 · Your movie night group')
st.caption('Friends join using the group code and upload their own Letterboxd CSVs.')

# The host link contains a secret, so bookmarking it restores host access after refresh.
# Share the room code, NEVER the private host link.
url_code = str(st.query_params.get('room', '')).strip().upper()
url_host = str(st.query_params.get('host', '')).strip()
if url_code and group_rooms.exists(url_code):
    st.session_state['group_code'] = url_code
    if url_host and group_rooms.is_host(url_code, url_host):
        st.session_state['group_host_key'] = url_host

current_code = st.session_state.get('group_code', '')
current_key = st.session_state.get('group_host_key', '')
is_current_host = bool(current_code and current_key and group_rooms.is_host(current_code, current_key))

if not is_current_host:
    choice = st.radio('Get started', ['Create a group', 'Join a group'], horizontal=True)
    if choice == 'Create a group':
        if st.button('Create group', type='primary'):
            new_code, new_key = group_rooms.create_room()
            st.session_state['group_code'] = new_code
            st.session_state['group_host_key'] = new_key
            st.query_params['room'] = new_code
            st.query_params['host'] = new_key
            st.rerun()
        st.info('Create a room to get a shareable code. Your browser will open the host view automatically.')
        st.stop()
    code = st.text_input('Group code', value=url_code or current_code, placeholder='ABC123').strip().upper()
    if not code or not group_rooms.exists(code):
        st.info('Enter a valid group code to join.')
        st.stop()
    st.markdown(f'**Room {code}**')
    display_name = st.text_input('Your name')
    csv_file = st.file_uploader('Your Letterboxd ratings CSV', type=['csv'], key=f'upload_{code}')
    if st.button('Submit my CSV', disabled=not (display_name.strip() and csv_file)):
        person = re.sub(r'[^a-z0-9]+', '_', display_name.strip().lower()).strip('_')
        for suffix in ('_rating', '_pred'):
            if person.endswith(suffix):
                person = person[:-len(suffix)]
        if not person:
            st.error('Please enter a name with letters or numbers.')
        else:
            try:
                csv_bytes = csv_file.getvalue()
                header = pd.read_csv(BytesIO(csv_bytes), nrows=0)
                missing = {'Name', 'Year', 'Rating'} - set(header.columns)
                if missing:
                    raise ValueError('Missing CSV columns: ' + ', '.join(sorted(missing)))
                group_rooms.upload(code, person, csv_bytes)
                st.success('Uploaded! The host can include your ratings.')
            except Exception as exc:
                st.error(str(exc))
    st.write('Members uploaded: ' + (', '.join(group_rooms.members(code)) or 'None yet'))
    st.stop()

code = current_code
host_key = current_key
# Keep the private bookmark URL in sync when host is recognized from the session.
if st.query_params.get('room') != code or st.query_params.get('host') != host_key:
    st.query_params['room'] = code
    st.query_params['host'] = host_key
st.success(f'You are hosting room {code}')
st.code(code, language=None)
st.caption('Share only the code above and the public website address with friends. Bookmark your current URL privately to return as host.')
st.warning('Do not share your current browser URL: it contains a private host credential.')
if st.button('Refresh uploads'):
    st.rerun()
shared_uploads = group_rooms.get_uploads(code)
st.write('Uploaded: ' + (', '.join(shared_uploads) or 'Nobody yet'))
expected_members = st.number_input('How many people are uploading CSVs (including you)?', min_value=1, max_value=12,
                                   value=3, step=1, key=f'expected_{code}')
ready = len(shared_uploads) >= expected_members
if ready:
    st.success(f'All {expected_members} CSVs are in. You can generate recommendations below.')
else:
    st.info(f'Waiting for {expected_members - len(shared_uploads)} more CSV(s).')
ratings = {person: BytesIO(data) for person, data in shared_uploads.items()}
people_valid = ready
mode = 'Upload ratings'
with st.expander('Delete this room and its uploads'):
    confirm = st.checkbox('Permanently delete this room and all its CSVs')
    if st.button('Delete room', disabled=not confirm):
        group_rooms.delete_room(code, host_key)
        st.session_state.pop('group_code', None)
        st.session_state.pop('group_host_key', None)
        st.query_params.clear()
        st.rerun()

'''
backup = folder / 'app_before_auto_host.py'
if backup.exists():
    raise SystemExit('app_before_auto_host.py already exists. Rename it before retrying.')
shutil.copy2(app, backup)
app.write_text(source[:start] + new_section + source[end:], encoding='utf-8')
print('Updated app.py with automatic host recognition and host-only generation.')
print('Backup:', backup)
print('Host access persists through a private bookmarked URL, not a browser cookie.')
print('Start with: python -m streamlit run app.py')
