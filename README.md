# Boxd Together

Boxd Together is a group movie recommendation web app built for VolHack Fall 2026.

Picking a movie with friends usually takes longer than watching the movie itself, especially when everyone has different tastes. While Letterboxd is great for tracking what individuals like, there is no built-in way to combine multiple profiles to find something a whole group will enjoy. Boxd Together solves this by taking exported Letterboxd rating CSVs from everyone in a room, training a Random Forest model on each person's rating history, and predicting how the group will react to movies none of them have seen yet.

For the full case study on the group with Arturo, Jacob, Jake, Julian, Matthew, and Sameer, methodology, and project background, refer to [background and theory on project](Volhack.pdf).

## Required Datasets

The following core Letterboxd library datasets are excluded from this repository due to GitHub file size limits. Download each file from the [Letterboxd Dataset on Kaggle](https://www.kaggle.com/datasets/gsimonx37/letterboxd) and place them inside the `data and machine learning/` directory:

- [`movies.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=movies.csv)
- [`posters.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=posters.csv)
- [`genres.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=genres.csv)
- [`actors.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=actors.csv)
- [`crew.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=crew.csv)

## How It Works

### 1. Data Processing (`pandas_group_data.py`)

The pipeline takes individual user rating CSVs and merges them with movie metadata (genres, release year, runtime, community ratings, and popularity) to build a unified dataset (`group_dataset.csv`).

### 2. Rating Prediction & Consensus (`random_forest.py`)

For each user in the group, we train a separate Random Forest Regressor based on their past ratings. We use cross-validation and out-of-fold predictions to check how well the model captures each person's taste.

Once the models predict how each person will rate unseen candidate movies, we rank the results using two main ideas:

* **Group Average:** Movies with the highest overall predicted score across everyone in the room.

* **Least Misery:** Filtering out polarizing movies where the average might be high, but at least one person in the room is predicted to hate it.

The final ranked picks are exported to `group_recommendations.csv` and displayed in the app.

### 3. Web App & Group Rooms (`app.py`, `group_rooms.py`, `boxd_group_ui.py`)

The frontend is built with Streamlit (`app.py`) and styled with a custom dark theme (`cinematic_ui.py`). A host can create a room backed by a local SQLite database (`movie_rooms.sqlite3`), share the room code, and let friends upload their Letterboxd CSV files. Once everyone is in, the app generates a poster menu of the top movie night picks and shows a breakdown of who is predicted to like what.

## Generated Plots

Running the machine learning script outputs evaluation charts and visual summaries into `data and machine learning/figures/` (along with an overview in `group_dashboard.png`):

* `1_cv_error_by_user.png` - Cross-validation error per user to see how predictable each person's taste is.

* `2_actual_vs_predicted_oof.png` - Out-of-fold actual vs. predicted ratings across the dataset.

* `3_feature_importances.png` - Which movie features (runtime, year, genres, etc.) mattered most to the models.

* `4_top_12_recommendations_heatmap.png` - Heatmap showing every group member's predicted rating for the top 12 movies.

* `5_group_avg_vs_least_misery.png` - Scatter plot comparing the group average against the lowest individual score for each movie.

* `6_predicted_rating_distributions.png` - Distribution of predicted ratings for each user.

* `7_top_10_poster_menu.png` - Poster grid of the top 10 recommended movies.

## Project Structure

```
volhack_fall26-main/
├── .devcontainer/
│   └── devcontainer.json
├── data and machine learning/
│   ├── app.py                             # Main Streamlit application
│   ├── boxd_group_ui.py                   # Group lobby interface
│   ├── cinematic_ui.py                    # Custom UI styling and layout
│   ├── group_rooms.py                     # SQLite room creation and state management
│   ├── pandas_group_data.py               # Dataset merging and cleaning script
│   ├── random_forest.py                   # Random Forest training, evaluation, and plotting
│   ├── movie_rooms.sqlite3                # Local SQLite database for room sessions
│   ├── group_dataset.csv                  # Combined user ratings and movie features
│   ├── group_recommendations.csv          # Output recommendations for the group
│   ├── group_dashboard.png                # Summary dashboard image
│   ├── *_ratings.csv                      # Sample user rating CSVs
│   └── figures/                           # Saved plots from model evaluation
├── Volhack.pdf                            # Project presentation slides & case study
└── README.md
```

## Running Locally

1. Clone the repo and navigate to the project directory:

```
git clone https://github.com/your-username/volhack_fall26.git
cd "volhack_fall26-main/data and machine learning"
```

2. Download the required Kaggle CSV files listed above and place them in the `data and machine learning/` folder.

3. Install the required Python packages:

```
pip install streamlit pandas numpy scikit-learn matplotlib seaborn requests
```

4. (Optional) Rebuild the dataset and retrain the models:

```
python pandas_group_data.py
python random_forest.py
```

5. Start the Streamlit app:

```
streamlit run app.py
```

## Contributors

* Julian Lee (jlee320@vols.utk.edu)

* Jake Laws (jlaws6@vols.utk.edu)

* Mohammad Rehan Sheik (msheik@vols.utk.edu)
