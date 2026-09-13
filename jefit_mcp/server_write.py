import os
from datetime import datetime, date

from fastmcp import FastMCP

from auth import get_access_token, get_user_id
from history import get_workout_history
from workout_info import get_workout_for_date
from routine_write import (
    list_routines_api, get_routine_api, create_routine_api, create_routine_with_days_api,
    update_routine_api, delete_routine_api, add_routine_day_api, update_day_api,
    copy_day_api, delete_day_api, search_exercises_api, add_exercise_to_day_api,
    update_day_exercise_api, update_day_exercise_sets_api, patch_one_set_api,
    add_set_api, remove_last_set_api, delete_day_exercise_api,
)

mcp = FastMCP(
    name="JEFitWorkouts",
    instructions="""
Read JEFIT workout history and create/edit future workout routines.
All dates use YYYY-MM-DD. JEFIT entity IDs may be encoded strings such as u_... or d_....
Only call mutating tools when the user explicitly asks to create or change a routine.
Never delete a routine, day, or exercise unless the user explicitly requests deletion and supplies confirmation.
Creating a routine does not publish it or activate/download it as the current routine.
When an exercise name is ambiguous, call search_exercises first and use the returned exact id.
""",
)


@mcp.tool
def test_jefit_connection() -> dict:
    """Verify JEFIT authentication and return the authenticated user id."""
    token = get_access_token()
    return {"ok": True, "user_id": get_user_id(token), "username": os.getenv("JEFIT_USERNAME")}


@mcp.tool
def list_workout_dates(start_date: str, end_date: str | None = None) -> list[str]:
    """List workout dates in an inclusive YYYY-MM-DD date range."""
    if end_date is None:
        end_date = date.today().isoformat()
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if start > end:
        raise ValueError("start_date must be before or equal to end_date")
    return sorted(
        value for value in get_workout_history()
        if start <= datetime.strptime(value, "%Y-%m-%d").date() <= end
    )


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
def get_routine(routine_id: str) -> dict:
    """Get one JEFIT routine."""
    return get_routine_api(routine_id)


@mcp.tool
def create_routine(
    name: str, description: str = "", focus: str = "general",
    difficulty: str = "intermediate", day_indexing_style: str = "number",
) -> dict:
    """Create a private JEFIT routine with its initial day; does not publish or activate it."""
    return create_routine_api(name, description, focus, difficulty, day_indexing_style)


@mcp.tool
def create_routine_plan(
    name: str, days: list[dict], description: str = "", focus: str = "general",
    difficulty: str = "intermediate", day_indexing_style: str = "number",
) -> dict:
    """
    Create a complete private JEFIT routine in one call: metadata, days, exercises and sets.
    Each day may contain name, rest_day, day_of_week and exercises. Each exercise object
    contains exercise (exact JEFIT name/id), sets, reps, rest_seconds, weight_lbs, duration,
    and set_type. On failure, only the newly-created partial routine is automatically removed.
    """
    return create_routine_with_days_api(
        name=name, days=days, description=description, focus=focus,
        difficulty=difficulty, day_indexing_style=day_indexing_style,
        cleanup_on_error=True,
    )


@mcp.tool
def update_routine(
    routine_id: str, name: str | None = None, description: str | None = None,
    focus: str | None = None, difficulty: str | None = None,
    day_indexing_style: str | None = None,
) -> dict:
    """Edit supported metadata on an existing JEFIT routine."""
    return update_routine_api(
        routine_id, name=name, description=description, focus=focus,
        difficulty=difficulty, day_indexing_style=day_indexing_style,
    )


@mcp.tool
def add_routine_day(
    routine_id: str, name: str | None = None, rest_day: bool = False,
    index: int | None = None, day_of_week: int | None = None,
) -> dict:
    """Add a day to a routine without removing existing days."""
    return add_routine_day_api(routine_id, name, rest_day, index, day_of_week)


@mcp.tool
def update_routine_day(
    day_id: str, name: str | None = None, rest_day: bool | None = None,
    index: int | None = None, day_of_week: int | None = None,
    estimated_duration: int | None = None, deload: bool | None = None,
    sort_order: int | None = None,
) -> dict:
    """Edit fields on an existing routine day."""
    return update_day_api(
        day_id, name=name, rest_day=rest_day, index=index, day_of_week=day_of_week,
        estimated_duration=estimated_duration, deload=deload, sort_order=sort_order,
    )


@mcp.tool
def copy_routine_day(day_id: str, day_of_week: int) -> dict:
    """Duplicate an existing routine day."""
    return copy_day_api(day_id, day_of_week)


@mcp.tool
def search_exercises(query: str, limit: int = 10) -> list[dict]:
    """Search the JEFIT exercise catalog by name."""
    return search_exercises_api(query, limit)


@mcp.tool
def add_exercise_to_day(
    day_id: str, exercise: str, sets: int = 3, reps: int = 8,
    rest_seconds: int = 60, weight_lbs: float | None = None,
    duration: int = 0, set_type: str = "default",
) -> dict:
    """Add an exercise to a routine day and configure its prescribed sets."""
    return add_exercise_to_day_api(
        day_id, exercise, sets, reps, rest_seconds, weight_lbs, duration, set_type
    )


@mcp.tool
def update_day_exercise(
    day_exercise_id: str, rest_time: int | None = None,
    number_of_reps: list[int] | None = None, count: int | None = None,
    index: int | None = None, interval_time_enabled: bool | None = None,
) -> dict:
    """Update supported fields on an exercise already inside a routine day."""
    return update_day_exercise_api(
        day_exercise_id, rest_time=rest_time, number_of_reps=number_of_reps,
        count=count, index=index, interval_time_enabled=interval_time_enabled,
    )


@mcp.tool
def update_day_exercise_sets(day_exercise_id: str, sets: list[dict]) -> dict:
    """Set the exact positional prescription for all sets of one day exercise."""
    return update_day_exercise_sets_api(day_exercise_id, sets)


@mcp.tool
def update_set(
    day_exercise_id: str, set_index: int, set_count: int,
    reps: int | None = None, weight_lbs: float | None = None,
    duration: int | None = None, rest_time: int | None = None,
    set_type: str | None = None,
) -> dict:
    """Patch one set by zero-based index; set_count is the current number of sets."""
    changes = {}
    if reps is not None: changes["reps"] = reps
    if weight_lbs is not None: changes["weight_lbs"] = weight_lbs
    if duration is not None: changes["duration"] = duration
    if rest_time is not None: changes["rest_time"] = rest_time
    if set_type is not None: changes["type"] = set_type
    return patch_one_set_api(day_exercise_id, set_index, set_count, changes)


@mcp.tool
def add_set(
    day_exercise_id: str, current_set_count: int, reps: int = 8,
    rest_time: int = 60, duration: int = 0, set_type: str = "default",
    weight_lbs: float | None = None,
) -> dict:
    """Append a set using JEFIT's positional set-patch API."""
    return add_set_api(day_exercise_id, current_set_count, reps, rest_time, duration, set_type, weight_lbs)


@mcp.tool
def remove_last_set(day_exercise_id: str, current_set_count: int) -> dict:
    """Remove only the final set; at least one set is retained."""
    return remove_last_set_api(day_exercise_id, current_set_count)


@mcp.tool
def delete_day_exercise(day_exercise_id: str, confirm: bool = False) -> dict:
    """Delete an exercise from a routine day. Requires confirm=true."""
    if not confirm:
        raise ValueError("Deletion requires confirm=true")
    delete_day_exercise_api(day_exercise_id)
    return {"deleted": True, "day_exercise_id": day_exercise_id}


@mcp.tool
def delete_routine_day(day_id: str, confirm: bool = False) -> dict:
    """Delete a routine day. Requires confirm=true."""
    if not confirm:
        raise ValueError("Deletion requires confirm=true")
    delete_day_api(day_id)
    return {"deleted": True, "day_id": day_id}


@mcp.tool
def delete_routine(routine_id: str, confirm_name: str) -> dict:
    """Delete a whole routine. confirm_name must exactly equal its current name."""
    routine = get_routine_api(routine_id)
    actual = str(routine.get("name") or "")
    if not actual or confirm_name != actual:
        raise ValueError("confirm_name must exactly match the current routine name")
    delete_routine_api(routine_id)
    return {"deleted": True, "routine_id": routine_id, "name": actual}


def _cleanup_test_artifacts():
    raw = os.getenv("JEFIT_CLEANUP_ROUTINE_IDS", "").strip()
    if not raw:
        return
    for rid in [v.strip() for v in raw.split(",") if v.strip()]:
        try:
            routine = get_routine_api(rid)
            name = str(routine.get("name") or "")
            if name != "New Routine":
                print(f"TEST_ARTIFACT_CLEANUP_SKIPPED id={rid} name={name!r}", flush=True)
                continue
            delete_routine_api(rid)
            print(f"TEST_ARTIFACT_CLEANUP_OK id={rid}", flush=True)
        except Exception as exc:
            print(f"TEST_ARTIFACT_CLEANUP_FAILED id={rid} {type(exc).__name__}: {exc}", flush=True)


def _smoke_test():
    if os.getenv("JEFIT_ROUTINE_SMOKE_TEST") != "1":
        return
    created_id = None
    try:
        created = create_routine_api(
            "MCP Test", "Temporary validation routine. Safe to delete.",
            "general", "intermediate", "number",
        )
        created_id = str(created.get("id"))
        days = created.get("days") if isinstance(created.get("days"), list) else []
        if not created_id or created_id == "None" or not days:
            raise RuntimeError("created routine or initial day missing")
        first_id = str(days[0].get("id"))
        update_day_api(first_id, name="MCP Test Day", rest_day=False)

        matches = search_exercises_api("bench", 5)
        if not matches:
            raise RuntimeError("exercise search returned no bench exercise")
        selected = matches[0]
        added_exercise = add_exercise_to_day_api(
            first_id, str(selected["id"]), sets=2, reps=7,
            rest_seconds=75, weight_lbs=None, duration=0, set_type="default",
        )

        added_day = add_routine_day_api(
            created_id, name="MCP Test Rest", rest_day=True, index=2
        )
        verified = get_routine_api(created_id)
        print(
            "ROUTINE_SMOKE_TEST_OK "
            f"id={created_id} days={len(verified.get('days') or [])} "
            f"exercise={selected.get('name')!r} day_exercise={added_exercise.get('day_exercise_id')} "
            f"added_day={added_day.get('id')}",
            flush=True,
        )
    except Exception as exc:
        print(f"ROUTINE_SMOKE_TEST_FAILED {type(exc).__name__}: {exc}", flush=True)
        raise
    finally:
        if created_id:
            try:
                delete_routine_api(created_id)
                print(f"ROUTINE_SMOKE_TEST_CLEANUP_OK id={created_id}", flush=True)
            except Exception as cleanup_exc:
                print(f"ROUTINE_SMOKE_TEST_CLEANUP_FAILED id={created_id}: {cleanup_exc}", flush=True)


def main():
    _cleanup_test_artifacts()
    _smoke_test()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    path = os.getenv("MCP_PATH", "/mcp")
    if not path.startswith("/"):
        path = "/" + path
    mcp.run(host=host, port=port, path=path, transport="streamable-http")


if __name__ == "__main__":
    main()
