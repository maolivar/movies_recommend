# Movie Recommender — Reasoning with Data (FEN, Universidad de Chile)

Streamlit app for Week 8, Class 2 (user-based recommendations / collaborative filtering). It reads the students' movie ratings from a Google Form response sheet and:

- finds each student's most similar classmates;
- predicts their ratings of the movies they have not seen (k nearest neighbors, scikit-learn `KNNImputer`);
- recommends movies from a larger catalog using the MovieLens users as neighbors.

## Files

| File | Content |
|---|---|
| `app.py` | Streamlit app |
| `utils.py` | Data loading and k-NN functions (no Streamlit code) |
| `data/movie_map.csv` | The 20 form movies: title in the form → English title → MovieLens `movieId` |
| `data/ratings.csv` | MovieLens small: 100,836 ratings (0.5–5 stars) by 610 users |
| `data/movies.csv` | MovieLens small: titles and genres of 9,742 movies |
| `data/README_movielens.txt` | MovieLens README with its license (must be distributed with the data) |
| `requirements.txt` | Python packages |
| `docs/guia_profesores.pdf` | Instructions for professors (downloadable from the app); rebuild with `python docs/make_guide.py` (needs `reportlab`) |
| `.streamlit/secrets.toml` | Password (`unlock_code`), **not committed** (listed in `.gitignore`) |

Student ratings are **not** stored in this repository. They are read live from the Google Sheet link entered in the app. The sheet must be shared as "Anyone with the link can view".

## Run locally

```
streamlit run app.py
```

The app is open to anyone: each user pastes the link to their own response sheet. Optionally, `.streamlit/secrets.toml` (not committed) can hold `unlock_code` and `sheet_url`; whoever enters the code in the sidebar loads the course form.

## Use your own form (any movies)

Paste the link to the **Google Sheet with the form responses** (not the `forms.gle` link) in the sidebar and share it as "Anyone with the link can view". Structure: timestamp in the first column, one column per movie with the title in brackets (`... [El Padrino]`), and the student name in the last column. Answers can be the Spanish labels of the course form or numbers 1–5; columns without recognized ratings are ignored and listed in a sidebar warning. The same text is in the app (sidebar, "Estructura requerida del formulario").

To get recommendations from MovieLens for movies other than the 20 course movies, download the list of movie names (sidebar), fill in the `movieId` column using MovieLens `movies.csv`, and upload the file in the MovieLens tab. The upload is used only in that session and is not stored.

## Deploy (Streamlit Cloud)

1. Push this folder as the root of a GitHub repository.
2. On share.streamlit.io, create an app with entry point `app.py`.
3. In the app's Settings > Secrets, add `unlock_code = "your-password"` and `sheet_url = "<course response sheet link>"`.

## Data source and license

MovieLens "ml-latest-small" dataset, GroupLens Research, University of Minnesota: https://grouplens.org/datasets/movielens/latest/

F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. *ACM Transactions on Interactive Intelligent Systems* 5(4): 19:1–19:19. https://doi.org/10.1145/2827872

The data is redistributed under its original license (see `data/README_movielens.txt`): research and educational use, no commercial use, no implied endorsement by GroupLens.
