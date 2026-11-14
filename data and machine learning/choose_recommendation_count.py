"""Add a recommendation-count selector to Boxd Togther's results.
Run once beside app.py and cinematic_ui.py. Backs up both files.
"""
from pathlib import Path
from datetime import datetime
import ast
import shutil

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app.py'
UI = ROOT / 'cinematic_ui.py'
MARKER = '# BOXD_RECOMMENDATION_COUNT_V1'

def main():
    if not APP.is_file() or not UI.is_file():
        raise SystemExit('Place this script beside app.py and cinematic_ui.py. Nothing changed.')
    app = APP.read_text(encoding='utf-8')
    ui = UI.read_text(encoding='utf-8')
    if MARKER in app:
        print('Recommendation selector is already installed. No changes needed.')
        return
    if 'cinematic_ui.movie_grid(recs)' not in app:
        raise SystemExit('Expected cinematic recommendation grid not found in app.py. Nothing changed.')
    if 'def movie_grid(recs):' not in ui or 'recs.head(10).iterrows()' not in ui:
        raise SystemExit('Expected cinematic_ui.movie_grid not found. Nothing changed.')

    # The selection is only displayed once recommendations have been generated.
    selector = '''                # BOXD_RECOMMENDATION_COUNT_V1
                count_options = [n for n in (5, 10, 15, 20, 25, 50) if n <= len(recs)]
                if len(recs) not in count_options:
                    count_options.append(len(recs))
                count_options = sorted(set(count_options))
                default_count = 10 if 10 in count_options else len(recs)
                show_count = st.selectbox(
                    'How many movie recommendations would you like to see?',
                    options=count_options,
                    index=count_options.index(default_count),
                    format_func=lambda n: f'All {n} movies' if n == len(recs) else f'Top {n} movies',
                    key='boxd_recommendation_count',
                )
                cinematic_ui.movie_grid(recs, show_count)
'''
    app = app.replace('                cinematic_ui.movie_grid(recs)\n', selector, 1)
    # Keep the table and top-N download consistent with the selection.
    app = app.replace('st.dataframe(recs.head(10),', 'st.dataframe(recs.head(show_count),', 1)
    app = app.replace("st.download_button('Download top 10 CSV', recs.head(10).to_csv(index=False).encode('utf-8'),\n                               'top_10_recommendations.csv', 'text/csv')", "st.download_button(f'Download top {show_count} CSV', recs.head(show_count).to_csv(index=False).encode('utf-8'),\n                               f'top_{show_count}_recommendations.csv', 'text/csv')", 1)
    ui = ui.replace('def movie_grid(recs):', 'def movie_grid(recs, limit=10):', 1)
    ui = ui.replace('recs.head(10).iterrows()', 'recs.head(limit).iterrows()', 1)
    ui = ui.replace('Top picks for your group</h2>', 'Your group’s movie picks</h2>', 1)
    ast.parse(app)
    ast.parse(ui)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    app_backup = ROOT / f'app_before_rec_count_{stamp}.py'
    ui_backup = ROOT / f'cinematic_ui_before_rec_count_{stamp}.py'
    shutil.copy2(APP, app_backup)
    shutil.copy2(UI, ui_backup)
    try:
        APP.write_text(app, encoding='utf-8')
        UI.write_text(ui, encoding='utf-8')
    except Exception:
        shutil.copy2(app_backup, APP)
        shutil.copy2(ui_backup, UI)
        raise
    print('Done! Recommendation count selector installed.')
    print('Backups:', app_backup.name, ui_backup.name)
    print('Restart with: python -m streamlit run app.py')

if __name__ == '__main__':
    main()
