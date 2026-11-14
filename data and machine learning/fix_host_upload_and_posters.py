"""Run once beside app.py to let the host upload ratings and standardize poster cards."""
from pathlib import Path
import shutil

folder = Path(__file__).resolve().parent
app = folder / 'app.py'
if not app.is_file():
    raise SystemExit('Put this installer in the same folder as app.py.')
source = app.read_text(encoding='utf-8')
if 'AUTO_HOST_BOOKMARK_V1' not in source or 'import group_rooms' not in source:
    raise SystemExit('Install add_group_rooms.py and upgrade_host_one_click.py first.')
if 'HOST_UPLOAD_AND_POSTER_FIX_V1' in source:
    raise SystemExit('This update is already installed.')

anchor = "if st.button('Refresh uploads'):"
if anchor not in source:
    raise SystemExit('Could not find the host room section. No changes made.')
host_upload = '''# HOST_UPLOAD_AND_POSTER_FIX_V1
st.markdown('#### Upload your own ratings (host)')
st.caption('You can contribute your CSV here without opening the friend/join link.')
host_name = st.text_input('Your name', key=f'host_name_{code}')
host_file = st.file_uploader('Your Letterboxd ratings CSV', type=['csv'], key=f'host_csv_{code}')
if st.button('Submit my CSV as host', disabled=not (host_name.strip() and host_file is not None)):
    person = re.sub(r'[^a-z0-9]+', '_', host_name.strip().lower()).strip('_')
    for suffix in ('_rating', '_pred'):
        if person.endswith(suffix):
            person = person[:-len(suffix)]
    if not person:
        st.error('Enter a name containing letters or numbers.')
    else:
        try:
            csv_bytes = host_file.getvalue()
            if not csv_bytes:
                raise ValueError('The CSV is empty.')
            header = pd.read_csv(BytesIO(csv_bytes), nrows=0)
            missing = {'Name', 'Year', 'Rating'} - set(header.columns)
            if missing:
                raise ValueError('Missing CSV columns: ' + ', '.join(sorted(missing)))
            existing = group_rooms.members(code)
            if person in existing and st.session_state.get(f'host_uploaded_name_{code}') != person:
                raise ValueError('This name already has an upload. Choose a unique name.')
            group_rooms.upload(code, person, csv_bytes)
            st.session_state[f'host_uploaded_name_{code}'] = person
            st.success('Your CSV was uploaded to the group!')
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

'''
source = source.replace(anchor, host_upload + anchor, 1)

# Replace any earlier poster renderer, including the original st.image or HTML fix.
poster_start = "                            poster = movie.get('poster_link')"
poster_end = '                            st.markdown(f"#### #{index + 1} · {movie[\'movie\']}")'
a = source.find(poster_start)
b = source.find(poster_end, a)
if a == -1 or b == -1 or b <= a:
    raise SystemExit('Could not find the recommendation poster block. No changes made.')
poster_block = '''                            poster = movie.get('poster_link')
                            # A fixed poster area keeps every recommendation card the same size.
                            # HOST_UPLOAD_AND_POSTER_FIX_V1_POSTER
                            if pd.notna(poster) and str(poster).strip().startswith(('https://', 'http://')):
                                from html import escape as escape_html
                                safe_poster = escape_html(str(poster).strip(), quote=True)
                                st.markdown(
                                    '<div style="height:340px;width:100%;display:flex;'
                                    'align-items:center;justify-content:center;overflow:hidden;'
                                    'background:#111923;border-radius:10px;margin-bottom:12px">'
                                    f'<img src="{safe_poster}" alt="Movie poster" '
                                    'style="width:100%;height:100%;object-fit:contain;display:block">'
                                    '</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    '<div style="height:340px;display:flex;align-items:center;'
                                    'justify-content:center;background:#111923;'
                                    'border-radius:10px;margin-bottom:12px">🎬 Poster unavailable</div>',
                                    unsafe_allow_html=True,
                                )
'''
source = source[:a] + poster_block + source[b:]

backup = folder / 'app_before_host_upload_poster_fix.py'
if backup.exists():
    raise SystemExit('Backup already exists: app_before_host_upload_poster_fix.py. No changes made.')
compile(source, str(app), 'exec')
shutil.copy2(app, backup)
app.write_text(source, encoding='utf-8')
print('Updated app.py: host CSV upload and consistent 340px movie poster areas.')
print('Backup saved:', backup.name)
print('Start the website: python -m streamlit run app.py')
