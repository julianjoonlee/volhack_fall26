"""Boxd Together visual components; no group or ML logic lives here."""
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
    st.markdown(r'''<style>
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
    </style>''', unsafe_allow_html=True)


def hero():
    st.markdown('''<div class="mn-nav"><div class="mn-brand">Boxd Together</div><div class="mn-navlinks">HOME &nbsp; / &nbsp; YOUR GROUP &nbsp; / &nbsp; RECOMMENDATIONS</div></div>
    <section class="mn-hero"><div class="mn-kicker">The ultimate group movie experience</div>
    <h1>One group.<br>One perfect movie.</h1>
    <p>Bring your friends together, combine your movie tastes, and discover what everyone will love.</p>
    <div class="mn-strip"><span class="mn-chip">01 · Create a room</span><span class="mn-chip">02 · Upload ratings</span><span class="mn-chip">03 · Find your movie</span></div></section>''', unsafe_allow_html=True)


def movie_grid(recs, limit=10):
    cards = []
    for rank, (_, movie) in enumerate(recs.head(limit).iterrows(), start=1):
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
        cards.append(f'''<article class="mn-card" tabindex="0" aria-label="Movie {rank}: {safe(movie.get('movie', 'Untitled'))}">
          <div class="mn-poster">{poster}</div>
          <div class="mn-details"><div class="mn-rank">#{rank} GROUP PICK</div>
          <div class="mn-name">{safe(movie.get('movie', 'Untitled'))}</div>
          <div class="mn-meta">{safe(movie.get('year', ''))} · {safe(movie.get('genre', ''))}</div>
          <div class="mn-score">★ {score}</div>
          <div class="mn-extra">Lowest prediction: {minimum}<br>Director: {safe(movie.get('director', 'Unknown'))}</div>
          </div></article>''')
    st.markdown('<div class="mn-shelf"><h2>Your group’s movie picks</h2><p>Real posters from your movie library. Hover to expand each recommendation.</p></div><div class="mn-poster-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)



def interactive_theme():
    """Landing-page layout, vertical host sections, and collapsed settings control."""
    st.markdown("""<style>
    /* A dark cinematic canvas that fills the viewport, not a boxed hero. */
    .stApp {background:radial-gradient(ellipse 85% 65% at 88% 12%,#40151b 0%,#1c1018 40%,#09090d 80%)!important}
    [data-testid="stMainBlockContainer"] {max-width:1060px!important;padding-top:1rem!important;padding-bottom:5rem!important}
    .mn-nav {padding-top:22px!important;padding-bottom:8px!important}
    .mn-hero {min-height:55vh!important;min-height:55svh!important;background:transparent!important;box-shadow:none!important;border:0!important;border-radius:0!important;margin:0!important;padding:clamp(26px,6vw,70px) clamp(2px,3vw,32px) 6px!important}
    .mn-hero h1 {font-size:clamp(48px,7vw,90px)!important;max-width:850px;line-height:1.02!important}
    .mn-hero p {font-size:clamp(15px,1.7vw,19px)!important;max-width:560px!important}
    .mn-hero .mn-strip {display:none!important}
    .mn-landing-actions {font-size:12px;letter-spacing:.15em;color:#f4b6b8;text-transform:uppercase;font-weight:800;margin:0 0 8px}
    /* Real Streamlit buttons live directly below the hero, as the primary actions. */
    div[data-testid="stHorizontalBlock"]:has(button[key="mn-create"]) {margin-top:-6px}
    .stButton button {min-height:44px!important;border-radius:9px!important;transition:transform .18s ease,box-shadow .18s ease!important}
    .stButton button:hover {transform:translateY(-2px);box-shadow:0 9px 24px #0007}
    .stButton button[kind="primary"] {background:#e50914!important;border-color:#e50914!important;color:white!important}
    [data-testid="stVerticalBlockBorderWrapper"] {border-color:#333039!important;border-radius:16px!important}
    [data-testid="stVerticalBlockBorderWrapper"] > div {background:#15141a80!important;border-radius:16px!important}
    [data-testid="stFileUploader"] {background:#1a1b23!important;border:1px solid #383842!important;padding:12px!important}
    [data-testid="stAlert"] {border-radius:12px!important}
    /* The native Streamlit sidebar toggle remains functional and accessible. */
    [data-testid="collapsedControl"] button,[data-testid="stSidebarCollapsedControl"] button {border:1px solid #5b3135!important;border-radius:9px!important;background:#1c171b!important;min-height:39px!important;min-width:42px!important}
    [data-testid="collapsedControl"] button:after,[data-testid="stSidebarCollapsedControl"] button:after {content:'📁';font-size:17px;position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);pointer-events:none}
    [data-testid="collapsedControl"] button svg,[data-testid="stSidebarCollapsedControl"] button svg {opacity:0}
    [data-testid="stSidebar"] {background:#111116!important}
    @media(max-width:700px){.mn-hero{min-height:42svh!important;padding:26px 3px 0!important}.mn-hero h1{font-size:clamp(43px,11vw,65px)!important}.mn-navlinks{display:none!important}}
    @media(prefers-reduced-motion:reduce){.stButton button{transition:none!important}}
    </style>""", unsafe_allow_html=True)



def interactive_hero():
    st.markdown("""
    <style>
    .mn-nav {
        padding: 20px 0 0 !important;
        margin: 0 !important;
    }

    .mn-navlinks,
    .mn-kicker {
        display: none !important;
    }

    .mn-nav .mn-brand {
        color: #e50914 !important;
        font-size: clamp(54px, 6vw, 90px) !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        letter-spacing: -0.05em !important;
        line-height: 1.05 !important;
    }

    .mn-hero {
        min-height: 0 !important;
        padding: 50px 0 28px 72px !important;
        margin: 0 !important;
    }

    .mn-hero h1 {
        font-size: clamp(42px, 5vw, 74px) !important;
        font-weight: 900 !important;
        line-height: 1.05 !important;
        color: white !important;
    }

    .mn-hero p {
        font-size: 18px !important;
        color: #d1d5db !important;
        max-width: 620px !important;
        line-height: 1.7 !important;
    }

    @media (max-width: 700px) {
        .mn-hero {
            padding: 35px 0 25px 12px !important;
        }
    }
    </style>

    <div class="mn-nav">
        <div class="mn-brand">BOXD TOGETHER</div>
    </div>

    <section class="mn-hero">
        <h1>One group.<br>One perfect movie.</h1>
        <p>
            Bring your friends together. Everyone uploads their ratings.
            Boxd Together finds the films your group will love.
        </p>
    </section>
    """, unsafe_allow_html=True)



def boxd_wide_results_theme():
    """Use the available screen width and display larger poster cards."""
    st.markdown("""<style>
    /* Streamlit's default max-width leaves large empty gutters. */
    [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] .block-container,
    .main .block-container {
        max-width: none !important;
        width: 100% !important;
        padding-left: clamp(14px, 2.2vw, 44px) !important;
        padding-right: clamp(14px, 2.2vw, 44px) !important;
        box-sizing: border-box !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        max-width: none !important;
        width: 100% !important;
    }
    /* Do not restrict the hero and dashboard to a narrow central column. */
    .mn-nav, .mn-hero, .mn-shelf, .mn-poster-grid {
        width: 100% !important;
        max-width: none !important;
    }
    .mn-hero {
        padding-left: clamp(20px, 4vw, 78px) !important;
        padding-right: clamp(20px, 4vw, 78px) !important;
    }
    /* Fewer columns = larger movie artwork and readable scores. */
    .mn-poster-grid {
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: clamp(16px, 1.7vw, 28px) !important;
        padding: 22px 15px 34px !important;
        overflow: visible !important;
    }
    .mn-card {border-radius: 14px !important;overflow: visible !important}
    .mn-poster {aspect-ratio: 2 / 3 !important;border-radius: 13px 13px 0 0 !important}
    .mn-poster img {width:100% !important;height:100% !important;object-fit:contain !important}
    .mn-details {padding: 18px 17px 20px !important}
    .mn-rank {font-size: 12px !important}
    .mn-name {font-size: clamp(17px, 1.4vw, 22px) !important;min-height: 0 !important}
    .mn-meta {font-size: 13px !important}
    .mn-score {font-size: 16px !important}
    .mn-extra {font-size: 13px !important}
    .mn-shelf h2 {font-size: clamp(27px, 3vw, 42px) !important}
    .mn-shelf p {font-size: 15px !important}
    .mn-card:hover, .mn-card:focus-within {
        transform: translateY(-9px) scale(1.07) !important;
        z-index: 20 !important;
    }
    @media(max-width: 1100px) {
        .mn-poster-grid {grid-template-columns: repeat(3, minmax(0, 1fr)) !important}
    }
    @media(max-width: 760px) {
        .mn-poster-grid {grid-template-columns: repeat(2, minmax(0, 1fr)) !important;gap:12px !important;padding:12px 4px 25px !important}
        .mn-details {padding:12px !important}
        .mn-name {font-size:16px !important}
        .mn-score {font-size:14px !important}
        .mn-card:hover,.mn-card:focus-within {transform:translateY(-3px) scale(1.025) !important}
    }
    @media(max-width: 390px) {
        .mn-poster-grid {grid-template-columns: repeat(2, minmax(0, 1fr)) !important;gap:9px !important}
    }
    @media(prefers-reduced-motion:reduce){.mn-card{transition:none!important}}
    </style>""", unsafe_allow_html=True)
