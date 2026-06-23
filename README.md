# Golf Event Scorecard

A Streamlit app for a two-day golf event with:

- 4 players
- Handicap Index to Course Handicap conversion
- Live gross score entry
- Stableford scoring inline with hole entry
- Cumulative two-day leaderboard

## Courses

- Day 1: Mossock Hall, yellow tees
- Day 2: Dean Wood, yellow tees

The app is designed to stay easy to edit for Streamlit Community Cloud deployment:

- main app file: `app.py`
- dependencies: `requirements.txt`
- player names and handicap indexes are set near the top of `app.py`
- course defaults are stored near the top of `app.py`

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

Use this repository as the source and set the main file to `app.py`.

Future edits can be made directly in the GitHub repo and then redeployed through Streamlit Community Cloud.
