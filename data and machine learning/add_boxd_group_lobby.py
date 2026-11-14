"""Install a group upload lobby and evidence-based taste compatibility in Boxd Togther.
Run once beside app.py and group_rooms.py. Makes timestamped backups.
"""
from pathlib import Path
from datetime import datetime
import ast
import shutil

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app.py'
ROOMS = ROOT / 'group_rooms.py'
HELPER = ROOT / 'boxd_group_ui.py'
MARKER = '# BOXD_GROUP_LOBBY_COMPAT_V1'

HELPER_SOURCE = r'''"""Visual room lobby and shared-rating compatibility for Boxd Togther."""
from io import BytesIO
from itertools import combinations
from html import escape
import pandas as pd
import streamlit as st

CSS = """<style>
.boxd-lobby-title{font-size:clamp(1.3rem,2.5vw,2rem);font-weight:850;letter-spacing:-.035em;margin:.2rem 0 .2rem}
.boxd-lobby-sub{color:#a9a9b5;font-size:.93rem;margin-bottom:1rem}
.boxd-lobby-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:16px 0 20px}
.boxd-member{border:1px solid #34313b;background:linear-gradient(145deg,#23212a,#141319);border-radius:16px;padding:20px 16px;min-height:145px;animation:boxd-rise .5s ease both;transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease}
.boxd-member:hover{transform:translateY(-5px);border-color:#d13b4a;box-shadow:0 12px 30px #0007}
.boxd-avatar{display:grid;place-items:center;width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#ef3449,#76152a);font-size:1.25rem;font-weight:850;color:#fff;margin-bottom:12px}
.boxd-member-name{color:#fff;font-size:1rem;font-weight:750;overflow-wrap:anywhere}
.boxd-member-status{color:#83e6ae;font-size:.78rem;font-weight:650;margin-top:6px}
.boxd-empty{padding:20px;border:1px dashed #514651;border-radius:14px;color:#b5aeba;background:#1c1921}
.boxd-meter{height:9px;background:#34303b;border-radius:99px;overflow:hidden;margin:12px 0 6px}
.boxd-meter-fill{height:100%;background:linear-gradient(90deg,#a91c31,#ff5264);border-radius:99px;transition:width .6s ease}
.boxd-score{font-size:clamp(2.4rem,6vw,4rem);font-weight:900;line-height:1.05;letter-spacing:-.055em;color:#fff}
.boxd-score-label{color:#bdb7c3;font-size:.9rem}
@keyframes boxd-rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@media(prefers-reduced-motion:reduce){.boxd-member{animation:none;transition:none}.boxd-member:hover{transform:none}.boxd-meter-fill{transition:none}}
</style>"""


def _ratings(blob):
    """Return film key -> rating fraction, using a consistent per-file rating scale."""
    try:
        df = pd.read_csv(BytesIO(blob), usecols=['Name', 'Year', 'Rating'])
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df = df.dropna(subset=['Name', 'Year', 'Rating'])
        df = df[df['Rating'] > 0]
        if df.empty:
            return {}
        # Letterboxd normally uses a 0.5–5 rating scale. Also handle 10-point CSVs.
        maximum = 10.0 if df['Rating'].max() > 5 else 5.0
        df = df[df['Rating'] <= maximum].copy()
        df['film'] = list(zip(df['Name'].astype(str).str.strip().str.casefold(), df['Year'].astype(int)))
        df['normalized'] = df['Rating'] / maximum
        return df.groupby('film')['normalized'].mean().to_dict()
    except (ValueError, KeyError, pd.errors.ParserError, UnicodeError, OverflowError):
        return {}


def compatibility(uploads):
    """Average pairwise agreement on films both people rated; never invent a score."""
    profiles = {name: _ratings(blob) for name, blob in uploads.items()}
    similarities = []
    pairs = 0
    comparisons = 0
    for (name_a, a), (name_b, b) in combinations(profiles.items(), 2):
        common = a.keys() & b.keys()
        # At least 3 shared films per pair avoids presenting a one-film match as meaningful.
        if len(common) < 3:
            continue
        pairs += 1
        for film in common:
            similarities.append(1.0 - abs(a[film] - b[film]))
            comparisons += 1
    if not similarities:
        return None
    return {'score': round(100 * sum(similarities) / len(similarities)),
            'pairs': pairs, 'comparisons': comparisons,
            'members': len(profiles)}


def render(code, uploads, expected=None):
    """Show uploaded members, progress and compatibility. No private CSVs are displayed."""
    st.markdown(CSS, unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="boxd-lobby-title">Your group lobby</div>', unsafe_allow_html=True)
        st.markdown('<div class="boxd-lobby-sub">Room ' + escape(str(code)) + ' · Members appear when their ratings are uploaded</div>', unsafe_allow_html=True)
        names = sorted(uploads)
        if names:
            cards = []
            for i, name in enumerate(names):
                safe_name = escape(str(name).replace('_', ' ').title())
                letter = escape(str(name)[:1].upper())
                cards.append('<div class="boxd-member" style="animation-delay:' + str(min(i, 10) * 60) + 'ms"><div class="boxd-avatar">' + letter + '</div><div class="boxd-member-name">' + safe_name + '</div><div class="boxd-member-status">✓ Ratings uploaded</div></div>')
            st.markdown('<div class="boxd-lobby-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="boxd-empty">No ratings uploaded yet. Share your group code to invite friends.</div>', unsafe_allow_html=True)
        if expected is not None:
            total = max(1, int(expected))
            filled = min(len(names), total)
            st.markdown('<div class="boxd-lobby-sub">' + str(len(names)) + ' of ' + str(total) + ' uploads received</div><div class="boxd-meter"><div class="boxd-meter-fill" style="width:' + str(100 * filled / total) + '%"></div></div>', unsafe_allow_html=True)
        else:
            st.caption(f'{len(names)} member(s) have uploaded their ratings.')
        st.caption('Use Refresh uploads to check for new members. This is an upload-status lobby, not live online-presence tracking.')

    with st.container(border=True):
        st.markdown('<div class="boxd-lobby-title">Group compatibility</div>', unsafe_allow_html=True)
        st.caption('Calculated from movies that multiple members have actually rated.')
        if len(uploads) < 2:
            st.info('At least two members must upload ratings to calculate compatibility.')
            return
        result = compatibility(uploads)
        if result is None:
            st.info('Not enough shared ratings yet. At least two members need to have rated 3 of the same movies.')
            return
        st.markdown('<div class="boxd-score">' + str(result['score']) + '%</div><div class="boxd-score-label">Average taste agreement</div>', unsafe_allow_html=True)
        st.progress(result['score'] / 100)
        st.caption(f"Based on {result['comparisons']} shared-film rating comparisons across {result['pairs']} member pair(s).")
        with st.expander('How is this calculated?'):
            st.write('We match movies by title and release year. For each pair of members who rated at least three of the same films, we compare their normalized ratings. Exact agreement scores 100%; larger differences reduce the score. The overall percentage is the average of those comparisons. It is descriptive, not a machine-learning prediction, and pairs with more shared films contribute more.')
'''


def main():
    if not APP.is_file() or not ROOMS.is_file():
        raise SystemExit('Put this script next to app.py and group_rooms.py. No files changed.')
    app = APP.read_text(encoding='utf-8')
    if MARKER in app:
        print('Group lobby and compatibility are already installed.')
        return
    host_anchor = 'shared_uploads = group_rooms.get_uploads(code)\n'
    join_anchor = "    st.write('Members uploaded: ' + (', '.join(group_rooms.members(code)) or 'None yet'))\n"
    if app.count(host_anchor) != 1 or app.count(join_anchor) != 1:
        raise SystemExit('This version of app.py has a different group layout. Nothing changed; share app.py so the installer can be adapted.')
    if 'import group_rooms' not in app:
        raise SystemExit('Group rooms are not installed. No files changed.')
    # Host: render immediately after loading the same uploaded CSVs used by the model.
    app = app.replace(host_anchor, host_anchor + 'boxd_group_ui.render(code, shared_uploads, expected=st.session_state.get(f"expected_{code}"))  ' + MARKER + '\n', 1)
    # Joiner: show lobby without exposing host-only controls or private host credentials.
    app = app.replace(join_anchor, join_anchor + '    boxd_group_ui.render(code, group_rooms.get_uploads(code))\n', 1)
    app = app.replace('import group_rooms\n', 'import group_rooms\nimport boxd_group_ui\n', 1)
    ast.parse(app)
    ast.parse(HELPER_SOURCE)
    if HELPER.exists():
        raise SystemExit('boxd_group_ui.py already exists; refusing to overwrite it. Nothing changed.')
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = ROOT / f'app_before_boxd_lobby_{stamp}.py'
    shutil.copy2(APP, backup)
    try:
        HELPER.write_text(HELPER_SOURCE, encoding='utf-8')
        APP.write_text(app, encoding='utf-8')
    except Exception:
        shutil.copy2(backup, APP)
        if HELPER.exists():
            HELPER.unlink()
        raise
    print('Installed animated group lobby and real compatibility score.')
    print('Backup:', backup.name)
    print('Restart: python -m streamlit run app.py')

if __name__ == '__main__':
    main()
