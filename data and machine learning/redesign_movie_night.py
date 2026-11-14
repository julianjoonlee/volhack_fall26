"""One-time, visual-only cinematic redesign for the existing Movie Night Streamlit app.

Place beside app.py and run: python redesign_movie_night.py
Does not modify group_rooms.py, databases, CSVs, or machine-learning scripts.
"""
from pathlib import Path
from datetime import datetime
import shutil
import sys

HERE = Path(__file__).resolve().parent
APP = HERE / 'app.py'
MARKER = 'MOVIE_NIGHT_CINEMATIC_UI_V1'

if not APP.is_file():
    sys.exit('ERROR: Place this script beside app.py in the data and machine learning folder.')

original = APP.read_text(encoding='utf-8')
if MARKER in original:
    sys.exit('This cinematic theme is already installed. No changes made.')
if 'st.set_page_config(' not in original:
    sys.exit('ERROR: Could not find Streamlit page configuration. No changes made.')
if 'import streamlit as st' not in original:
    sys.exit('ERROR: This does not look like the expected Streamlit app. No changes made.')

# Preserve all Python workflow code; only add CSS and a decorative header.
THEME = r'''# MOVIE_NIGHT_CINEMATIC_UI_V1 — presentation only, no backend changes
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
'''

# Insert immediately after page configuration; Streamlit page config must come first.
anchor = "st.set_page_config("
start = original.find(anchor)
# Locate end of the page config statement using Python AST, not fragile string matching.
import ast
try:
    tree = ast.parse(original)
    page_call = next(node for node in tree.body if isinstance(node, ast.Expr)
                     and isinstance(node.value, ast.Call)
                     and isinstance(node.value.func, ast.Attribute)
                     and isinstance(node.value.func.value, ast.Name)
                     and node.value.func.value.id == 'st'
                     and node.value.func.attr == 'set_page_config')
except (SyntaxError, StopIteration) as exc:
    sys.exit(f'ERROR: Could not safely identify Streamlit setup: {exc}')

lines = original.splitlines(keepends=True)
insert_at = sum(len(line) for line in lines[:page_call.end_lineno])
updated = original[:insert_at] + '\n' + THEME + '\n' + original[insert_at:]

# Optional existing hero subtitle gets a cinematic divider, without touching workflow code.
hero_line = "st.write('Upload Letterboxd ratings, run your existing Python workflow, and find the group’s next watch.')"
if hero_line in updated:
    updated = updated.replace(hero_line, hero_line + "\nst.markdown('<div class=\"mn-hero-rule\"></div>', unsafe_allow_html=True)", 1)

try:
    compile(updated, str(APP), 'exec')
except SyntaxError as exc:
    sys.exit(f'ERROR: Updated app failed syntax validation. Nothing changed: {exc}')

stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup = HERE / f'app_before_cinematic_{stamp}.py'
shutil.copy2(APP, backup)
try:
    APP.write_text(updated, encoding='utf-8')
except Exception:
    shutil.copy2(backup, APP)
    raise

print('SUCCESS: Applied Movie Night cinematic UI theme to app.py')
print('Backup:', backup.name)
print('Unchanged: group_rooms.py, machine-learning scripts, CSVs, SQLite, and poster dimensions.')
print('Run: python -m streamlit run app.py')
