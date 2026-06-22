# Golf Event Scorecard

A Streamlit app for a two-day golf event with:

- 4 players
- Handicap Index to Course Handicap to Playing Handicap conversion
- Live gross score entry
- Stableford scoring by hole and by day
- Cumulative two-day leaderboard
- Download and reload of the event as JSON

## Courses

- Day 1: Mossock Hall
- Day 2: Huyton and Prescot

The course setup is editable so you can match the exact tee, par, stroke index, slope rating, course rating, and handicap allowance from the cards you are using.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Upload to GitHub

This folder is ready to upload as a repository. If you want to publish it on Streamlit Community Cloud, set the main file to `app.py`.
