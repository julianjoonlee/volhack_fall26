import os
import matplotlib
matplotlib.use('Agg')  # Prevents Linux GUI window from hanging the script
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from urllib.request import Request, urlopen
from PIL import Image
from io import BytesIO
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

# Create a dedicated directory for all figure files
FIG_DIR = 'figures'
os.makedirs(FIG_DIR, exist_ok=True)

# 1. Load your compiled group_dataset and the full library files
print("[1/7] Loading group_dataset and movies.csv...")
group_df = pd.read_csv('group_dataset.csv')
movies = pd.read_csv('movies.csv')

# SPEED FIX 1: Filter movies.csv FIRST before merging millions of crew/actor/genre rows!
movies['date'] = pd.to_numeric(movies['date'], errors='coerce')
movies['minute'] = pd.to_numeric(movies['minute'], errors='coerce')
movies['rating'] = pd.to_numeric(movies['rating'], errors='coerce')

# Keep only feature-length movies (40 to 300 mins) that actually have a global rating
valid_movies = movies.dropna(subset=['id', 'date', 'minute', 'rating']).copy()
valid_movies = valid_movies[(valid_movies['minute'] >= 40) & (valid_movies['minute'] <= 300)]

# Remove movies the group already watched right away
watched_ids = set(group_df['id'].dropna().unique())
valid_movies = valid_movies[~valid_movies['id'].isin(watched_ids)].copy()

# Keep top 50,000 highest-rated candidate movies so ML prediction is fast
valid_movies = valid_movies.sort_values('rating', ascending=False).head(50000)
candidate_ids = set(valid_movies['id'])
print(f"      -> Filtered candidate pool to {len(valid_movies):,} unwatched feature films.")

# 2. Load & filter auxiliary library files ONLY for those candidate IDs
print("[2/7] Loading and linking crew, actors, genres, and posters...")
crew = pd.read_csv('crew.csv')
crew = crew[(crew['id'].isin(candidate_ids)) & (crew['role'] == 'Director')]
directors = crew.drop_duplicates('id')[['id', 'name']].rename(columns={'name': 'director'})

actors = pd.read_csv('actors.csv')
actors = actors[actors['id'].isin(candidate_ids)]
first_actors = actors.drop_duplicates('id')[['id', 'name']].rename(columns={'name': 'first_actor'})

genres = pd.read_csv('genres.csv')
genres = genres[genres['id'].isin(candidate_ids)].dropna(subset=['genre'])
movie_genres = genres.groupby('id')['genre'].agg(', '.join).reset_index()

posters = pd.read_csv('posters.csv')
posters = posters[posters['id'].isin(candidate_ids)]
movie_posters = posters.drop_duplicates('id')[['id', 'link']].rename(columns={'link': 'poster_link'})

unwatched_catalog = (
    valid_movies[['id', 'name', 'date', 'minute', 'rating']]
    .rename(columns={'name': 'movie', 'date': 'year', 'rating': 'global_avg_rating'})
    .merge(directors, on='id', how='left')
    .merge(first_actors, on='id', how='left')
    .merge(movie_genres, on='id', how='left')
    .merge(movie_posters, on='id', how='left')
    .reset_index(drop=True)
)

# 3. Feature Engineering: Multi-Hot Encode Genres
print("[3/7] Encoding genres and features...")
vectorizer = CountVectorizer(tokenizer=lambda x: x.split(', '), token_pattern=None)
all_genres = pd.concat([group_df['genre'], unwatched_catalog['genre']]).fillna('Unknown')
vectorizer.fit(all_genres)

train_genres = vectorizer.transform(group_df['genre'].fillna('Unknown')).toarray()
cand_genres = vectorizer.transform(unwatched_catalog['genre'].fillna('Unknown')).toarray()

feature_names = ['Release Year', 'Runtime (Min)', 'Global Rating', 'Director Affinity', 'Actor Affinity'] + [
    f"Genre: {g}" for g in vectorizer.get_feature_names_out()
]

# 4. Validate (5-Fold CV) & Train a personalized ML model for each friend (including Sameer!)
print("[4/7] Running 5-Fold Cross-Validation & Training Random Forests...")
user_cols = [
    'arturo_rating', 'jacob_rating', 'jake_rating',
    'julian_rating', 'matthew_rating', 'sameer_rating'
]
user_cols = [c for c in user_cols if c in group_df.columns]

predicted_cols = []
validation_metrics = []
oof_records = []
feature_importances = np.zeros(len(feature_names))
valid_user_count = 0

for user in user_cols:
    valid_mask = (
        group_df[user].notna() &
        group_df['year'].notna() &
        group_df['minute'].notna() &
        group_df['global_avg_rating'].notna()
    )
    user_train = group_df[valid_mask].copy().reset_index(drop=True)
    user_genres = train_genres[valid_mask]
    
    if len(user_train) < 5:
        print(f"      Skipping {user} (not enough rated movies to train).")
        continue
        
    y_all = user_train[user].values
    clean_name = user.replace('_rating', '').capitalize()
    
    # --- A. Leak-Free Cross-Validation ---
    n_splits = min(5, len(user_train))
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    oof_preds = np.zeros(len(user_train))
    
    for train_idx, val_idx in kf.split(user_train):
        fold_train = user_train.iloc[train_idx]
        fold_val = user_train.iloc[val_idx]
        fold_mean = fold_train[user].mean()
        
        f_dir = fold_train.groupby('director')[user].agg(['count', 'mean'])
        f_dir_map = (f_dir['count'] * f_dir['mean'] + 3 * fold_mean) / (f_dir['count'] + 3)
        
        f_act = fold_train.groupby('first_actor')[user].agg(['count', 'mean'])
        f_act_map = (f_act['count'] * f_act['mean'] + 3 * fold_mean) / (f_act['count'] + 3)
        
        X_tr = np.hstack([
            fold_train[['year', 'minute', 'global_avg_rating']].values,
            fold_train['director'].map(f_dir_map).fillna(fold_mean).values.reshape(-1, 1),
            fold_train['first_actor'].map(f_act_map).fillna(fold_mean).values.reshape(-1, 1),
            user_genres[train_idx]
        ])
        
        X_va = np.hstack([
            fold_val[['year', 'minute', 'global_avg_rating']].values,
            fold_val['director'].map(f_dir_map).fillna(fold_mean).values.reshape(-1, 1),
            fold_val['first_actor'].map(f_act_map).fillna(fold_mean).values.reshape(-1, 1),
            user_genres[val_idx]
        ])
        
        cv_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
        cv_model.fit(X_tr, fold_train[user].values)
        oof_preds[val_idx] = cv_model.predict(X_va)
        
    mae = mean_absolute_error(y_all, oof_preds)
    rmse = root_mean_squared_error(y_all, oof_preds)
    validation_metrics.append({
        'User': clean_name,
        'Movies': len(user_train),
        'MAE': round(mae, 3),
        'RMSE': round(rmse, 3)
    })
    
    for actual, pred in zip(y_all, oof_preds):
        oof_records.append({'User': clean_name, 'Actual': actual, 'Predicted': pred})
        
    print(f"      [{clean_name}] {n_splits}-Fold CV -> MAE: {mae:.3f} ★ | RMSE: {rmse:.3f} ★ ({len(user_train)} movies)")

    # --- B. Train Final Model on 100% of User Data & Predict Catalog ---
    global_user_mean = y_all.mean()
    dir_stats = user_train.groupby('director')[user].agg(['count', 'mean'])
    dir_Target = (dir_stats['count'] * dir_stats['mean'] + 3 * global_user_mean) / (dir_stats['count'] + 3)
    
    act_stats = user_train.groupby('first_actor')[user].agg(['count', 'mean'])
    act_Target = (act_stats['count'] * act_stats['mean'] + 3 * global_user_mean) / (act_stats['count'] + 3)
    
    X_train = np.hstack([
        user_train[['year', 'minute', 'global_avg_rating']].values,
        user_train['director'].map(dir_Target).fillna(global_user_mean).values.reshape(-1, 1),
        user_train['first_actor'].map(act_Target).fillna(global_user_mean).values.reshape(-1, 1),
        user_genres
    ])
    
    X_cand = np.hstack([
        unwatched_catalog[['year', 'minute', 'global_avg_rating']].values,
        unwatched_catalog['director'].map(dir_Target).fillna(global_user_mean).values.reshape(-1, 1),
        unwatched_catalog['first_actor'].map(act_Target).fillna(global_user_mean).values.reshape(-1, 1),
        cand_genres
    ])
    
    model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    model.fit(X_train, y_all)
    
    feature_importances += model.feature_importances_
    valid_user_count += 1
    
    pred_col = f"{user.replace('_rating', '')}_pred"
    unwatched_catalog[pred_col] = np.round(model.predict(X_cand), 2)
    predicted_cols.append(pred_col)

# 5. Calculate Group Consensus Scores
print("[5/7] Ranking Group Consensus Recommendations...")
unwatched_catalog['group_pred_avg'] = unwatched_catalog[predicted_cols].mean(axis=1).round(2)
unwatched_catalog['least_misery_score'] = unwatched_catalog[predicted_cols].min(axis=1).round(2)

recommendations = unwatched_catalog.sort_values(
    by=['group_pred_avg', 'least_misery_score', 'global_avg_rating'],
    ascending=False
)

output_cols = [
    'id', 'movie', 'year', 'director', 'first_actor', 'genre',
    'global_avg_rating', 'group_pred_avg', 'least_misery_score'
] + predicted_cols + ['poster_link']

top_100 = recommendations[output_cols].head(100)
top_100.to_csv('group_recommendations.csv', index=False)

val_df = pd.DataFrame(validation_metrics)
print("\nValidation Summary Table:")
print(val_df.to_string(index=False))

print("\nTop 10 Recommended Movies for Movie Night:")
print(top_100[['movie', 'year', 'director', 'group_pred_avg', 'least_misery_score']].head(10).to_string(index=False))


# ==============================================================================
# 6. SAVE EACH FIGURE AS ITS OWN STANDALONE FILE IN 'figures/'
# ==============================================================================
print(f"\n[6/7] Generating individual figure files inside '{FIG_DIR}/'...")
sns.set_theme(
    style="whitegrid",
    rc={
        'font.size': 15,
        'axes.titlesize': 20,
        'axes.labelsize': 17,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'legend.fontsize': 14,
        'legend.title_fontsize': 15
    }
)

# --- Figure 1: Cross-Validation Error (MAE vs RMSE) ---
fig1, ax1 = plt.subplots(figsize=(11, 7))
val_melted = val_df.melt(id_vars='User', value_vars=['MAE', 'RMSE'], var_name='Metric', value_name='Stars Error')
sns.barplot(data=val_melted, x='User', y='Stars Error', hue='Metric', palette='muted', ax=ax1)
ax1.set_title('5-Fold Cross-Validation Error by User (Lower is Better)', fontweight='bold', fontsize=20, pad=12)
ax1.set_ylabel('Prediction Error (Stars)', fontsize=17, fontweight='bold')
ax1.set_xlabel('')
ax1.tick_params(axis='both', labelsize=15)
ax1.set_ylim(0, val_melted['Stars Error'].max() * 1.15)
for container in ax1.containers:
    ax1.bar_label(container, fmt='%.2f', padding=4, fontsize=14, fontweight='bold')
plt.tight_layout()
fig1_path = os.path.join(FIG_DIR, '1_cv_error_by_user.png')
fig1.savefig(fig1_path, dpi=300)
plt.close(fig1)
print(f"      -> Saved {fig1_path}")

# --- Figure 2: Out-of-Fold Actual vs. Predicted Ratings Scatter Plot ---
fig2, ax2 = plt.subplots(figsize=(10, 7))
oof_df = pd.DataFrame(oof_records)
sns.scatterplot(data=oof_df, x='Actual', y='Predicted', hue='User', alpha=0.7, s=90, palette='deep', ax=ax2)
ax2.plot([0.5, 5.0], [0.5, 5.0], 'r--', lw=2.5, label='Perfect Prediction')
ax2.set_title('Out-of-Fold Validation: Actual vs. Predicted Ratings', fontweight='bold', fontsize=20, pad=12)
ax2.set_xlabel('Actual Letterboxd Rating', fontsize=17, fontweight='bold')
ax2.set_ylabel('Model Predicted Rating', fontsize=17, fontweight='bold')
ax2.tick_params(axis='both', labelsize=15)
ax2.set_xlim(0.3, 5.2)
ax2.set_ylim(0.3, 5.2)
ax2.legend(loc='upper left', fontsize=13, title_fontsize=14)
plt.tight_layout()
fig2_path = os.path.join(FIG_DIR, '2_actual_vs_predicted_oof.png')
fig2.savefig(fig2_path, dpi=300)
plt.close(fig2)
print(f"      -> Saved {fig2_path}")

# --- Figure 3: Top 12 Most Influential Features ---
fig3, ax3 = plt.subplots(figsize=(11, 7))
avg_importances = feature_importances / max(valid_user_count, 1)
feat_df = pd.DataFrame({'Feature': feature_names, 'Importance': avg_importances})
feat_df = feat_df.sort_values('Importance', ascending=False).head(12)
sns.barplot(data=feat_df, x='Importance', y='Feature', palette='viridis', ax=ax3)
ax3.set_title('Top 12 Most Influential Features in Random Forest Models', fontweight='bold', fontsize=20, pad=12)
ax3.set_xlabel('Relative Feature Importance', fontsize=17, fontweight='bold')
ax3.set_ylabel('')
ax3.tick_params(axis='both', labelsize=15)
plt.tight_layout()
fig3_path = os.path.join(FIG_DIR, '3_feature_importances.png')
fig3.savefig(fig3_path, dpi=300)
plt.close(fig3)
print(f"      -> Saved {fig3_path}")

# --- Figure 4: Top 12 Movie Recommendations Heatmap ---
fig4, ax4 = plt.subplots(figsize=(14, 8))
top_12 = top_100.head(12).copy()
top_12['Movie_Label'] = top_12['movie'] + " (" + top_12['year'].astype(int).astype(str) + ")"
heatmap_data = top_12.set_index('Movie_Label')[predicted_cols + ['group_pred_avg', 'least_misery_score']]
heatmap_data.columns = [c.replace('_pred', '').capitalize() for c in predicted_cols] + ['Group Avg', 'Least Misery']
sns.heatmap(
    heatmap_data, annot=True, fmt='.2f', cmap='YlGnBu',
    annot_kws={'size': 14, 'weight': 'bold'},
    cbar_kws={'label': 'Predicted Stars'}, ax=ax4
)
ax4.set_title('Top 12 Movie Recommendations: Individual Breakdown', fontweight='bold', fontsize=20, pad=12)
ax4.set_ylabel('')
ax4.tick_params(axis='x', labelsize=14)
ax4.tick_params(axis='y', labelsize=14)
cbar = ax4.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.set_label('Predicted Stars', size=16, weight='bold')
plt.tight_layout()
fig4_path = os.path.join(FIG_DIR, '4_top_12_recommendations_heatmap.png')
fig4.savefig(fig4_path, dpi=300)
plt.close(fig4)
print(f"      -> Saved {fig4_path}")

# --- Figure 5: Group Average vs. Least Misery Frontier ---
fig5, ax5 = plt.subplots(figsize=(11, 7))
top_500_pool = recommendations.head(500)
sns.scatterplot(
    data=top_500_pool, x='group_pred_avg', y='least_misery_score',
    hue='global_avg_rating', size='global_avg_rating', palette='magma',
    sizes=(40, 180), alpha=0.8, ax=ax5
)
for _, row in top_100.head(5).iterrows():
    ax5.annotate(
        row['movie'],
        (row['group_pred_avg'], row['least_misery_score']),
        xytext=(6, 6), textcoords='offset points', fontsize=13, fontweight='bold'
    )
ax5.set_title('Top 500 Candidates: Group Average vs. Least Misery Score', fontweight='bold', fontsize=20, pad=12)
ax5.set_xlabel('Predicted Group Average (Utilitarian Score)', fontsize=17, fontweight='bold')
ax5.set_ylabel('Minimum Friend Rating (Least Misery Score)', fontsize=17, fontweight='bold')
ax5.tick_params(axis='both', labelsize=15)
ax5.legend(fontsize=13, title_fontsize=14)
plt.tight_layout()
fig5_path = os.path.join(FIG_DIR, '5_group_avg_vs_least_misery.png')
fig5.savefig(fig5_path, dpi=300)
plt.close(fig5)
print(f"      -> Saved {fig5_path}")

# --- Figure 6: Predicted Rating Distribution KDE ---
fig6, ax6 = plt.subplots(figsize=(11, 7))
sample_size = min(5000, len(unwatched_catalog))
cand_melted = unwatched_catalog[predicted_cols].sample(n=sample_size, random_state=42).melt(
    var_name='User', value_name='Predicted Rating'
)
cand_melted['User'] = cand_melted['User'].str.replace('_pred', '').str.capitalize()
sns.kdeplot(
    data=cand_melted, x='Predicted Rating', hue='User',
    fill=True, common_norm=False, alpha=0.3, palette='tab10', ax=ax6
)
ax6.set_title('Distribution of Predicted Ratings on Unwatched Movies', fontweight='bold', fontsize=20, pad=12)
ax6.set_xlabel('Predicted Star Rating', fontsize=17, fontweight='bold')
ax6.set_ylabel('Density', fontsize=17, fontweight='bold')
ax6.tick_params(axis='both', labelsize=15)
ax6.set_xlim(0.5, 5.0)
plt.setp(ax6.get_legend().get_texts(), fontsize='14')
plt.setp(ax6.get_legend().get_title(), fontsize='15')
plt.tight_layout()
fig6_path = os.path.join(FIG_DIR, '6_predicted_rating_distributions.png')
fig6.savefig(fig6_path, dpi=300)
plt.close(fig6)
print(f"      -> Saved {fig6_path}")


# ==============================================================================
# 7. SAVE TOP 10 MOVIE NIGHT POSTER MENU IN 'figures/'
# ==============================================================================
print("[7/7] Downloading posters for Top 10 Movie Night Menu...")
fig_posters, ax_posters = plt.subplots(2, 5, figsize=(22, 12))
fig_posters.patch.set_facecolor('#14181c')
fig_posters.suptitle(
    'TOP 10 RECOMMENDED MOVIES FOR MOVIE NIGHT',
    fontsize=28, fontweight='bold', color='white', y=0.97
)

top_10_movies = top_100.head(10).reset_index(drop=True)

for idx, row in top_10_movies.iterrows():
    r, c = divmod(idx, 5)
    ax = ax_posters[r, c]
    ax.set_facecolor('#14181c')
    
    poster_loaded = False
    if pd.notna(row['poster_link']) and str(row['poster_link']).startswith('http'):
        try:
            req = Request(str(row['poster_link']), headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=3) as response:
                img_data = response.read()
                img = Image.open(BytesIO(img_data)).convert('RGB')
                ax.imshow(img)
                poster_loaded = True
        except Exception:
            poster_loaded = False
            
    if not poster_loaded:
        ax.text(
            0.5, 0.5, f"{row['movie']}\n({int(row['year'])})",
            color='white', ha='center', va='center', fontsize=16, fontweight='bold', wrap=True
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    ax.axis('off')
    title_short = row['movie'] if len(str(row['movie'])) <= 22 else str(row['movie'])[:19] + '...'
    ax.set_title(
        f"#{idx+1}: {title_short} ({int(row['year'])})\n"
        f"★ Group Avg: {row['group_pred_avg']:.2f} | Min: {row['least_misery_score']:.2f}",
        color='#00e054', fontsize=13.5, fontweight='bold', pad=10
    )

plt.tight_layout(rect=[0, 0, 1, 0.93])
poster_path = os.path.join(FIG_DIR, '7_top_10_poster_menu.png')
fig_posters.savefig(poster_path, dpi=250, facecolor=fig_posters.get_facecolor())
plt.close(fig_posters)
print(f"      -> Saved {poster_path}! All done!")