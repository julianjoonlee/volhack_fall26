# MOVIE_NIGHT_INTERACTIVE_LAYOUT_V1
from pathlib import Path
from tempfile import TemporaryDirectory
from io import BytesIO
import ast
import re
import hashlib


def configure_backend(source, script_name, people):
    """Configure only the fixed people list in a temporary execution copy."""
    target = 'rating_files' if script_name == 'pandas_group_data.py' else 'user_cols'
    matches = [node for node in ast.parse(source).body
               if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == target for t in node.targets)
               and isinstance(node.value, (ast.Dict, ast.List))]
    if len(matches) != 1:
        raise ValueError(f'{script_name}: expected one literal {target} configuration.')
    value = ({f'{p}_rating': f'{p}_ratings.csv' for p in people}
             if target == 'rating_files' else [f'{p}_rating' for p in people])
    node = matches[0].value
    raw = source.encode('utf-8')
    lines = raw.splitlines(keepends=True)
    start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
    end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
    return (raw[:start] + repr(value).encode('utf-8') + raw[end:]).decode('utf-8')

import json
import os
import shutil
import subprocess
import sys
import zipfile

import pandas as pd
import streamlit as st
import group_rooms
import cinematic_ui


APP_DIR = Path(__file__).resolve().parent
PEOPLE = ('arturo', 'jacob', 'jake', 'julian', 'matthew', 'sameer')
LIBRARY_FILES = ('movies.csv', 'crew.csv', 'actors.csv', 'genres.csv', 'posters.csv')
SCRIPT_NAMES = ('pandas_group_data.py', 'random_forest.py')
UPLOADED_SCRIPTS = {
    'pandas_group_data.py': Path('/mnt/data/assistant-6czdFGE1jHcvgiJqM4hEyy-pandas_group_data.py'),
    'random_forest.py': Path('/mnt/data/assistant-8iqgubYx6jrCzj99vfZNmd-random_forest.py'),
}


def resolve_scripts(folder):
    scripts = {}
    for name in SCRIPT_NAMES:
        path = folder / name
        if not path.is_file() and folder == APP_DIR:
            path = UPLOADED_SCRIPTS[name]
        if not path.is_file():
            raise ValueError(f'Missing backend script: {name}. Check the backend folder.')
        scripts[name] = path
    return scripts


def stage_file(source, destination):
    if isinstance(source, Path):
        try:
            destination.symlink_to(source.resolve())
        except OSError:
            shutil.copy2(source, destination)
    else:
        destination.write_bytes(source.getvalue())


def run_script(script, workspace, log_box, logs):
    env = dict(os.environ, MPLBACKEND='Agg', PYTHONUNBUFFERED='1')
    logs.append(f'\n>>> {script}')
    process = subprocess.Popen(
        [sys.executable, '-u', str(workspace / script)],
        cwd=str(workspace), env=env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
    )
    try:
        for line in process.stdout:
            logs.append(line.rstrip())
            log_box.code('\n'.join(logs[-45:]), language='text')
        return process.wait()
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        process.stdout.close()


def execute_pipeline(scripts, libraries, ratings, log_box, status):
    logs = []
    files = {}
    failure = None
    manifest = {
        'backend_sha256': {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in scripts.items()
        },
        'rating_slots': list(ratings),
        'library_sources': {
            name: ('local file' if isinstance(source, Path) else 'upload')
            for name, source in libraries.items()
        },
    }
    # Original files stay untouched. Adapt only input lists in temporary copies.
    baseline_mode = mode == 'Use existing hard-coded files'
    manifest['execution_mode'] = 'verbatim baseline' if baseline_mode else 'dynamic people'
    manifest['execution_sha256'] = {}
    with TemporaryDirectory(prefix='movie_night_') as temp:
        workspace = Path(temp)
        for name, path in scripts.items():
            destination = workspace / name
            if baseline_mode:
                shutil.copy2(path, destination)
            else:
                source = path.read_text(encoding='utf-8')
                destination.write_text(configure_backend(source, name, ratings), encoding='utf-8')
            manifest['execution_sha256'][name] = hashlib.sha256(destination.read_bytes()).hexdigest()
        for name, source in libraries.items():
            stage_file(source, workspace / name)
        for person, source in ratings.items():
            stage_file(source, workspace / f'{person}_ratings.csv')
        for index, name in enumerate(SCRIPT_NAMES, start=1):
            status.update(label=f'Step {index}/2 · Running {name}')
            code = run_script(name, workspace, log_box, logs)
            if code:
                failure = f'{name} exited with code {code}. Read the backend log below.'
                break
        for name in ('group_dataset.csv', 'group_recommendations.csv', 'group_dashboard.png'):
            path = workspace / name
            if path.is_file():
                files[name] = path.read_bytes()
        for path in sorted((workspace / 'figures').glob('*.png')):
            files[f'figures/{path.name}'] = path.read_bytes()
    files['backend.log'] = '\n'.join(logs).encode('utf-8')
    files['run_manifest.json'] = json.dumps(manifest, indent=2).encode('utf-8')
    archive = BytesIO()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for name, content in files.items():
            bundle.writestr(name, content)
    return {'files': files, 'archive': archive.getvalue(), 'failure': failure,
            'people': list(ratings)}


def show_comparison(actual_bytes, baseline, label):
    if baseline is None:
        return
    try:
        actual = pd.read_csv(BytesIO(actual_bytes))
        expected = pd.read_csv(BytesIO(baseline.getvalue()))
        pd.testing.assert_frame_equal(
            actual, expected, check_dtype=False, check_exact=False,
            rtol=1e-9, atol=1e-9,
        )
    except (AssertionError, ValueError, pd.errors.ParserError) as exc:
        st.error(f'{label}: does not match.')
        st.code(str(exc), language='text')
    else:
        st.success(f'{label}: matches, including row order, columns and values (numeric tolerance 1e-9).')
        if actual_bytes == baseline.getvalue():
            st.caption('The CSV files are also byte-for-byte identical.')
        else:
            st.caption('CSV bytes differ, but parsed values match within the stated tolerance.')


st.set_page_config(page_title='Movie Night', page_icon='🎬', layout='wide', initial_sidebar_state='collapsed')
# MOVIE_NIGHT_CINEMATIC_V2
cinematic_ui.theme()
cinematic_ui.interactive_theme()

# MOVIE_NIGHT_CINEMATIC_UI_V1 — presentation only, no backend changes
st.markdown("""
<style>
/* Design tokens */
:root {
  --mn-bg: #080d13;
  --mn-panel: #121c26;
  --mn-panel-2: #182631;
  --mn-text: #f4f7fa;
  --mn-muted: #a8b8c6;
  --mn-green: #21cf79;
  --mn-border: rgba(172, 201, 217, .17);
}
html { scroll-behavior: smooth; }
.stApp {
  background: radial-gradient(ellipse 85% 35% at 52% -6%, rgba(19, 108, 78, .29), transparent 78%),
              linear-gradient(180deg, #0b141d 0%, var(--mn-bg) 58%);
  color: var(--mn-text);
}
[data-testid="stAppViewContainer"] { background: transparent; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: #0d1721;
  border-right: 1px solid var(--mn-border);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--mn-muted); }
.block-container { max-width: 1260px; padding-top: 2.3rem; padding-bottom: 5rem; }
/* Typographic hierarchy */
h1, h2, h3, h4 { color: var(--mn-text); letter-spacing: -.035em; }
h1 { font-size: clamp(2.15rem, 5vw, 4.1rem) !important; line-height: 1.09 !important; font-weight: 800 !important; }
h2 { font-size: clamp(1.45rem, 2.8vw, 2rem) !important; font-weight: 750 !important; }
h3 { font-weight: 720 !important; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--mn-muted) !important; }
/* Brand / hero */
.mn-brandbar { display: flex; align-items: center; gap: .65rem; margin: .35rem 0 1.5rem; }
.mn-brandicon { width: 39px; height: 39px; border-radius: 12px; display: grid; place-items: center;
  color: #07160f; font-weight: 900; background: linear-gradient(145deg, #6cf3aa, #13b96d);
  box-shadow: 0 5px 24px rgba(32, 211, 121, .22); font-size: 1.25rem; }
.mn-brandname { font-size: 1.05rem; font-weight: 850; letter-spacing: .09em; color: #f8fbff; }
.mn-brandpill { margin-left: auto; padding: .35rem .8rem; border: 1px solid rgba(48, 217, 128, .34);
  background: rgba(33, 207, 121, .08); border-radius: 100px; color: #8df1ba; font-size: .73rem;
  font-weight: 750; letter-spacing: .08em; text-transform: uppercase; }
.mn-hero-eyebrow { color: #8bf0b6; font-size: .76rem; font-weight: 800; letter-spacing: .18em;
  text-transform: uppercase; margin-bottom: -.25rem; }
.mn-hero-rule { height: 1px; background: linear-gradient(90deg, rgba(33, 207, 121, .7), rgba(33, 207, 121, 0));
  margin: 1.3rem 0 1.9rem; }
/* Buttons, fields, and uploader */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius: 12px !important; min-height: 2.9rem; font-weight: 700;
  border: 1px solid rgba(172, 201, 217, .22); transition: background .16s, border-color .16s, transform .16s;
}
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-1px); border-color: #53e49c; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background: linear-gradient(120deg, #20d47d, #0db66a) !important;
  color: #07150e !important; border: 1px solid #20d47d !important;
  box-shadow: 0 5px 22px rgba(20, 192, 111, .18);
}
.stButton > button[kind="primary"]:disabled { opacity: .48; box-shadow: none; }
[data-testid="stFileUploader"] { background: rgba(20, 34, 46, .65); border-radius: 15px; padding: .35rem; }
[data-testid="stFileUploaderDropzone"] { border: 1px dashed rgba(69, 207, 139, .48); border-radius: 12px; }
[data-baseweb="input"] > div, [data-baseweb="select"] > div {
  background-color: #13212d !important; border-color: rgba(172, 201, 217, .23) !important;
  border-radius: 10px !important;
}
/* Tabs, dividers, and output panels */
[data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid var(--mn-border); flex-wrap: wrap; }
button[data-baseweb="tab"] { color: #b7c8d4; font-weight: 650; border-radius: 9px 9px 0 0; }
button[data-baseweb="tab"][aria-selected="true"] { color: #8af3b6; }
hr { border-color: var(--mn-border) !important; }
[data-testid="stMetric"] { padding: 1.1rem 1.2rem; border-radius: 15px;
  background: linear-gradient(145deg, #172631, #111c26); border: 1px solid var(--mn-border); }
[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
  border-radius: 15px;
}
/* Streamlit bordered containers — leave poster HTML dimensions untouched */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 15px !important; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
/* Accessibility */
button:focus-visible, input:focus-visible, textarea:focus-visible, a:focus-visible {
  outline: 2px solid #70efad !important; outline-offset: 3px;
}
@media (max-width: 700px) {
  .block-container { padding-top: 1.25rem; padding-left: 1rem; padding-right: 1rem; }
  .mn-brandpill { display: none; }
  .mn-brandbar { margin-bottom: 1.1rem; }
  h1 { font-size: 2.15rem !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; animation: none !important; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mn-brandbar">
  <div class="mn-brandicon" aria-hidden="true">▶</div>
  <div class="mn-brandname">MOVIE NIGHT</div>
  <div class="mn-brandpill">Better together</div>
</div>
<div class="mn-hero-eyebrow">Find the perfect group pick</div>
""", unsafe_allow_html=True)

st.markdown('''<style>
.stApp { background: #10171e; color: #edf3f8; }
[data-testid="stSidebar"] { background: #18232d; }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3 { letter-spacing: -0.03em; }
div.stButton > button[kind="primary"] { background: #00a842; border: 0; color: white; }
[data-testid="stMetric"] { padding: 1rem; background: #1b2834; border-radius: 12px; }
</style>''', unsafe_allow_html=True)
cinematic_ui.interactive_hero()

with st.sidebar:
    st.header('Backend setup')
    backend_folder = Path(st.text_input('Folder containing both Python scripts', str(APP_DIR))).expanduser().resolve()
    st.caption('Paths refer to the computer running Streamlit.')
    library_mode = st.radio('Movie library source', ['Local folder', 'Upload library CSVs'])
    libraries = {}
    if library_mode == 'Local folder':
        library_folder = Path(st.text_input('Library folder', str(APP_DIR))).expanduser().resolve()
        for name in LIBRARY_FILES:
            libraries[name] = library_folder / name
        st.caption('Required: ' + ', '.join(LIBRARY_FILES))
    else:
        st.caption('For large datasets, use a local folder instead.')
        for name in LIBRARY_FILES:
            libraries[name] = st.file_uploader(name, type=['csv'], key=f'library_{name}')
    st.divider()
    st.caption('The original matching, training, random seeds and ranking stay in your two backend scripts.')

# AUTO_HOST_BOOKMARK_V1
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
    st.markdown('<div class="mn-landing-actions">Start your movie night</div>', unsafe_allow_html=True)
    landing_create, landing_join = st.columns(2, gap='medium')
    with landing_create:
        if st.button('＋ Create a group', type='primary', use_container_width=True, key='mn-create'):
            new_code, new_key = group_rooms.create_room()
            st.session_state['group_code'] = new_code
            st.session_state['group_host_key'] = new_key
            st.query_params['room'] = new_code
            st.query_params['host'] = new_key
            st.rerun()
    with landing_join:
        if st.button('Join with a code', use_container_width=True, key='mn-join'):
            st.session_state['mn_show_join'] = True
    if st.session_state.get('mn_show_join'):
        choice = 'Join a group'
    else:
        choice = 'Create a group'
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
with st.container(border=True):
    st.success(f'You are hosting room {code}')
    st.code(code, language=None)
    st.caption('Share only the code above and the public website address with friends. Bookmark your current URL privately to return as host.')
    st.warning('Do not share your current browser URL: it contains a private host credential.')
    # HOST_UPLOAD_AND_POSTER_FIX_V1
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

if st.button('Refresh uploads'):
    st.rerun()
shared_uploads = group_rooms.get_uploads(code)
st.write('Uploaded: ' + (', '.join(shared_uploads) or 'Nobody yet'))
# FLEXIBLE_GROUP_UPLOADS_V1
# Any number of members may upload; the host can generate once at least one CSV exists.
if shared_uploads:
    st.success(f"{len(shared_uploads)} CSV file(s) uploaded. Ready to generate recommendations.")
else:
    st.info('Waiting for the first CSV upload.')
ratings = {person: BytesIO(data) for person, data in shared_uploads.items()}
people_valid = bool(shared_uploads)
mode = 'Upload ratings'
with st.expander('Delete this room and its uploads'):
    confirm = st.checkbox('Permanently delete this room and all its CSVs')
    if st.button('Delete room', disabled=not confirm):
        group_rooms.delete_room(code, host_key)
        st.session_state.pop('group_code', None)
        st.session_state.pop('group_host_key', None)
        st.query_params.clear()
        st.rerun()

with st.container(border=True):
    st.subheader('2 · Run the recommendation workflow')
    st.caption('At least one person needs five rated movies with usable matching library features. '
               'Your backend skips people below that threshold. Runs include its original charts and poster downloads.')
    if st.button('Generate recommendations', type='primary', disabled=not ratings or not people_valid):
        st.session_state.pop('movie_result', None)
        try:
            scripts = resolve_scripts(backend_folder)
            missing = [name for name, source in libraries.items()
                       if source is None or (isinstance(source, Path) and not source.is_file())]
            if missing:
                raise ValueError('Missing library files: ' + ', '.join(missing))
            for person, source in ratings.items():
                reader = source if isinstance(source, Path) else BytesIO(source.getvalue())
                header = pd.read_csv(reader, nrows=0)
                missing_columns = {'Name', 'Year', 'Rating'} - set(header.columns)
                if missing_columns:
                    raise ValueError(f'{person.capitalize()}: missing CSV columns: {", ".join(sorted(missing_columns))}')
            with st.status('Starting the original backend scripts…', expanded=True) as status:
                log_box = st.empty()
                result = execute_pipeline(scripts, libraries, ratings, log_box, status)
                st.session_state['movie_result'] = result
                status.update(
                    label='Backend stopped — inspect the log' if result['failure'] else 'Recommendations ready',
                    state='error' if result['failure'] else 'complete', expanded=bool(result['failure']),
                )
        except Exception as exc:
            st.error(str(exc))

result = st.session_state.get('movie_result')
if result:
    files = result['files']
    st.divider()
    st.subheader('3 · Results from your last run')
    st.caption('People included: ' + ', '.join(p.capitalize() for p in result['people']) +
               '. Changing inputs does not update these results until you run again.')
    if result['failure']:
        st.error(result['failure'])
        st.caption('Any files below were saved before the failure; the full workflow did not finish.')
    st.download_button('Download all outputs + backend log', result['archive'],
                       'movie_night_results.zip', 'application/zip')
    rec_tab, group_tab, charts_tab, compare_tab, log_tab = st.tabs(
        ['Recommendations', 'Group dataset', 'Backend charts', 'Compare with Python', 'Backend log'])
    with rec_tab:
        if 'group_recommendations.csv' not in files:
            st.info('The backend has not produced a recommendations CSV.')
        else:
            recs = pd.read_csv(BytesIO(files['group_recommendations.csv']))
            metrics = st.columns(3)
            metrics[0].metric('Recommended films', len(recs))
            metrics[1].metric('Trained people', len([c for c in recs if c.endswith('_pred')]))
            metrics[2].metric('Top group prediction',
                              f"{recs.iloc[0]['group_pred_avg']:.2f} / 5" if len(recs) else '—')
            st.caption('Original backend order: group average, then minimum individual prediction, '
                       'then global rating. Scores are model predictions, not actual ratings.')
            if len(recs):
                st.markdown('### Top 10 recommendations')
                if len(recs) < 10:
                    st.info(f'The backend returned only {len(recs)} eligible recommendations.')
                cinematic_ui.movie_grid(recs)
            st.dataframe(recs.head(10), hide_index=True, use_container_width=True)
            st.download_button('Download top 10 CSV', recs.head(10).to_csv(index=False).encode('utf-8'),
                               'top_10_recommendations.csv', 'text/csv')
            with st.expander(f'All backend recommendations ({len(recs)})'):
                st.dataframe(recs, hide_index=True, use_container_width=True)
            st.download_button('Download full recommendations CSV', files['group_recommendations.csv'],
                               'group_recommendations.csv', 'text/csv')
    with group_tab:
        if 'group_dataset.csv' in files:
            group = pd.read_csv(BytesIO(files['group_dataset.csv']))
            st.caption(f'{len(group):,} group rows · {group["id"].isna().sum():,} rows without a matched library ID')
            st.dataframe(group, hide_index=True, use_container_width=True)
            st.download_button('Download group dataset CSV', files['group_dataset.csv'],
                               'group_dataset.csv', 'text/csv')
        else:
            st.info('No group dataset was produced.')
    with charts_tab:
        images = [name for name in files if name.endswith('.png')]
        if images:
            selected = st.selectbox('Original backend chart', images)
            st.image(files[selected], caption=selected, use_container_width=True)
            st.download_button('Download chart', files[selected], Path(selected).name, 'image/png')
        else:
            st.info('No charts were produced.')
    with compare_tab:
        st.write('Upload CSV outputs saved from running your scripts directly with the same input files. '
                 'This checks values and row order without sorting or changing either file.')
        st.caption('Use the same Python environment and package versions for the closest comparison. '
                   'These controls only compare files; they do not retrain the model.')
        for name in ('group_dataset.csv', 'group_recommendations.csv'):
            baseline = st.file_uploader(f'Python baseline: {name}', type=['csv'], key=f'baseline_{name}')
            if name in files:
                show_comparison(files[name], baseline, name)
            elif baseline is not None:
                st.info(f'No UI-generated {name} is available to compare.')
    with log_tab:
        st.code(files['backend.log'].decode('utf-8'), language='text')
        st.download_button('Download backend log', files['backend.log'], 'backend.log', 'text/plain')
else:
    st.info('Add ratings and your library files, then generate recommendations. Your backend files stay unchanged.')
