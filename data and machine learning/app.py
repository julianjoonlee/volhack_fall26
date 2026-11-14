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


st.set_page_config(page_title='Movie Night', page_icon='🎬', layout='wide')
st.markdown('''<style>
.stApp { background: #10171e; color: #edf3f8; }
[data-testid="stSidebar"] { background: #18232d; }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3 { letter-spacing: -0.03em; }
div.stButton > button[kind="primary"] { background: #00a842; border: 0; color: white; }
[data-testid="stMetric"] { padding: 1rem; background: #1b2834; border-radius: 12px; }
</style>''', unsafe_allow_html=True)
st.caption('MOVIE NIGHT / GROUP RECOMMENDATIONS')
st.title('Different tastes. One movie night.')
st.write('Upload Letterboxd ratings, run your existing Python workflow, and find the group’s next watch.')

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

st.subheader('1 · Add your group')
mode = st.radio('Ratings source', ['Upload ratings', 'Use existing hard-coded files'], horizontal=True)
ratings = {}
people_valid = True
if mode == 'Upload ratings':
    st.caption('One CSV per person, with Name, Year and Rating columns. '
               'Upload one person or a larger group—there is no fixed people limit. '
               'Give each person a unique name, even if their files share the same filename.')
    uploads = st.file_uploader('People’s ratings CSVs', type=['csv'],
                               accept_multiple_files=True, key='group_uploads')
    for index, upload in enumerate(uploads):
        default = re.sub(r'_ratings?$', '', Path(upload.name).stem, flags=re.IGNORECASE)
        name = st.text_input(f'Person {index + 1} · {upload.name}', value=default,
                             key=f'person_name_{index}_{upload.name}')
        person = re.sub(r'[^a-z0-9]+', '_', name.strip().lower()).strip('_')
        person = person.replace('_rating', '').replace('_pred', '')
        if not person:
            st.error(f'Person {index + 1}: enter a name containing letters or numbers.')
            people_valid = False
        elif person in ratings:
            st.error(f'Person {index + 1}: choose a unique name. Output name {person} is already used.')
            people_valid = False
        else:
            ratings[person] = upload
            st.caption(f'Output rating column: {person}_rating')
    # The original six names sort into their original backend order for comparison.
    ratings = dict(sorted(ratings.items()))
    if uploads:
        st.caption(f'{len(uploads)} people selected. Each eligible person gets a separate model.')
else:
    ratings_folder = Path(st.text_input('Folder containing your existing ratings CSVs', str(APP_DIR))).expanduser().resolve()
    for person in PEOPLE:
        path = ratings_folder / f'{person}_ratings.csv'
        if path.is_file():
            ratings[person] = path
    st.caption('Expected filenames: ' + ', '.join(f'{p}_ratings.csv' for p in PEOPLE))
    if ratings:
        st.success('Found: ' + ', '.join(p.capitalize() for p in ratings))
    else:
        st.info('No matching ratings files found in that folder.')

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
                for index, (_, movie) in enumerate(recs.head(10).iterrows()):
                    if index % 3 == 0:
                        cards = st.columns(3)
                    with cards[index % 3]:
                        with st.container(border=True):
                            poster = movie.get('poster_link')
                            if pd.notna(poster) and str(poster).strip().startswith(('https://', 'http://')):
                                st.image(str(poster).strip(), use_container_width=True)
                            else:
                                st.caption('🎬 Poster unavailable')
                            st.markdown(f"#### #{index + 1} · {movie['movie']}")
                            st.caption(f"{int(movie['year'])} · {movie['genre']}")
                            st.write(f"Group prediction: **{movie['group_pred_avg']:.2f} ★**")
                            st.write(f"Lowest prediction: **{movie['least_misery_score']:.2f} ★**")
                            st.caption(f"Director: {movie['director']}")
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
