# volhack_fall26

You use here! https://boxdtogether.streamlit.app/

A machine learning and data exploration web application built with **Streamlit** using Letterboxd movie data for **VolHacks Fall 2026**.

For the full case study, methodology, and project background, refer to [background and theory on project](Volhack.pdf).

## Prerequisites

Before setting up the project, make sure you have the following installed:

- **Python 3.9+** ([Download Python](https://www.python.org/downloads/))
- **pip** (Python package installer)
- **Git** ([Download Git](https://git-scm.com/))

## Required Datasets

The following core Letterboxd library datasets are excluded from this repository due to GitHub file size limits. Download each file from the [Letterboxd Dataset on Kaggle](https://www.kaggle.com/datasets/gsimonx37/letterboxd) and place them inside the `data and machine learning/` directory:

- [`movies.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=movies.csv)
- [`posters.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=posters.csv)
- [`genres.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=genres.csv)
- [`actors.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=actors.csv)
- [`crew.csv`](https://www.kaggle.com/datasets/gsimonx37/letterboxd?select=crew.csv)

## Installation & Setup

### 1. Clone the Repository

Open your terminal and clone the repository to your local machine:

```bash
git clone [https://github.com/julianjoonlee/volhack_fall26.git](https://github.com/julianjoonlee/volhack_fall26.git)
cd volhack_fall26
```

### 2. Create a Virtual Environment (Recommended)

Creating a virtual environment keeps your dependencies isolated:

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt / PowerShell):**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Required Packages

If using `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install the core data science, machine learning, and Streamlit packages directly:

```bash
pip install streamlit pandas numpy scikit-learn matplotlib seaborn plotly requests pillow
```

### 4. Verify Dataset Placement

Ensure the 5 CSV files downloaded from Kaggle are placed inside the `data and machine learning/` folder before launching the app:

```text
volhack_fall26/
├── data and machine learning/
│   ├── movies.csv
│   ├── posters.csv
│   ├── genres.csv
│   ├── actors.csv
│   └── crew.csv
├── app.py
├── Volhack.pdf
└── README.md
```

## Running the App

Once your packages are installed and the datasets are in place, run the Streamlit app from the root directory:

```bash
python -m streamlit run app.py
```

The application will automatically launch in your default web browser at:

```text
http://localhost:8501
```

To stop the local server at any time, press `Ctrl + C` in your terminal.
