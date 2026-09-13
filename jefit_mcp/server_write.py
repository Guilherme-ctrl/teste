import json
import os
from datetime import datetime, date

from fastmcp import FastMCP

from auth import get_access_token, get_user_id
from history import get_workout_history
from workout_info import get_workout_for_date
from routine_write import (
    api,
    list_routines_api,
    get_routine_api,
    create_routine_api,
    add_routine_day_api,
    update_routine_api,
    update_day_api,
    search_exercises_api,
    add_exercise_to_day_api,
    update_day_exercise_sets_api,
)

mcp = FastMCP(
    name="JEFitWorkouts",
    instructions="""
Read JEFIT workout history and create/edit future workout routines.
All dates use YYYY-MM-DD. Routine write tools may create or edit routines,
but this server intentionally does not expose delete, publish, or activate/download actions.
When an exercise name is ambiguous, search exercises first and use its numeric id.
""",
)


@mcp.tool
def test_jefit_connection() -> dict:
    """Verify JEFIT authentication and return the authenticated user id."""
    token = get_access_token()
    uid = get_user_id(token)
    return {"ok": True, "user_id": uid, "username": os.getenv("JEFIT_USERNAME")}


@mcp.tool
def list_workout_dates(start_date: str, end_date: str | None = None) -> list[str]:
    """List workout dates in an inclusive YYYY-MM-DD date range."""
    if end_date is None:
        end_date = date.today().isoformat()
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if start > end:
        raise ValueError("start_date must be before or equal to end_date")
    result = []
    for value in get_workout_history():
        workout_date = datetime.strptime(value, "%Y-%m-%d").date()
        if start <= workout_date <= end:
            result.append(value)
    return sorted(result)


@mcp.tool
def get_workout_info(workout_date: str) -> dict:
    """Get raw detailed JEFIT workout/session data for one YYYY-MM-DD date."""
    datetime.strptime(workout_date, "%Y-%m-%d")
    return get_workout_for_date(workout_date)


@mcp.tool
def get_batch_workouts(dates: list[str]) -> dict[str, dict]:
    """Get detailed workout/session data for several YYYY-MM-DD dates."""
    if not dates:
        raise ValueError("dates cannot be empty")
    result = {}
    for value in dates:
        datetime.strptime(value, "%Y-%m-%d")
        result[value] = get_workout_for_date(value)
    return result


@mcp.tool
def list_routines() -> list[dict]:
    """List the authenticated user's JEFIT routines."""
    return list_routines_api()


@mcp.tool
def get_routine(routine_id: int) -> dict:
    """Get one JEFIT routine including its days and exercises."""
    return get_routine_api(routine_id)


@mcp.tool
def create_routine(
    name: str,
    description: str = "",
    focus: str = "general",
    difficulty: str = "intermediate",
    day_indexing_style: str = "number",
) -> dict:
    """
    Create a new private JEFIT routine with an initial day.

    focus: general | bulking | cutting | sport
    difficulty: beginner | intermediate | advanced
    day_indexing_style: number | weekday

    This does not publish, activate, or delete any existing routine.
    """
    return create_routine_api(name, description, focus, difficulty, day_indexing_style)


@mcp.tool
def update_routine(
    routine_id: int,
    name: str | None = None,
    description: str | None = None,
    focus: str | None = None,
    difficulty: str | None = None,
    day_indexing_style: str | None = None,
) -> dict:
    """Edit supported metadata on an existing JEFIT routine."""
    return update_routine_api(
        routine_id,
        name=name,
        description=description,
        focus=focus,
        difficulty=difficulty,
        day_indexing_style=day_indexing_style,
    )


@mcp.tool
def add_routine_day(
    routine_id: int,
    name: str | None = None,
    rest_day: bool = False,
    index: int | None = None,
    day_of_week: int | None = None,
) -> dict:
    """
    Add a day to a JEFIT routine.
    day_of_week uses 0..6 when supplied. This never removes existing days.
    """
    return add_routine_day_api(routine_id, name, rest_day, index, day_of_week)


@mcp.tool
def update_routine_day(
    day_id: int,
    name: str | None = None,
    rest_day: bool | None = None,
    index: int | None = None,
    day_of_week: int | None = None,
    estimated_duration: int | None = None,
    deload: bool | None = None,
):
    """Edit supported fields on an existing routine day."""
    return update_day_api(
        day_id,
        name=name,
        rest_day=rest_day,
        index=index,
        day_of_week=day_of_week,
        estimated_duration=estimated_duration,
        deload=deload,
    )


@mcp.tool
def search_exercises(query: str, limit: int = 10) -> list[dict]:
    """Search the JEFIT exercise catalog by name before adding exercises to a routine."""
    return search_exercises_api(query, limit)


@mcp.tool
def add_exercise_to_day(
    day_id: int,
    exercise: str,
    sets: int = 3,
    reps: int = 8,
    rest_seconds: int = 60,
    weight_lbs: float = 0,
    duration: int = 0,
    set_type: str = "default",
    sort_order: int = 0,
) -> dict:
    """
    Add an exercise to a routine day with an initial set prescription.

    exercise may be an exact exercise name or numeric JEFIT exercise id.
    set_type: default | warm-up | failure | drop
    Weight is stored in JEFIT's API field weight_lbs.
    """
    return add_exercise_to_day_api(
        day_id,
        exercise,
        sets,
        reps,
        rest_seconds,
        weight_lbs,
        duration,
        set_type,
        sort_order,
    )


@mcp.tool
def update_day_exercise_sets(day_exercise_id: int, sets: list[dict]):
    """
    Replace the prescribed sets for one exercise within a routine day.

    Each set can contain: id, type, sort_order, weight_lbs, reps, duration, rest_time.
    """
    return update_day_exercise_sets_api(day_exercise_id, sets)


def _smoke_test():
    if os.getenv("JEFIT_ROUTINE_SMOKE_TEST") != "1":
        return
    try:
        routines = list_routines_api()
        existing = next(
            (r for r in routines if isinstance(r, dict) and r.get("name") == "MCP Test"),
            None,
        )
        if existing:
            print(f"ROUTINE_SMOKE_TEST_OK existing id={existing.get('id')}", flush=True)
            return
        created = create_routine_api(
            "MCP Test",
            "Created automatically to validate JEFIT MCP routine write access.",
            "general",
            "intermediate",
            "number",
        )
        print(f"ROUTINE_SMOKE_TEST_OK created id={created.get('id')}", flush=True)
    except Exception as exc:
        print(f"ROUTINE_SMOKE_TEST_FAILED {type(exc).__name__}: {exc}", flush=True)


def _routine_diag():
    if os.getenv("JEFIT_ROUTINE_DIAG") != "1":
        return
    try:
        raw = api("GET", "/api/v2/user/routines", unwrap=False)
        text = json.dumps(raw, ensure_ascii=False, default=str)
        print("ROUTINE_DIAG_RAW " + text[:12000], flush=True)
    except Exception as exc:
        print(f"ROUTINE_DIAG_FAILED {type(exc).__name__}: {exc}", flush=True)


def main():
    _smoke_test()
    _routine_diag()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    mcp.run(host=host, port=port, transport="streamable-http")


if __name__ == "__main__":
    main()
