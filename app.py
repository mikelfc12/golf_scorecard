from copy import deepcopy
from datetime import datetime, timezone
import base64
import json
import os
from pathlib import Path
from textwrap import dedent
from urllib import error, request

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Golf Event Scorecard",
    page_icon="GC",
    layout="centered",
)


# Edit player names and handicap indexes here.
DEFAULT_PLAYERS = [
    {"name": "Mike", "handicap_index": 16},
    {"name": "Jack", "handicap_index": 12.5},
    {"name": "Ollie", "handicap_index": 19.5},
    {"name": "Danny", "handicap_index": 30.3},
]

DATA_FILE = Path("event_data.json")
GITHUB_API_BASE = "https://api.github.com"

APP_CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #f4f8f1 0%, #ffffff 35%, #f9f7ef 100%);
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 960px;
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
    .player-grid, .summary-grid, .metrics-grid {
        display: grid;
        gap: 0.8rem;
    }
    .player-grid {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }
    .summary-grid {
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        margin-top: 0.85rem;
    }
    .metrics-grid {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        margin: 0.9rem 0 1rem 0;
    }
    .player-card {
        padding: 0.9rem 1rem;
        border-left: 6px solid #d7a73d;
    }
    .summary-card, .metric-card, .hole-card {
        background: #ffffff;
        border: 1px solid #d8e4d2;
        border-radius: 16px;
        box-shadow: 0 10px 28px rgba(41, 74, 47, 0.06);
    }
    .summary-card {
        padding: 0.95rem 1rem;
    }
    .summary-card.is-leader {
        background: linear-gradient(135deg, #173622 0%, #2d6b3d 100%);
        border: none;
        color: #ffffff;
    }
    .summary-rank {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #5c745f;
        margin-bottom: 0.25rem;
    }
    .summary-card.is-leader .summary-rank,
    .summary-card.is-leader .summary-stat-label,
    .summary-card.is-leader .summary-meta {
        color: rgba(255, 255, 255, 0.8);
    }
    .summary-card.is-leader .summary-player,
    .summary-card.is-leader .summary-stat-value {
        color: #ffffff;
    }
    .summary-player {
        font-size: 1.15rem;
        font-weight: 700;
        color: #173622;
        margin-bottom: 0.55rem;
    }
    .summary-stats {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.6rem;
    }
    .summary-stat-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #5c745f;
    }
    .summary-stat-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: #173622;
    }
    .summary-meta {
        margin-top: 0.7rem;
        font-size: 0.88rem;
        color: #53705d;
    }
    .metric-card {
        padding: 0.85rem 0.95rem;
    }
    .metric-label {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #5c745f;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #173622;
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
    .score-intro {
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
    .hole-card {
        padding: 0.9rem;
        margin-bottom: 0.85rem;
    }
    .hole-topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        margin-bottom: 0.75rem;
    }
    .hole-number {
        font-size: 1.15rem;
        font-weight: 700;
        color: #173622;
    }
    .hole-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        justify-content: flex-end;
    }
    .hole-chip {
        padding: 0.3rem 0.55rem;
        border-radius: 999px;
        background: #edf4e8;
        color: #355440;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .player-score-shell {
        border-top: 1px solid #ebf1e7;
        padding-top: 0.75rem;
        margin-top: 0.75rem;
    }
    .player-score-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.55rem;
    }
    .player-score-name {
        font-weight: 700;
        color: #173622;
    }
    .player-score-meta {
        font-size: 0.86rem;
        color: #53705d;
    }
    .badge-row {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-top: 0.55rem;
    }
    .score-cell-badge {
        min-width: 74px;
        padding: 0.38rem 0.55rem;
        text-align: center;
        border-radius: 10px;
        font-weight: 700;
        color: #173622;
    }
    .score-badge-label {
        display: block;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.08rem;
        opacity: 0.78;
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
    div[data-testid="stSegmentedControl"] {
        margin-bottom: 1rem;
    }
    @media (max-width: 640px) {
        .block-container {
            padding-top: 1rem;
            padding-left: 0.85rem;
            padding-right: 0.85rem;
            padding-bottom: 1.5rem;
        }
        .hero-card {
            padding: 1rem;
            border-radius: 16px;
        }
        .hero-card h1 {
            font-size: 1.55rem;
        }
        .section-card {
            padding: 0.85rem;
            border-radius: 16px;
        }
        .summary-grid, .player-grid, .metrics-grid {
            gap: 0.65rem;
        }
        .hole-card {
            padding: 0.8rem;
        }
        .hole-topline, .player-score-head {
            align-items: flex-start;
            flex-direction: column;
        }
        .hole-meta {
            justify-content: flex-start;
        }
        .badge-row {
            width: 100%;
        }
        .score-cell-badge {
            flex: 1 1 0;
        }
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


def get_secret_or_env(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, default)


def normalize_event_data(raw_data: dict | None) -> dict:
    normalized = deepcopy(DEFAULT_EVENT)
    if not isinstance(raw_data, dict):
        return normalized

    players = raw_data.get("players", [])
    if isinstance(players, list):
        for idx, default_player in enumerate(normalized["players"]):
            if idx >= len(players) or not isinstance(players[idx], dict):
                continue
            incoming = players[idx]
            default_player["name"] = str(incoming.get("name", default_player["name"]))
            default_player["handicap_index"] = safe_float(
                incoming.get("handicap_index"),
                float(default_player["handicap_index"]),
            )

    for day_key, default_course in normalized["courses"].items():
        course = raw_data.get("courses", {}).get(day_key, {})
        if not isinstance(course, dict):
            continue
        default_course["name"] = str(course.get("name", default_course["name"]))
        default_course["par"] = safe_int(course.get("par"), default_course["par"])
        default_course["slope_rating"] = safe_int(course.get("slope_rating"), default_course["slope_rating"])
        default_course["course_rating"] = safe_float(course.get("course_rating"), default_course["course_rating"])
        default_course["handicap_allowance"] = safe_float(
            course.get("handicap_allowance"),
            default_course["handicap_allowance"],
        )
        holes = course.get("holes", [])
        if isinstance(holes, list) and len(holes) == 18:
            default_course["holes"] = [
                {
                    "hole": safe_int(hole.get("hole"), idx + 1),
                    "par": safe_int(hole.get("par"), default_course["holes"][idx]["par"]),
                    "stroke_index": safe_int(hole.get("stroke_index"), default_course["holes"][idx]["stroke_index"]),
                }
                for idx, hole in enumerate(holes)
                if isinstance(hole, dict)
            ]

    for day_key in normalized["scores"]:
        incoming_scores = raw_data.get("scores", {}).get(day_key, {})
        if not isinstance(incoming_scores, dict):
            continue
        for idx in range(len(normalized["players"])):
            player_key = f"player_{idx}"
            score_list = incoming_scores.get(player_key, [])
            if not isinstance(score_list, list):
                continue
            normalized["scores"][day_key][player_key] = [
                safe_int(value, fallback="") if safe_int(value, fallback=0) != 0 else ""
                for value in score_list[:18]
            ]
            if len(normalized["scores"][day_key][player_key]) < 18:
                normalized["scores"][day_key][player_key].extend([""] * (18 - len(normalized["scores"][day_key][player_key])))

    return normalized


def load_event_data() -> dict:
    if not DATA_FILE.exists():
        return deepcopy(DEFAULT_EVENT)

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file_handle:
            return normalize_event_data(json.load(file_handle))
    except (OSError, json.JSONDecodeError):
        return deepcopy(DEFAULT_EVENT)


def set_persistence_status(saved: bool, message: str, github_enabled: bool | None = None):
    st.session_state.persistence_status = {
        "saved": saved,
        "message": message,
        "updated_at": datetime.now().strftime("%H:%M:%S"),
        "github_enabled": github_enabled,
    }


def sync_event_data_to_github(file_text: str):
    token = get_secret_or_env("GITHUB_TOKEN")
    repo = get_secret_or_env("GITHUB_REPO", "mikelfc12/golf_scorecard")
    branch = get_secret_or_env("GITHUB_BRANCH", "main")
    file_path = get_secret_or_env("GITHUB_DATA_PATH", DATA_FILE.name)

    if not token:
        return False, "Saved locally. Add GITHUB_TOKEN to also commit scores to GitHub."

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "golf-scorecard-app",
    }
    contents_url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{file_path}"

    sha_value = None
    get_request = request.Request(f"{contents_url}?ref={branch}", headers=headers, method="GET")
    try:
        with request.urlopen(get_request, timeout=15) as response:
            existing = json.loads(response.read().decode("utf-8"))
            sha_value = existing.get("sha")
    except error.HTTPError as exc:
        if exc.code != 404:
            raise

    payload = {
        "message": f"Update golf scores {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "content": base64.b64encode(file_text.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha_value:
        payload["sha"] = sha_value

    put_request = request.Request(
        contents_url,
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
        method="PUT",
    )
    with request.urlopen(put_request, timeout=20) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    commit_sha = response_payload.get("commit", {}).get("sha", "")
    short_sha = commit_sha[:7] if commit_sha else "created"
    return True, f"Saved locally and committed to GitHub ({short_sha})."


def persist_event_data():
    normalized = normalize_event_data(st.session_state.event_data)
    st.session_state.event_data = normalized
    file_text = json.dumps(normalized, indent=2)

    try:
        DATA_FILE.write_text(file_text + "\n", encoding="utf-8")
    except OSError as exc:
        set_persistence_status(False, f"Save failed: {exc}")
        return

    try:
        github_saved, message = sync_event_data_to_github(file_text + "\n")
        set_persistence_status(True, message, github_enabled=github_saved)
    except Exception as exc:
        set_persistence_status(True, f"Saved locally, but GitHub sync failed: {exc}")


def initialize_state():
    if "event_data" not in st.session_state:
        st.session_state.event_data = load_event_data()
    if "persistence_status" not in st.session_state:
        github_configured = bool(get_secret_or_env("GITHUB_TOKEN"))
        default_message = "Scores save on this device."
        if github_configured:
            default_message = "Scores save locally and can sync to GitHub."
        set_persistence_status(True, default_message, github_enabled=github_configured)


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
    persist_event_data()


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


def render_persistence_status():
    status = st.session_state.get("persistence_status", {})
    timestamp = status.get("updated_at", "")
    message = status.get("message", "Scores have not been saved yet.")
    if timestamp:
        st.caption(f"{message} Last update: {timestamp}")
    else:
        st.caption(message)


def get_player_color_class(player_idx: int) -> str:
    return ["mike", "jack", "ollie", "danny"][player_idx]


def render_player_cards():
    st.markdown("#### Players")
    player_cards = []
    for player in st.session_state.event_data["players"]:
        player_cards.append(
            dedent(
                f"""
                <div class="player-card">
                    <div class="player-name">{player["name"]}</div>
                    <div class="player-meta">Handicap Index: {float(player["handicap_index"]):.1f}</div>
                </div>
                """
            ).strip()
        )
    st.markdown(f"<div class='player-grid'>{''.join(player_cards)}</div>", unsafe_allow_html=True)


def render_metric_cards(metrics: list[tuple[str, str]]):
    metric_markup = "".join(
        dedent(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """
        ).strip()
        for label, value in metrics
    )
    st.markdown(f"<div class='metrics-grid'>{metric_markup}</div>", unsafe_allow_html=True)


def render_summary_cards(rows: list[dict], total_points_key: str, gross_key: str, holes_key: str | None = None):
    cards = []
    for idx, row in enumerate(rows, start=1):
        leader_class = " is-leader" if idx == 1 else ""
        hole_meta = f"<div class='summary-meta'>Holes logged: {int(row[holes_key])}</div>" if holes_key else ""
        cards.append(
            dedent(
                f"""
                <div class="summary-card{leader_class}">
                    <div class="summary-rank">Position {idx}</div>
                    <div class="summary-player">{row["Player"]}</div>
                    <div class="summary-stats">
                        <div>
                            <div class="summary-stat-label">Stableford</div>
                            <div class="summary-stat-value">{int(row[total_points_key])}</div>
                        </div>
                        <div>
                            <div class="summary-stat-label">Gross</div>
                            <div class="summary-stat-value">{int(row[gross_key])}</div>
                        </div>
                    </div>
                    {hole_meta}
                </div>
                """
            ).strip()
        )
    st.markdown(f"<div class='summary-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_course_shots_cards():
    shots_df = build_course_shots_summary()
    cards = []
    for row in shots_df.to_dict("records"):
        cards.append(
            dedent(
                f"""
                <div class="summary-card">
                    <div class="summary-player">{row["Player"]}</div>
                    <div class="summary-stats">
                        <div>
                            <div class="summary-stat-label">Handicap Index</div>
                            <div class="summary-stat-value">{float(row["Handicap Index"]):.1f}</div>
                        </div>
                        <div>
                            <div class="summary-stat-label">Day 1 shots</div>
                            <div class="summary-stat-value">{int(row["Day 1 shots"])}</div>
                        </div>
                    </div>
                    <div class="summary-meta">Day 2 shots: {int(row["Day 2 shots"])}</div>
                </div>
                """
            ).strip()
        )
    st.markdown(f"<div class='summary-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


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

    st.markdown(f"#### {title} - {course['name']}")
    st.markdown(
        f"<div class='summary-inline-details'><strong>Course Details:</strong> Yellow tees, SR {course['slope_rating']}, CR {course['course_rating']:.1f}</div>",
        unsafe_allow_html=True,
    )
    render_summary_cards(summary_df.to_dict("records"), "Stableford", "Gross", "Holes Played")


def score_editor(day_key: str, title: str):
    course = normalize_course(st.session_state.event_data["courses"][day_key])
    st.subheader(f"{title} - {course['name']} scoring")
    st.markdown(
        "<div class='score-intro'>Enter gross scores only. Leave a box empty until that hole is played.</div>",
        unsafe_allow_html=True,
    )

    players = st.session_state.event_data["players"]

    for hole in course["holes"]:
        st.markdown(
            f"""
            <div class="hole-card">
                <div class="hole-topline">
                    <div class="hole-number">Hole {hole["hole"]}</div>
                    <div class="hole-meta">
                        <div class="hole-chip">Par {hole["par"]}</div>
                        <div class="hole-chip">SI {hole["stroke_index"]}</div>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        for player_idx, player in enumerate(players):
            input_key = get_score_input_key(day_key, player_idx, hole["hole"])
            current_score = st.session_state.event_data["scores"][day_key][f"player_{player_idx}"][hole["hole"] - 1]
            if input_key not in st.session_state:
                st.session_state[input_key] = "" if current_score in ("", None) else str(current_score)

            color_class = get_player_color_class(player_idx)
            st.markdown(
                f"""
                <div class="player-score-shell">
                    <div class="player-score-head">
                        <div class="player-score-name">{player["name"]}</div>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            st.text_input(
                label=f"{player['name']} hole {hole['hole']}",
                value=st.session_state[input_key],
                key=input_key,
                on_change=sync_single_score_input,
                args=(day_key, player_idx, hole["hole"]),
                label_visibility="collapsed",
                placeholder="Enter score",
                max_chars=2,
            )
            st.markdown(
                f"""
                <div class="badge-row">
                    <div class='score-cell-badge score-cell-{color_class}'>
                        <span class="score-badge-label">Shots</span>
                        {get_hole_shots_received(day_key, player_idx, hole['hole'])}
                    </div>
                    <div class='score-cell-badge score-cell-{color_class}'>
                        <span class="score-badge-label">Points</span>
                        {get_hole_stableford_points(day_key, player_idx, hole['hole'])}
                    </div>
                </div>
                </div>
                """,
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
    st.markdown("#### Cumulative leaderboard")
    render_metric_cards(
        [
            ("Leading player", str(leader["Player"])),
            ("Total points", str(int(leader["Total Stableford"]))),
            ("Day 1 logged", str(int(overview["Day 1 Holes"].sum()))),
            ("Day 2 logged", str(int(overview["Day 2 Holes"].sum()))),
        ]
    )
    render_summary_cards(overview.to_dict("records"), "Total Stableford", "Total Gross", "Total Holes Played")


def render_overall_page():
    overview = cumulative_leaderboard()
    render_player_cards()
    render_leaderboard(overview)

    st.markdown("#### Course shots summary")
    render_course_shots_cards()


def render_day_page(day_key: str, title: str):
    render_day_snapshot(day_key, title)
    score_editor(day_key, title)


def main():
    initialize_state()
    inject_styles()

    render_hero()
    render_persistence_status()
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
