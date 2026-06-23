from copy import deepcopy

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Golf Event Scorecard",
    page_icon="GC",
    layout="wide",
)


# Edit player names and handicap indexes here.
DEFAULT_PLAYERS = [
    {"name": "Mike", "handicap_index": 16},
    {"name": "Jack", "handicap_index": 12.5},
    {"name": "Ollie", "handicap_index": 19.5},
    {"name": "Danny", "handicap_index": 28.2},
]

APP_CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #f4f8f1 0%, #ffffff 35%, #f9f7ef 100%);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero-card, .section-card, .player-card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #d8e4d2;
        border-radius: 18px;
        box-shadow: 0 14px 40px rgba(41, 74, 47, 0.08);
    }
    .hero-card {
        padding: 1.4rem 1.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #0f5132 0%, #5d8c49 100%);
        color: #ffffff;
        border: none;
    }
    .hero-card h1 {
        margin: 0;
        font-size: 2rem;
        color: #ffffff;
    }
    .hero-card p {
        margin: 0.4rem 0 0 0;
        font-size: 1rem;
        color: #edf7ea;
    }
    .section-card {
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
    }
    .player-card {
        padding: 0.9rem 1rem;
        margin-bottom: 0.75rem;
        border-left: 6px solid #d7a73d;
    }
    .standings-wrap {
        margin-top: 1rem;
        background: linear-gradient(160deg, #18354c 0%, #0f2235 60%, #142c43 100%);
        border-radius: 20px;
        padding: 0.9rem;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 18px 40px rgba(10, 28, 44, 0.2);
    }
    .standings-title {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .summary-inline-details {
        color: #53705d;
        font-size: 0.95rem;
        margin-bottom: 0.9rem;
    }
    .player-name {
        font-weight: 700;
        font-size: 1rem;
        color: #173622;
        margin-bottom: 0.15rem;
    }
    .player-meta {
        color: #53705d;
        font-size: 0.92rem;
    }
    .mini-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #5c745f;
        margin-bottom: 0.2rem;
    }
    .mini-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #173622;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d8e4d2;
        border-radius: 16px;
        padding: 0.7rem 0.9rem;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #d8e4d2;
    }
    .score-header {
        padding: 0.3rem 0.1rem;
        text-align: center;
        font-size: 0.82rem;
        font-weight: 700;
        color: #173622;
        border-radius: 10px;
    }
    .score-header-meta {
        background: #edf4e8;
    }
    .score-header-mike {
        background: #f6d7d9;
    }
    .score-header-jack {
        background: #dcefdc;
    }
    .score-header-ollie {
        background: #dce8f7;
    }
    .score-header-danny {
        background: #f7e4d1;
    }
    .score-cell-badge {
        margin-top: 0.15rem;
        padding: 0.32rem 0.1rem;
        text-align: center;
        border-radius: 10px;
        font-weight: 700;
        color: #173622;
    }
    .score-cell-mike {
        background: #f6d7d9;
    }
    .score-cell-jack {
        background: #dcefdc;
    }
    .score-cell-ollie {
        background: #dce8f7;
    }
    .score-cell-danny {
        background: #f7e4d1;
    }
</style>
"""


def make_default_course(name: str, slope_rating: int, course_rating: float, par_total: int, holes: list[dict]):
    return {
        "name": name,
        "par": par_total,
        "slope_rating": slope_rating,
        "course_rating": course_rating,
        "handicap_allowance": 95,
        "holes": holes,
    }


MOSSOCK_HALL_YELLOW_HOLES = [
    {"hole": 1, "par": 4, "stroke_index": 3},
    {"hole": 2, "par": 3, "stroke_index": 13},
    {"hole": 3, "par": 4, "stroke_index": 1},
    {"hole": 4, "par": 4, "stroke_index": 7},
    {"hole": 5, "par": 5, "stroke_index": 9},
    {"hole": 6, "par": 3, "stroke_index": 17},
    {"hole": 7, "par": 5, "stroke_index": 11},
    {"hole": 8, "par": 4, "stroke_index": 15},
    {"hole": 9, "par": 4, "stroke_index": 5},
    {"hole": 10, "par": 4, "stroke_index": 12},
    {"hole": 11, "par": 3, "stroke_index": 18},
    {"hole": 12, "par": 4, "stroke_index": 10},
    {"hole": 13, "par": 4, "stroke_index": 8},
    {"hole": 14, "par": 3, "stroke_index": 16},
    {"hole": 15, "par": 5, "stroke_index": 6},
    {"hole": 16, "par": 4, "stroke_index": 2},
    {"hole": 17, "par": 4, "stroke_index": 4},
    {"hole": 18, "par": 4, "stroke_index": 14},
]


PLACEHOLDER_DAY_2_HOLES = [
    {"hole": 1, "par": 4, "stroke_index": 11},
    {"hole": 2, "par": 4, "stroke_index": 3},
    {"hole": 3, "par": 4, "stroke_index": 7},
    {"hole": 4, "par": 3, "stroke_index": 15},
    {"hole": 5, "par": 4, "stroke_index": 1},
    {"hole": 6, "par": 4, "stroke_index": 17},
    {"hole": 7, "par": 5, "stroke_index": 13},
    {"hole": 8, "par": 5, "stroke_index": 5},
    {"hole": 9, "par": 4, "stroke_index": 9},
    {"hole": 10, "par": 3, "stroke_index": 12},
    {"hole": 11, "par": 4, "stroke_index": 4},
    {"hole": 12, "par": 4, "stroke_index": 16},
    {"hole": 13, "par": 4, "stroke_index": 8},
    {"hole": 14, "par": 4, "stroke_index": 2},
    {"hole": 15, "par": 3, "stroke_index": 14},
    {"hole": 16, "par": 3, "stroke_index": 6},
    {"hole": 17, "par": 4, "stroke_index": 18},
    {"hole": 18, "par": 5, "stroke_index": 10},
]


DEFAULT_EVENT = {
    "players": deepcopy(DEFAULT_PLAYERS),
    "courses": {
        "day_1": make_default_course(
            "Mossock Hall",
            slope_rating=126,
            course_rating=71.7,
            par_total=71,
            holes=deepcopy(MOSSOCK_HALL_YELLOW_HOLES),
        ),
        "day_2": make_default_course(
            "Dean Wood",
            slope_rating=134,
            course_rating=68.7,
            par_total=71,
            holes=deepcopy(PLACEHOLDER_DAY_2_HOLES),
        ),
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


def get_score_input_key(day_key: str, player_idx: int, hole_number: int) -> str:
    return f"{day_key}_player_{player_idx}_hole_{hole_number}"


def sync_single_score_input(day_key: str, player_idx: int, hole_number: int):
    input_key = get_score_input_key(day_key, player_idx, hole_number)
    raw_value = st.session_state.get(input_key, "")
    parsed_value = safe_int(str(raw_value).strip(), fallback="")
    stored_value = parsed_value if parsed_value != 0 else ""
    st.session_state.event_data["scores"][day_key][f"player_{player_idx}"][hole_number - 1] = stored_value


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


def inject_styles():
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_hero():
    st.markdown(
        """
        <div class="hero-card">
            <h1>Aughton Major</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_player_color_class(player_idx: int) -> str:
    return ["mike", "jack", "ollie", "danny"][player_idx]


def render_player_cards():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Players")
    cols = st.columns(4)
    for idx, player in enumerate(st.session_state.event_data["players"]):
        with cols[idx]:
            st.markdown(
                f"""
                <div class="player-card">
                    <div class="player-name">{player["name"]}</div>
                    <div class="player-meta">Handicap Index: {float(player["handicap_index"]):.1f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


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
        rows.append(
            {
                "Player": player["name"],
                "Handicap Index": round(float(player["handicap_index"]), 1),
                "Course Handicap": course_hcap,
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
        course_hcap = int(handicap_table.loc[idx, "Course Handicap"])
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
            strokes = get_strokes_received(course_hcap, hole_info["stroke_index"])
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


def build_stableford_table(day_key: str) -> pd.DataFrame:
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    handicap_df = build_handicap_table(day_key)
    stableford_rows = []
    for hole in course["holes"]:
        row = {"Hole": hole["hole"], "Par": hole["par"], "SI": hole["stroke_index"]}
        for idx, player in enumerate(st.session_state.event_data["players"]):
            course_hcap = int(handicap_df.loc[idx, "Course Handicap"])
            score = st.session_state.event_data["scores"][day_key][f"player_{idx}"][hole["hole"] - 1]
            if score in ("", None):
                row[player["name"]] = ""
                continue
            strokes = get_strokes_received(course_hcap, hole["stroke_index"])
            row[player["name"]] = stableford_points(safe_int(score), hole["par"], strokes)
        stableford_rows.append(row)
    return pd.DataFrame(stableford_rows)


def build_shots_received_table(day_key: str) -> pd.DataFrame:
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    handicap_df = build_handicap_table(day_key)
    shots_rows = []
    for hole in course["holes"]:
        row = {"Hole": hole["hole"], "SI": hole["stroke_index"]}
        for idx, player in enumerate(st.session_state.event_data["players"]):
            course_hcap = int(handicap_df.loc[idx, "Course Handicap"])
            shots = get_strokes_received(course_hcap, hole["stroke_index"])
            row[player["name"]] = shots
        shots_rows.append(row)
    return pd.DataFrame(shots_rows)


def build_course_shots_summary() -> pd.DataFrame:
    day_1 = build_handicap_table("day_1").rename(columns={"Course Handicap": "Day 1 shots"})
    day_2 = build_handicap_table("day_2").rename(columns={"Course Handicap": "Day 2 shots"})
    merged = day_1.merge(day_2[["Player", "Day 2 shots"]], on="Player", how="inner")
    return merged[["Player", "Handicap Index", "Day 1 shots", "Day 2 shots"]]


def build_day_shots_summary(day_key: str) -> pd.DataFrame:
    handicap_df = build_handicap_table(day_key).rename(columns={"Course Handicap": "Shots"})
    return handicap_df[["Player", "Handicap Index", "Shots"]]


def build_standings_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    standings = summary_df.copy()
    standings.insert(0, "#", range(1, len(standings) + 1))
    standings = standings.rename(columns={"Shots": "Handicap"})
    return standings[["#", "Player", "Handicap", "Gross", "Stableford"]]


def get_hole_stableford_points(day_key: str, player_idx: int, hole_number: int) -> str:
    score = st.session_state.event_data["scores"][day_key][f"player_{player_idx}"][hole_number - 1]
    if score in ("", None):
        return "-"

    course = normalize_course(st.session_state.event_data["courses"][day_key])
    handicap_df = build_handicap_table(day_key)
    hole = course["holes"][hole_number - 1]
    course_hcap = int(handicap_df.loc[player_idx, "Course Handicap"])
    strokes = get_strokes_received(course_hcap, hole["stroke_index"])
    return str(stableford_points(safe_int(score), hole["par"], strokes))


def get_hole_shots_received(day_key: str, player_idx: int, hole_number: int) -> str:
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    handicap_df = build_handicap_table(day_key)
    hole = course["holes"][hole_number - 1]
    course_hcap = int(handicap_df.loc[player_idx, "Course Handicap"])
    return str(get_strokes_received(course_hcap, hole["stroke_index"]))


def render_day_snapshot(day_key: str, title: str):
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    summary_df = get_player_day_summary(day_key).sort_values(by=["Stableford", "Gross"], ascending=[False, True]).reset_index(drop=True)
    shots_df = build_day_shots_summary(day_key)
    summary_df = summary_df.merge(shots_df[["Player", "Shots"]], on="Player", how="left")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"#### {title} - {course['name']}")
    st.markdown(
        f"<div class='summary-inline-details'><strong>Course Details:</strong> Yellow tees, SR {course['slope_rating']}, CR {course['course_rating']:.1f}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='standings-wrap'><div class='standings-title'>Standings</div>", unsafe_allow_html=True)
    st.dataframe(
        build_standings_table(summary_df[["Player", "Shots", "Gross", "Stableford"]]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "#": st.column_config.NumberColumn(width="small"),
            "Player": st.column_config.TextColumn(width="medium"),
            "Handicap": st.column_config.NumberColumn(width="small"),
            "Gross": st.column_config.NumberColumn(width="small"),
            "Stableford": st.column_config.NumberColumn(width="small"),
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def score_editor(day_key: str, title: str):
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    st.subheader(f"{title} - {course['name']} scoring")
    st.caption("Enter gross scores only. Leave a box empty until that hole is played.")

    players = st.session_state.event_data["players"]

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    header_widths = [0.45, 0.45, 0.45, 0.9, 0.45, 0.45, 0.9, 0.45, 0.45, 0.9, 0.45, 0.45, 0.9, 0.45, 0.45]
    header_cols = st.columns(header_widths)
    for idx, label in enumerate(["Hole", "Par", "SI"]):
        header_cols[idx].markdown(f"<div class='score-header score-header-meta'>{label}</div>", unsafe_allow_html=True)

    for player_idx, player in enumerate(players):
        base_col = 3 + (player_idx * 3)
        color_class = get_player_color_class(player_idx)
        header_cols[base_col].markdown(
            f"<div class='score-header score-header-{color_class}'>{player['name']}</div>",
            unsafe_allow_html=True,
        )
        header_cols[base_col + 1].markdown(
            f"<div class='score-header score-header-{color_class}'>Shots</div>",
            unsafe_allow_html=True,
        )
        header_cols[base_col + 2].markdown(
            f"<div class='score-header score-header-{color_class}'>Pts</div>",
            unsafe_allow_html=True,
        )

    for hole in course["holes"]:
        row_cols = st.columns(header_widths)
        row_cols[0].markdown(str(hole["hole"]))
        row_cols[1].markdown(str(hole["par"]))
        row_cols[2].markdown(str(hole["stroke_index"]))

        for player_idx, player in enumerate(players):
            input_key = get_score_input_key(day_key, player_idx, hole["hole"])
            current_score = st.session_state.event_data["scores"][day_key][f"player_{player_idx}"][hole["hole"] - 1]
            if input_key not in st.session_state:
                st.session_state[input_key] = "" if current_score in ("", None) else str(current_score)

            score_col = 3 + (player_idx * 3)
            shots_col = score_col + 1
            points_col = score_col + 2
            color_class = get_player_color_class(player_idx)

            row_cols[score_col].text_input(
                label=f"{player['name']} hole {hole['hole']}",
                value=st.session_state[input_key],
                key=input_key,
                on_change=sync_single_score_input,
                args=(day_key, player_idx, hole["hole"]),
                label_visibility="collapsed",
                placeholder="-",
                max_chars=2,
            )
            row_cols[shots_col].markdown(
                f"<div class='score-cell-badge score-cell-{color_class}'>{get_hole_shots_received(day_key, player_idx, hole['hole'])}</div>",
                unsafe_allow_html=True,
            )
            row_cols[points_col].markdown(
                f"<div class='score-cell-badge score-cell-{color_class}'>{get_hole_stableford_points(day_key, player_idx, hole['hole'])}</div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)



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


def render_leaderboard(overview: pd.DataFrame):
    leader = overview.iloc[0]
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Cumulative leaderboard")
    metrics = st.columns(4)
    metrics[0].metric("Leading player", leader["Player"])
    metrics[1].metric("Total points", int(leader["Total Stableford"]))
    metrics[2].metric("Day 1 logged", int(overview["Day 1 Holes"].sum()))
    metrics[3].metric("Day 2 logged", int(overview["Day 2 Holes"].sum()))
    st.dataframe(
        overview[["Position", "Player", "Total Stableford", "Day 1 Stableford", "Day 2 Stableford", "Total Gross"]],
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_overall_page():
    overview = cumulative_leaderboard()
    render_player_cards()
    render_leaderboard(overview)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Course shots summary")
    st.dataframe(build_course_shots_summary(), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_day_page(day_key: str, title: str):
    render_day_snapshot(day_key, title)
    score_editor(day_key, title)


def main():
    initialize_state()
    inject_styles()

    render_hero()
    page = st.segmented_control(
        "View",
        options=["Overall Leaderboard", "Day 1", "Day 2"],
        default="Overall Leaderboard",
        selection_mode="single",
    )

    if page == "Overall Leaderboard":
        render_overall_page()
    elif page == "Day 1":
        render_day_page("day_1", "Day 1")
    else:
        render_day_page("day_2", "Day 2")


if __name__ == "__main__":
    main()
