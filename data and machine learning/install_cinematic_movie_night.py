"""Install the cinematic Movie Night interface without touching the recommendation backend."""
from pathlib import Path
from datetime import datetime
import ast
import shutil

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app.py'
HELPER = ROOT / 'cinematic_ui.py'
MARKER = '# MOVIE_NIGHT_CINEMATIC_V2'

HELPER_SOURCE = r'''"""Movie Night visual components; no group or ML logic lives here."""
from html import escape
from urllib.parse import urlsplit
import math
import streamlit as st


def safe(value):
    if value is None:
        return ''
    try:
        if isinstance(value, float) and math.isnan(value):
            return ''
    except (TypeError, ValueError):
        pass
    return escape(str(value), quote=True)


def poster_url(value):
    try:
        value = str(value).strip()
        parts = urlsplit(value)
        if parts.scheme in ('http', 'https') and parts.netloc and not any(c in value for c in '\n\r\t'):
            return escape(value, quote=True)
    except Exception:
        pass
    return ''


def theme():
    st.markdown(r''' + "'''" + r'''<style>
    :root{color-scheme:dark}
    .stApp{background:#0b0b0e!important;color:#f5f5f6!important}
    [data-testid="stSidebar"]{background:#121216!important;border-right:1px solid #29292e}
    [data-testid="stHeader"]{background:rgba(10,10,12,.85)!important;backdrop-filter:blur(12px)}
    [data-testid="stMainBlockContainer"]{max-width:1320px;padding-top:1.6rem}
    .block-container h1,.block-container h2,.block-container h3{letter-spacing:-.035em}
    .stButton button[kind="primary"]{background:#e50914!important;color:#fff!important;border:1px solid #e50914!important;border-radius:7px!important;font-weight:750!important}
    .stButton button:not([kind="primary"]){border-radius:7px!important}
    [data-testid="stMetric"]{background:#19191e;border:1px solid #2a2a31;border-radius:12px;padding:16px}
    [data-testid="stFileUploader"],[data-testid="stExpander"]{border-radius:12px!important}
    .mn-nav{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 0 23px}
    .mn-brand{font-size:clamp(20px,2.8vw,29px);font-weight:950;letter-spacing:-.06em;color:#e50914}
    .mn-navlinks{font-size:12px;color:#aaaab4;letter-spacing:.02em}
    .mn-hero{min-height:285px;border-radius:16px;padding:clamp(26px,5vw,65px);margin-bottom:30px;background:linear-gradient(90deg,rgba(8,9,13,.98),rgba(8,9,13,.75) 53%,rgba(8,9,13,.13)),radial-gradient(ellipse at 84% 26%,#a3272c 0%,#422c35 35%,#101520 76%);display:flex;flex-direction:column;justify-content:center;box-shadow:0 25px 60px #0005}
    .mn-kicker{color:#ff8b8f;font-size:11px;font-weight:850;letter-spacing:2px;text-transform:uppercase}
    .mn-hero h1{font-size:clamp(34px,5vw,65px);line-height:1.06;letter-spacing:-.06em;margin:14px 0!important;color:#fff!important;font-weight:900}
    .mn-hero p{font-size:15px;color:#dedee2;max-width:580px;line-height:1.65;margin:0}
    .mn-strip{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px}
    .mn-chip{border:1px solid #ffffff40;background:#ffffff13;border-radius:6px;padding:9px 13px;font-size:12px;font-weight:650;color:#fff}
    .mn-shelf{margin:10px 0 18px}
    .mn-shelf h2{font-size:clamp(22px,3vw,30px);margin:0!important;font-weight:850}
    .mn-shelf p{color:#a7a7b0;font-size:13px;margin-top:7px}
    .mn-poster-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:17px;overflow:visible;padding:18px 9px 28px}
    .mn-card{position:relative;min-width:0;border-radius:10px;background:#18181d;border:1px solid #2a2a31;transition:transform .27s cubic-bezier(.2,.8,.2,1),box-shadow .27s,border-color .27s;transform-origin:center;outline:none;z-index:1;box-shadow:0 8px 20px #0005}
    .mn-card:hover,.mn-card:focus-within{transform:translateY(-9px) scale(1.10);z-index:10;border-color:#e50914;box-shadow:0 22px 45px #000c,0 0 0 1px #e50914}
    .mn-poster{aspect-ratio:2/3;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:9px 9px 0 0;background:radial-gradient(circle at 50% 25%,#293241,#111216 75%)}
    .mn-poster img{width:100%;height:100%;object-fit:contain;display:block}
    .mn-missing{font-size:14px;color:#a8a8b2;text-align:center;padding:14px}
    .mn-details{padding:12px 12px 15px}
    .mn-rank{color:#e50914;font-size:10px;font-weight:900;letter-spacing:.12em}
    .mn-name{font-size:14px;font-weight:800;line-height:1.35;min-height:38px;margin:5px 0 7px;overflow-wrap:anywhere}
    .mn-meta{font-size:11px;color:#a7a7af;line-height:1.5;overflow-wrap:anywhere}
    .mn-score{font-size:12px;color:#67d894;font-weight:850;margin:8px 0}
    .mn-extra{max-height:0;opacity:0;overflow:hidden;transition:max-height .22s,opacity .22s;font-size:11px;color:#d0d0d7}
    .mn-card:hover .mn-extra,.mn-card:focus-within .mn-extra{max-height:90px;opacity:1}
    @media(max-width:1100px){.mn-poster-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
    @media(max-width:750px){.mn-poster-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.mn-hero{min-height:240px}.mn-navlinks{display:none}.mn-card:hover,.mn-card:focus-within{transform:translateY(-4px) scale(1.035)}}
    @media(prefers-reduced-motion:reduce){.mn-card,.mn-extra{transition:none!important}}
    </style>''' + "'''" + r''', unsafe_allow_html=True)


def hero():
    st.markdown(''' + "'''" + r'''<div class="mn-nav"><div class="mn-brand">MOVIE NIGHT</div><div class="mn-navlinks">HOME &nbsp; / &nbsp; YOUR GROUP &nbsp; / &nbsp; RECOMMENDATIONS</div></div>
    <section class="mn-hero"><div class="mn-kicker">The ultimate group movie experience</div>
    <h1>One group.<br>One perfect movie.</h1>
    <p>Bring your friends together, combine your movie tastes, and discover what everyone will love.</p>
    <div class="mn-strip"><span class="mn-chip">01 · Create a room</span><span class="mn-chip">02 · Upload ratings</span><span class="mn-chip">03 · Find your movie</span></div></section>''' + "'''" + r''', unsafe_allow_html=True)


def movie_grid(recs):
    cards = []
    for rank, (_, movie) in enumerate(recs.head(10).iterrows(), start=1):
        url = poster_url(movie.get('poster_link', ''))
        poster = (f'<img src="{url}" alt="Poster for {safe(movie.get("movie", "Film"))}" loading="lazy">'
                  if url else '<div class="mn-missing">🎬<br>Poster unavailable</div>')
        try:
            score = f'{float(movie.get("group_pred_avg")):.2f} / 5 ★'
        except (ValueError, TypeError):
            score = 'Score unavailable'
        try:
            minimum = f'{float(movie.get("least_misery_score")):.2f} / 5'
        except (ValueError, TypeError):
            minimum = 'Unavailable'
        cards.append(f''' + "'''" + r'''<article class="mn-card" tabindex="0" aria-label="Movie {rank}: {safe(movie.get('movie', 'Untitled'))}">
          <div class="mn-poster">{poster}</div>
          <div class="mn-details"><div class="mn-rank">#{rank} GROUP PICK</div>
          <div class="mn-name">{safe(movie.get('movie', 'Untitled'))}</div>
          <div class="mn-meta">{safe(movie.get('year', ''))} · {safe(movie.get('genre', ''))}</div>
          <div class="mn-score">★ {score}</div>
          <div class="mn-extra">Lowest prediction: {minimum}<br>Director: {safe(movie.get('director', 'Unknown'))}</div>
          </div></article>''' + "'''" + r''')
    st.markdown('<div class="mn-shelf"><h2>Top picks for your group</h2><p>Real posters from your movie library. Hover to expand each recommendation.</p></div><div class="mn-poster-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)
'''


def main():
    if not APP.exists():
        raise SystemExit('app.py not found. Put this installer beside app.py and group_rooms.py.')
    source = APP.read_text(encoding='utf-8')
    if MARKER in source:
        print('Cinematic redesign already installed. No changes made.')
        return
    if 'import group_rooms' not in source or 'HOST_UPLOAD_AND_POSTER_FIX_V1' not in source:
        raise SystemExit('Expected group-room/host-upload version not found. No changes made.')
    if 'for index, (_, movie) in enumerate(recs.head(10).iterrows()):' not in source:
        raise SystemExit('Movie recommendation card loop not found. No changes made.')
    if "st.caption('MOVIE NIGHT / GROUP RECOMMENDATIONS')" not in source:
        raise SystemExit('Expected homepage header not found. No changes made.')
    # Replace only the recommendation-card rendering, leaving its DataFrame and downloads intact.
    start = source.index('                for index, (_, movie) in enumerate(recs.head(10).iterrows()):')
    end = source.index('            st.dataframe(recs.head(10)', start)
    source = source[:start] + '                cinematic_ui.movie_grid(recs)\n' + source[end:]
    header_start = source.index("st.caption('MOVIE NIGHT / GROUP RECOMMENDATIONS')")
    header_end = source.index("\nwith st.sidebar:", header_start)
    source = source[:header_start] + 'cinematic_ui.hero()\n' + source[header_end:]
    source = source.replace('import group_rooms\n', 'import group_rooms\nimport cinematic_ui\n', 1)
    source = source.replace("st.set_page_config(page_title='Movie Night', page_icon='🎬', layout='wide')", "st.set_page_config(page_title='Movie Night', page_icon='🎬', layout='wide')\n" + MARKER + "\ncinematic_ui.theme()", 1)
    ast.parse(source)
    ast.parse(HELPER_SOURCE)
    backup = APP.with_name('app_before_cinematic_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.py')
    shutil.copy2(APP, backup)
    if HELPER.exists():
        old_helper = HELPER.with_name('cinematic_ui_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.py')
        shutil.copy2(HELPER, old_helper)
    HELPER.write_text(HELPER_SOURCE, encoding='utf-8')
    APP.write_text(source, encoding='utf-8')
    print('Installed cinematic Movie Night design!')
    print('Backup:', backup.name)
    print('Created:', HELPER.name)
    print('Updated:', APP.name)
    print('Run: python -m streamlit run app.py')


if __name__ == '__main__':
    main()
