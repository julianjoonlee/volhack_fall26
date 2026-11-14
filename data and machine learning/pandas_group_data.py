import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Define your input files
rating_files = {
    'arturo_rating': 'arturo_ratings.csv',
    'julian_rating': 'julian_ratings.csv',
    'sameer_rating': 'sameer_ratings.csv'
}

# 2. Load the library files
print("Loading library datasets...")
movies = pd.read_csv('movies.csv')
crew = pd.read_csv('crew.csv')
actors = pd.read_csv('actors.csv')
genres = pd.read_csv('genres.csv')
posters = pd.read_csv('posters.csv')

# Clean up types to ensure accurate matching
movies['date'] = pd.to_numeric(movies['date'], errors='coerce')
movies['name_clean'] = movies['name'].astype(str).str.strip().str.lower()

# If movies.csv has duplicate (name, year) entries, keep the most popular/highest rated one
movies = movies.sort_values('rating', ascending=False).drop_duplicates(subset=['name_clean', 'date'])

# 3. Pre-process library features by movie ID so merges don't create duplicate rows
# Grab the first listed Director for each movie ID
directors = (
    crew[crew['role'] == 'Director']
    .drop_duplicates(subset=['id'], keep='first')[['id', 'name']]
    .rename(columns={'name': 'director'})
)

# Grab the first listed Actor for each movie ID
first_actors = (
    actors.drop_duplicates(subset=['id'], keep='first')[['id', 'name']]
    .rename(columns={'name': 'first_actor'})
)

# Combine all genres for a movie ID into a comma-separated string (or use .drop_duplicates() for just the first genre)
movie_genres = (
    genres.groupby('id')['genre']
    .apply(lambda x: ', '.join(x.dropna().astype(str)))
    .reset_index()
)

# Grab the poster link for each movie ID
movie_posters = (
    posters.drop_duplicates(subset=['id'], keep='first')[['id', 'link']]
    .rename(columns={'link': 'poster_link'})
)

# 4. Load and combine all friends' Letterboxd rating files
print("Processing Letterboxd rating files...")
user_dfs = []

for user_col, filepath in rating_files.items():
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        # Keep only the columns needed for matching and the rating
        df = df[['Name', 'Year', 'Rating']].copy()
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        
        # If a user rated the same movie twice, keep their latest rating
        df = df.drop_duplicates(subset=['Name', 'Year'], keep='last')
        
        # Rename Rating column to the specific person's name
        df = df.rename(columns={'Rating': user_col})
        df = df.set_index(['Name', 'Year'])
        user_dfs.append(df)
    else:
        print(f"Warning: {filepath} not found. Skipping {user_col}.")

# Concatenate along columns to build the group rating matrix
group_ratings = pd.concat(user_dfs, axis=1).reset_index()
group_ratings['name_clean'] = group_ratings['Name'].astype(str).str.strip().str.lower()

# 5. Link Letterboxd movies to the library IDs and attach features
group_dataset = pd.merge(
    group_ratings,
    movies[['id', 'name_clean', 'date', 'minute', 'rating']],
    left_on=['name_clean', 'Year'],
    right_on=['name_clean', 'date'],
    how='left'
)

group_dataset = group_dataset.merge(directors, on='id', how='left')
group_dataset = group_dataset.merge(first_actors, on='id', how='left')
group_dataset = group_dataset.merge(movie_genres, on='id', how='left')
group_dataset = group_dataset.merge(movie_posters, on='id', how='left')

# 6. Format final columns for your ML dataset
group_dataset = group_dataset.rename(columns={
    'Name': 'movie',
    'Year': 'year',
    'rating': 'global_avg_rating'
})

user_cols = [col for col in rating_files.keys() if col in group_dataset.columns]
final_columns = [
    'id', 'movie', 'year', 'director', 'first_actor',
    'genre', 'minute', 'global_avg_rating', 'poster_link'
] + user_cols

group_dataset = group_dataset[final_columns]

# 7. Save to CSV
group_dataset.to_csv('group_dataset.csv', index=False)
print(f"Saved group_dataset.csv with {len(group_dataset)} unique movies!")
print(group_dataset.head())

sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Movie Group Ratings Dashboard', fontsize=18, fontweight='bold', y=0.98)

# 1. Average Rating & Movie Count per Person
avg_ratings = group_dataset[user_cols].mean().sort_values(ascending=True)
rating_counts = group_dataset[user_cols].count()[avg_ratings.index]
clean_names = [col.replace('_rating', '').capitalize() for col in avg_ratings.index]

bars = axes[0, 0].barh(clean_names, avg_ratings.values, color=sns.color_palette("viridis", len(user_cols)))
axes[0, 0].set_title('Average Rating & Total Watched per Person', fontweight='bold')
axes[0, 0].set_xlim(0, 5.5)
axes[0, 0].set_xlabel('Average Star Rating')

for bar, count in zip(bars, rating_counts):
    width = bar.get_width()
    axes[0, 0].text(
        width + 0.1, bar.get_y() + bar.get_height() / 2,
        f'{width:.2f} ★ ({count} movies)',
        va='center', fontsize=10
    )

# 2. Taste Similarity Heatmap (Correlation Matrix)
corr = group_dataset[user_cols].corr()
corr.index = [col.replace('_rating', '').capitalize() for col in corr.index]
corr.columns = [col.replace('_rating', '').capitalize() for col in corr.columns]

sns.heatmap(
    corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1,
    center=0, fmt='.2f', ax=axes[0, 1], cbar_kws={'label': 'Correlation'}
)
axes[0, 1].set_title('Taste Similarity (Rating Correlation)', fontweight='bold')

# 3. Rating Distributions (Who is the harshest critic?)
melted_ratings = group_dataset[user_cols].melt(var_name='User', value_name='Rating').dropna()
melted_ratings['User'] = melted_ratings['User'].str.replace('_rating', '').str.capitalize()

sns.boxplot(
    data=melted_ratings, x='User', y='Rating',
    palette='pastel', ax=axes[1, 0], width=0.4
)
sns.stripplot(
    data=melted_ratings, x='User', y='Rating',
    color='black', alpha=0.25, jitter=0.15, ax=axes[1, 0], size=4
)
axes[1, 0].set_title('Rating Spread by User', fontweight='bold')
axes[1, 0].set_ylim(0, 5.5)
axes[1, 0].set_xlabel('')

# 4. Top 10 Most Watched Genres in the Group
genres_exploded = (
    group_dataset['genre']
    .dropna()
    .str.split(', ')
    .explode()
)
top_genres = genres_exploded.value_counts().head(10)

sns.barplot(
    x=top_genres.values, y=top_genres.index,
    palette='magma', ax=axes[1, 1]
)
axes[1, 1].set_title('Top 10 Most Watched Genres in Dataset', fontweight='bold')
axes[1, 1].set_xlabel('Number of Movies')
axes[1, 1].set_ylabel('')

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig('group_dashboard.png', dpi=300)
print("Saved visualization to group_dashboard.png!")
plt.show()