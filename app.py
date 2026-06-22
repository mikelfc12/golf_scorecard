import io
import json
from copy import deepcopy

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Golf Event Scorecard",
    page_icon="⛳",
    layout="wide",
)


DEFAULT_PLAYERS = [
    {"name": "Player 1", "handicap_index": 18.2},
    {"name": "Player 2", "handicap_index": 16.4},
    {"name": "Player 3", "handicap_index": 12.7},
    {"name": "Player 4", "handicap_index": 9.8},
]

DEFAULT_PAR_SEQUENCE = [4, 4, 3, 5, 4, 4, 3, 5, 4, 4, 4, 3, 5, 4, 4, 3, 5, 4]


def make_default_course(name: str, slope_rating: int, course_rating: float, par_total: int):
    pars = DEFAULT_PAR_SEQUENCE[:]
    adjustment = par_total - sum(pars)
    pars[-1] += adjustment
    return {
        "name": name,
        "par": par_total,
        "slope_rating": slope_rating,
        "course_rating": course_rating,
        "handicap_allowance": 95,
        "holes": [
            {"hole": hole, "par": pars[hole - 1], "stroke_index": hole}
            for hole in range(1, 19)
        ],
    }


DEFAULT_EVENT = {
    "players": deepcopy(DEFAULT_PLAYERS),
    "courses": {
        "day_1": make_default_course("Mossock Hall", slope_rating=123, course_rating=71.4, par_total=72),
        "day_2": make_default_course("Huyton and Prescot", slope_rating=128, course_rating=71.8, par_total=72),
    },
    "scores": {
        "day_1": {f"player_{idx}": [""] * 18 for idx in range(4)},
        "day_2": {f"player_{idx}": [""] * 18 for idx in range(4)},
    },
}


def initialize_state():
    if "event_data" not in st.session_state:
        st.session_state.event_data = deepcopy(DEFAULT_EVENT)


def safe_int(value, fallback=0):
    try:
        if value in ("", None):
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback


def safe_float(value, fallback=0.0):
    try:
        if value in ("", None):
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def get_strokes_received(playing_handicap: int, stroke_index: int) -> int:
    if playing_handicap >= 0:
        base, remainder = divmod(playing_handicap, 18)
        return base + (1 if stroke_index <= remainder else 0)

    plus_value = abs(playing_handicap)
    base, remainder = divmod(plus_value, 18)
    return -base - (1 if stroke_index > 18 - remainder else 0)


def stableford_points(gross_score: int, par: int, strokes_received: int) -> int:
    net_relative_to_par = gross_score - strokes_received - par
    return max(0, 2 - net_relative_to_par)


def course_handicap(handicap_index: float, slope_rating: int, course_rating: float, par_value: int) -> int:
    calculated = handicap_index * (slope_rating / 113) + (course_rating - par_value)
    return int(round(calculated))


def playing_handicap(course_handicap_value: int, allowance_percent: float) -> int:
    return int(round(course_handicap_value * (allowance_percent / 100)))


def normalize_course(course: dict) -> dict:
    normalized = deepcopy(course)
    normalized["par"] = safe_int(normalized.get("par"), 72)
    normalized["slope_rating"] = safe_int(normalized.get("slope_rating"), 113)
    normalized["course_rating"] = safe_float(normalized.get("course_rating"), float(normalized["par"]))
    normalized["handicap_allowance"] = safe_float(normalized.get("handicap_allowance"), 95)
    holes = normalized.get("holes", [])
    if len(holes) != 18:
        holes = [{"hole": hole, "par": 4, "stroke_index": hole} for hole in range(1, 19)]
    normalized["holes"] = [
        {
            "hole": safe_int(hole_data.get("hole"), idx + 1),
            "par": safe_int(hole_data.get("par"), 4),
            "stroke_index": safe_int(hole_data.get("stroke_index"), idx + 1),
        }
        for idx, hole_data in enumerate(holes)
    ]
    return normalized


def to_plain_data(value):
    if isinstance(value, dict):
        return {key: to_plain_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain_data(item) for item in value]
    if isinstance(value, tuple):
        return [to_plain_data(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def course_editor(day_key: str, title: str):
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    with st.expander(f"{title} course setup", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        course["name"] = col1.text_input("Course name", value=course["name"], key=f"{day_key}_name")
        course["par"] = col2.number_input("Course par", min_value=54, max_value=90, value=course["par"], key=f"{day_key}_par")
        course["slope_rating"] = col3.number_input(
            "Slope rating",
            min_value=55,
            max_value=155,
            value=course["slope_rating"],
            key=f"{day_key}_slope",
        )
        course["course_rating"] = col4.number_input(
            "Course rating",
            min_value=50.0,
            max_value=90.0,
            value=float(course["course_rating"]),
            step=0.1,
            key=f"{day_key}_rating",
        )

        course["handicap_allowance"] = st.number_input(
            "Handicap allowance (%)",
            min_value=1.0,
            max_value=100.0,
            value=float(course["handicap_allowance"]),
            step=1.0,
            key=f"{day_key}_allowance",
        )

        holes_df = pd.DataFrame(course["holes"])
        edited_holes = st.data_editor(
            holes_df,
            key=f"{day_key}_holes",
            use_container_width=True,
            hide_index=True,
            disabled=["hole"],
            column_config={
                "hole": st.column_config.NumberColumn("Hole", required=True),
                "par": st.column_config.NumberColumn("Par", min_value=3, max_value=6, required=True),
                "stroke_index": st.column_config.NumberColumn("Stroke Index", min_value=1, max_value=18, required=True),
            },
        )

        course["holes"] = [
            {
                "hole": safe_int(row["hole"], idx + 1),
                "par": safe_int(row["par"], 4),
                "stroke_index": safe_int(row["stroke_index"], idx + 1),
            }
            for idx, row in enumerate(edited_holes.to_dict("records"))
        ]
        st.session_state.event_data["courses"][day_key] = course


def render_players():
    st.sidebar.header("Players")
    for idx, player in enumerate(st.session_state.event_data["players"]):
        st.sidebar.subheader(f"Player {idx + 1}")
        player["name"] = st.sidebar.text_input(
            "Name",
            value=player["name"],
            key=f"player_name_{idx}",
        )
        player["handicap_index"] = st.sidebar.number_input(
            "Handicap Index",
            min_value=-10.0,
            max_value=54.0,
            value=float(player["handicap_index"]),
            step=0.1,
            key=f"player_hi_{idx}",
        )


def build_handicap_table(day_key: str) -> pd.DataFrame:
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    rows = []
    for player in st.session_state.event_data["players"]:
        course_hcap = course_handicap(
            handicap_index=float(player["handicap_index"]),
            slope_rating=course["slope_rating"],
            course_rating=course["course_rating"],
            par_value=course["par"],
        )
        play_hcap = playing_handicap(course_hcap, course["handicap_allowance"])
        rows.append(
            {
                "Player": player["name"],
                "Handicap Index": round(float(player["handicap_index"]), 1),
                "Course Handicap": course_hcap,
                "Playing Handicap": play_hcap,
            }
        )
    return pd.DataFrame(rows)


def get_player_day_summary(day_key: str):
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    hole_lookup = {hole["hole"]: hole for hole in course["holes"]}
    handicap_table = build_handicap_table(day_key)
    summaries = []

    for idx, player in enumerate(st.session_state.event_data["players"]):
        player_scores = st.session_state.event_data["scores"][day_key][f"player_{idx}"]
        play_hcap = int(handicap_table.loc[idx, "Playing Handicap"])
        gross_total = 0
        stableford_total = 0
        holes_played = 0

        for hole_number, raw_score in enumerate(player_scores, start=1):
            score = safe_int(raw_score, fallback=0)
            if score <= 0:
                continue
            holes_played += 1
            gross_total += score
            hole_info = hole_lookup[hole_number]
            strokes = get_strokes_received(play_hcap, hole_info["stroke_index"])
            stableford_total += stableford_points(score, hole_info["par"], strokes)

        summaries.append(
            {
                "Player": player["name"],
                "Gross": gross_total if holes_played else 0,
                "Stableford": stableford_total,
                "Holes Played": holes_played,
            }
        )

    return pd.DataFrame(summaries)


def score_editor(day_key: str, title: str):
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    scores = st.session_state.event_data["scores"][day_key]
    score_df = pd.DataFrame(
        {
            "Hole": list(range(1, 19)),
            "Par": [hole["par"] for hole in course["holes"]],
            "SI": [hole["stroke_index"] for hole in course["holes"]],
            st.session_state.event_data["players"][0]["name"]: scores["player_0"],
            st.session_state.event_data["players"][1]["name"]: scores["player_1"],
            st.session_state.event_data["players"][2]["name"]: scores["player_2"],
            st.session_state.event_data["players"][3]["name"]: scores["player_3"],
        }
    )

    st.subheader(f"{title} scoring")
    st.caption("Enter gross scores as the round progresses. Leave a cell blank if the hole has not been played yet.")

    edited_scores = st.data_editor(
        score_df,
        key=f"{day_key}_scores",
        use_container_width=True,
        hide_index=True,
        disabled=["Hole", "Par", "SI"],
        column_config={
            "Hole": st.column_config.NumberColumn("Hole"),
            "Par": st.column_config.NumberColumn("Par"),
            "SI": st.column_config.NumberColumn("SI"),
        },
    )

    player_names = [player["name"] for player in st.session_state.event_data["players"]]
    for idx, player_name in enumerate(player_names):
        cleaned_scores = []
        for value in edited_scores[player_name].tolist():
            if value in ("", None):
                cleaned_scores.append("")
            else:
                cleaned_scores.append(safe_int(value, ""))
        st.session_state.event_data["scores"][day_key][f"player_{idx}"] = cleaned_scores

    handicap_df = build_handicap_table(day_key)
    summary_df = get_player_day_summary(day_key)

    col1, col2 = st.columns([1.1, 1])
    with col1:
        st.markdown("**Handicap conversion**")
        st.dataframe(handicap_df, use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**Day totals**")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("**Hole-by-hole Stableford**")
    stableford_rows = []
    for hole in course["holes"]:
        row = {"Hole": hole["hole"], "Par": hole["par"], "SI": hole["stroke_index"]}
        for idx, player in enumerate(st.session_state.event_data["players"]):
            play_hcap = int(handicap_df.loc[idx, "Playing Handicap"])
            score = st.session_state.event_data["scores"][day_key][f"player_{idx}"][hole["hole"] - 1]
            if score in ("", None):
                row[player["name"]] = ""
                continue
            strokes = get_strokes_received(play_hcap, hole["stroke_index"])
            row[player["name"]] = stableford_points(safe_int(score), hole["par"], strokes)
        stableford_rows.append(row)
    st.dataframe(pd.DataFrame(stableford_rows), use_container_width=True, hide_index=True)


def cumulative_leaderboard():
    day_1 = get_player_day_summary("day_1").rename(
        columns={"Gross": "Day 1 Gross", "Stableford": "Day 1 Stableford", "Holes Played": "Day 1 Holes"}
    )
    day_2 = get_player_day_summary("day_2").rename(
        columns={"Gross": "Day 2 Gross", "Stableford": "Day 2 Stableford", "Holes Played": "Day 2 Holes"}
    )

    merged = day_1.merge(day_2, on="Player", how="outer")
    merged["Total Gross"] = merged["Day 1 Gross"] + merged["Day 2 Gross"]
    merged["Total Stableford"] = merged["Day 1 Stableford"] + merged["Day 2 Stableford"]
    merged["Total Holes Played"] = merged["Day 1 Holes"] + merged["Day 2 Holes"]
    merged = merged.sort_values(by=["Total Stableford", "Total Gross"], ascending=[False, True]).reset_index(drop=True)
    merged.index = merged.index + 1
    merged.insert(0, "Position", merged.index)
    return merged


def render_save_load():
    st.sidebar.header("Event file")
    export_data = json.dumps(to_plain_data(st.session_state.event_data), indent=2)
    st.sidebar.download_button(
        "Download event JSON",
        data=export_data,
        file_name="golf_event_scorecard.json",
        mime="application/json",
    )

    uploaded = st.sidebar.file_uploader("Load event JSON", type=["json"])
    if uploaded is not None:
        loaded = json.load(io.StringIO(uploaded.getvalue().decode("utf-8")))
        st.session_state.event_data = loaded
        st.rerun()

    if st.sidebar.button("Reset event"):
        st.session_state.event_data = deepcopy(DEFAULT_EVENT)
        st.rerun()


def main():
    initialize_state()

    st.title("Two-Day Golf Event Scorecard")
    st.write(
        "Track four players across Mossock Hall and Huyton and Prescot with live score entry, "
        "automatic playing handicaps, Stableford scoring, and a cumulative leaderboard."
    )

    render_players()
    render_save_load()

    overview = cumulative_leaderboard()
    top_col, bottom_col = st.columns([1.1, 1])
    with top_col:
        st.subheader("Cumulative leaderboard")
        st.dataframe(overview, use_container_width=True, hide_index=True)
    with bottom_col:
        st.subheader("Event progress")
        metric_cols = st.columns(3)
        metric_cols[0].metric("Day 1 holes logged", int(overview["Day 1 Holes"].sum()))
        metric_cols[1].metric("Day 2 holes logged", int(overview["Day 2 Holes"].sum()))
        metric_cols[2].metric("Total Stableford points", int(overview["Total Stableford"].sum()))
        st.info(
            "Course details are editable so you can match the exact tee, par, stroke index, "
            "slope rating, and course rating from your scorecard."
        )

    tab1, tab2 = st.tabs(["Day 1: Mossock Hall", "Day 2: Huyton and Prescot"])
    with tab1:
        course_editor("day_1", "Day 1")
        score_editor("day_1", "Day 1")
    with tab2:
        course_editor("day_2", "Day 2")
        score_editor("day_2", "Day 2")


if __name__ == "__main__":
    main()
