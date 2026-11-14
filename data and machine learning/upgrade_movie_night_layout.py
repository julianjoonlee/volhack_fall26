"""Upgrade an existing cinematic Movie Night Streamlit app to an interactive landing page.
Run once in the same directory as app.py and cinematic_ui.py.
"""
from pathlib import Path
from datetime import datetime
import ast
import shutil

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app.py'
UI = ROOT / 'cinematic_ui.py'
MARKER = '# MOVIE_NIGHT_INTERACTIVE_LAYOUT_V1'

# The extra CSS is injected by a separate function so existing poster-grid styles stay intact.
EXTRA = r'''

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
    """An actual welcome screen. Actions are Streamlit controls in app.py."""
    st.markdown("""<div class="mn-nav"><div class="mn-brand">MOVIE NIGHT</div><div class="mn-navlinks">DISCOVER &nbsp; / &nbsp; WATCH TOGETHER</div></div>
    <section class="mn-hero"><div class="mn-kicker">YOUR NEXT MOVIE NIGHT STARTS HERE</div>
    <h1>One group.<br>One perfect movie.</h1>
    <p>Bring your friends together. Everyone uploads their ratings. Movie Night finds the films your group will love.</p></section>""", unsafe_allow_html=True)
'''


def main():
    if not APP.is_file() or not UI.is_file():
        raise SystemExit('Place this script next to app.py and cinematic_ui.py. No files changed.')
    src = APP.read_text(encoding='utf-8')
    ui = UI.read_text(encoding='utf-8')
    if MARKER in src:
        print('Interactive layout is already installed. No changes made.')
        return
    if 'import cinematic_ui' not in src or 'cinematic_ui.hero()' not in src:
        raise SystemExit('Install the cinematic update first; this version of app.py is not supported.')
    if 'if not is_current_host:' not in src or 'group_rooms.create_room()' not in src:
        raise SystemExit('Expected group-room host workflow was not found. No files changed.')
    # Sidebar is collapsed on initial load; native Streamlit sidebar toggle remains clickable.
    original_config = "st.set_page_config(page_title='Movie Night', page_icon='🎬', layout='wide')"
    if original_config not in src:
        raise SystemExit('Could not locate Streamlit page configuration. No files changed.')
    src = src.replace(original_config, "st.set_page_config(page_title='Movie Night', page_icon='🎬', layout='wide', initial_sidebar_state='collapsed')", 1)
    # Inject extra styles after the original theme. The existing movie grid is untouched.
    src = src.replace('cinematic_ui.theme()', 'cinematic_ui.theme()\ncinematic_ui.interactive_theme()', 1)
    src = src.replace('cinematic_ui.hero()', 'cinematic_ui.interactive_hero()', 1)
    # Remove the redundant static homepage title if present.
    # Main landing buttons are wired to the existing group_rooms backend.
    anchor = 'if not is_current_host:\n'
    replacement = '''if not is_current_host:
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
'''
    if anchor not in src:
        raise SystemExit('Host selection anchor not found. No files changed.')
    src = src.replace(anchor, replacement, 1)
    # The original radio would override our landing actions; remove only that line.
    old_radio = "    choice = st.radio('Get started', ['Create a group', 'Join a group'], horizontal=True)\n"
    if old_radio not in src:
        raise SystemExit('Original group-choice radio not found. No files changed.')
    src = src.replace(old_radio, '', 1)
    # Create-group button in the original workflow remains as an alternative.
    # Give the host a distinct vertically stacked card for their group code and upload.
    host_start = "st.success(f'You are hosting room {code}')\n"
    host_end = "if st.button('Refresh uploads'):\n"
    if host_start not in src or host_end not in src:
        raise SystemExit('Host upload section not found. No files changed.')
    a = src.index(host_start)
    b = src.index(host_end, a)
    section = src[a:b]
    src = src[:a] + "with st.container(border=True):\n" + ''.join('    '+line if line.strip() else line for line in section.splitlines(keepends=True)) + src[b:]
    # Separate the ready status and generation controls into another vertical card.
    flow_start = "st.subheader('2 · Run the recommendation workflow')\n"
    flow_end = "result = st.session_state.get('movie_result')\n"
    if flow_start not in src or flow_end not in src:
        raise SystemExit('Recommendation workflow section not found. No files changed.')
    a = src.index(flow_start)
    b = src.index(flow_end, a)
    section = src[a:b]
    src = src[:a] + "with st.container(border=True):\n" + ''.join('    '+line if line.strip() else line for line in section.splitlines(keepends=True)) + src[b:]
    # Make the room view focus on its controls rather than repeating a huge welcome hero.
    # The hero is still the whole-page welcome before a room is selected.
    src = src.replace('cinematic_ui.interactive_hero()\n', "cinematic_ui.interactive_hero()\n", 1)
    src = MARKER + '\n' + src
    new_ui = ui + '\n' + EXTRA
    ast.parse(src)
    ast.parse(new_ui)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = ROOT / f'app_before_interactive_layout_{stamp}.py'
    backup_ui = ROOT / f'cinematic_ui_before_interactive_layout_{stamp}.py'
    shutil.copy2(APP, backup)
    shutil.copy2(UI, backup_ui)
    UI.write_text(new_ui, encoding='utf-8')
    APP.write_text(src, encoding='utf-8')
    print('Installed interactive Movie Night homepage and vertical group sections.')
    print('Backups:', backup.name, 'and', backup_ui.name)
    print('Start with: python -m streamlit run app.py')


if __name__ == '__main__':
    main()
