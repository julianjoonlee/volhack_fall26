"""Expand Boxd Togther to nearly full viewport width and enlarge movie results.
Run beside app.py and cinematic_ui.py. Safe to rerun; backs up both files.
"""
from pathlib import Path
from datetime import datetime
import ast
import shutil

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app.py'
UI = ROOT / 'cinematic_ui.py'
MARKER = '# BOXD_TO GTHER_WIDE_RESULTS_V1'.replace(' ', '')

STYLE = r'''

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
'''

def main():
    if not APP.is_file() or not UI.is_file():
        raise SystemExit('Place this script next to app.py and cinematic_ui.py. No files changed.')
    app = APP.read_text(encoding='utf-8')
    ui = UI.read_text(encoding='utf-8')
    if MARKER in app:
        print('Wide layout already installed. No changes made.')
        return
    if 'import cinematic_ui' not in app or 'cinematic_ui.movie_grid(recs)' not in app:
        raise SystemExit('Expected cinematic app.py with movie_grid was not found. No files changed.')
    if 'def theme():' not in ui:
        raise SystemExit('Expected cinematic_ui.py was not found. No files changed.')
    # Add last so these overrides win over both earlier cinematic and interactive styles.
    call_anchor = 'cinematic_ui.interactive_theme()' if 'cinematic_ui.interactive_theme()' in app else 'cinematic_ui.theme()'
    app = app.replace(call_anchor, call_anchor + '\ncinematic_ui.boxd_wide_results_theme()\n' + MARKER, 1)
    ui += '\n' + STYLE
    ast.parse(app)
    ast.parse(ui)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    app_backup = ROOT / f'app_before_wide_layout_{stamp}.py'
    ui_backup = ROOT / f'cinematic_ui_before_wide_layout_{stamp}.py'
    shutil.copy2(APP, app_backup)
    shutil.copy2(UI, ui_backup)
    try:
        UI.write_text(ui, encoding='utf-8')
        APP.write_text(app, encoding='utf-8')
    except Exception:
        shutil.copy2(app_backup, APP)
        shutil.copy2(ui_backup, UI)
        raise
    print('Done! Boxd Togther now uses the available width and larger movie cards.')
    print('Backups:', app_backup.name, ui_backup.name)
    print('Restart: python -m streamlit run app.py')

if __name__ == '__main__':
    main()
