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
    create_routine_with_days_api,
    update_routine_api,
    delete_routine_api,
    add_routine_day_api,
    update_day_api,
    copy_day_api,
    delete_day_api,
    search_exercises_api,
    add_exercise_to_day_api,
    update_day_exercise_api,
    update_day_exercise_sets_api,
    patch_one_set_api,
    add_set_api,
    remove_last_set_api,
    delete_day_exercise_api,
)

mcp = FastMCP(
    name="JEFitWorkouts",
    instructions="""
Read JEFIT workout history and create/edit future workout routines.
All dates use YYYY-MM-DD. JEFIT entity IDs may be encoded strings such as u_... or d_....
Only call tools that mutate routines when the user explicitly asks to create or change a routine.
Never delete a routine, day, or exercise unless the user explicitly requests deletion and supplies confirmation.
Creating a routine does not publish it or activate/download it as the current routine.
When an exercise name is ambiguous, call search_exercises first and use the returned exact id.
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
def get_routine(routine_id: str) -> dict:
    """Get one JEFIT routine including its current days/exercises returned by JEFIT."""
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
    Create a private JEFIT routine with its initial day.
    focus: general | bulking | cutting | sport
    difficulty: beginner | intermediate | advanced
    day_indexing_style: number | weekday
    Does not publish or activate the routine.
    """
    return create_routine_api(name, description, focus, difficulty, day_indexing_style)


@mcp.tool
def create_routine_plan(
    name: str,
    days: list[dict],
    description: str = "",
    focus: str = "general",
    difficulty: str = "intermediate",
    day_indexing_style: str = "number",
) -> dict:
    """
    Create a complete private JEFIT routine in one call: metadata, days, exercises, and sets.

    days example:
    [{"name":"Push","exercises":[{"exercise":"Barbell Bench Press","sets":4,"reps":8,"rest_seconds":120}]},
     {"name":"Rest","rest_day":true}]

    Exercise may be an exact JEFIT exercise name or id. If a name is ambiguous,
    call search_exercises first. If any creation step fails, the newly-created
    partial routine is removed automatically. Existing routines are never touched.
    """
    return create_routine_with_days_api(
        name=name,
        days=days,
        description=description,
        focus=focus,
        difficulty=difficulty,
        day_indexing_style=day_indexing_style,
        cleanup_on_error=True,
    )


@mcp.tool
def update_routine(
    routine_id: str,
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
    routine_id: str,
    name: str | None = None,
    rest_day: bool = False,
    index: int | None = None,
    day_of_week: int | None = None,
) -> dict:
    """Add a day to a JEFIT routine without removing existing days."""
    return add_routine_day_api(routine_id, name, rest_day, index, day_of_week)


@mcp.tool
def update_routine_day(
    day_id: str,
    name: str | None = None,
    rest_day: bool | None = None,
    index: int | None = None,
    day_of_week: int | None = None,
    estimated_duration: int | None = None,
    deload: bool | None = None,
    sort_order: int | None = None,
) -> dict:
    """Edit fields on an existing routine day."""
    return update_day_api(
        day_id,
        name=name,
        rest_day=rest_day,
        index=index,
        day_of_week=day_of_week,
        estimated_duration=estimated_duration,
        deload=deload,
        sort_order=sort_order,
    )


@mcp.tool
def copy_routine_day(day_id: str, day_of_week: int) -> dict:
    """Duplicate an existing JEFIT routine day to the supplied weekday index."""
    return copy_day_api(day_id, day_of_week)


@mcp.tool
def search_exercises(query: str, limit: int = 10) -> list[dict]:
    """Search the JEFIT exercise catalog by name before adding exercises to a routine."""
    return search_exercises_api(query, limit)


@mcp.tool
def add_exercise_to_day(
    day_id: str,
    exercise: str,
    sets: int = 3,
    reps: int = 8,
    rest_seconds: int = 60,
    weight_lbs: float | None = None,
    duration: int = 0,
    set_type: str = "default",
) -> dict:
    """
    Add an exercise to a routine day and configure its prescribed sets.
    exercise may be an exact name or JEFIT id (including d_.../u_...).
    set_type: default | warm-up | failure | drop.
    """
    return add_exercise_to_day_api(
        day_id, exercise, sets, reps, rest_seconds, weight_lbs, duration, set_type
    )


@mcp.tool
def update_day_exercise(
    day_exercise_id: str,
    rest_time: int | None = None,
    number_of_reps: list[int] | None = None,
    count: int | None = None,
    index: int | None = None,
    interval_time_enabled: bool | None = None,
) -> dict:
    """Update supported fields on an exercise already inside a routine day."""
    return update_day_exercise_api(
        day_exercise_id,
        rest_time=rest_time,
        number_of_reps=number_of_reps,
        count=count,
        index=index,
        interval_time_enabled=interval_time_enabled,
    )


@mcp.tool
def update_day_exercise_sets(day_exercise_id: str, sets: list[dict]) -> dict:
    """
    Set the exact prescription for all sets of one day exercise.
    Each set can contain type, weight_lbs, reps, duration, rest_time.
    The number of objects supplied becomes the requested set count.
    """
    return update_day_exercise_sets_api(day_exercise_id, sets)


@mcp.tool
def update_set(
    day_exercise_id: str,
    set_index: int,
    set_count: int,
    reps: int | None = None,
    weight_lbs: float | None = None,
    duration: int | None = None,
    rest_time: int | None = None,
    set_type: str | None = None,
) -> dict:
    """Patch one set by zero-based index. set_count is the exercise's current number of sets."""
    changes = {}
    if reps is not None:
        changes["reps"] = reps
    if weight_lbs is not None:
        changes["weight_lbs"] = weight_lbs
    if duration is not None:
        changes["duration"] = duration
    if rest_time is not None:
        changes["rest_time"] = rest_time
    if set_type is not None:
        changes["type"] = set_type
    return patch_one_set_api(day_exercise_id, set_index, set_count, changes)


@mcp.tool
def add_set(
    day_exercise_id: str,
    current_set_count: int,
    reps: int = 8,
    rest_time: int = 60,
    duration: int = 0,
    set_type: str = "default",
    weight_lbs: float | None = None,
) -> dict:
    """Append a set using JEFIT's positional set-patch API."""
    return add_set_api(day_exercise_id, current_set_count, reps, rest_time, duration, set_type, weight_lbs)


@mcp.tool
def remove_last_set(day_exercise_id: str, current_set_count: int) -> dict:
    """Remove only the final set from a day exercise; at least one set is retained."""
    return remove_last_set_api(day_exercise_id, current_set_count)


@mcp.tool
def delete_day_exercise(day_exercise_id: str, confirm: bool = False) -> dict:
    """Delete an exercise from a routine day. Must be called with confirm=true."""
    if not confirm:
        raise ValueError("Deletion requires confirm=true")
    delete_day_exercise_api(day_exercise_id)
    return {"deleted": True, "day_exercise_id": day_exercise_id}


@mcp.tool
def delete_routine_day(day_id: str, confirm: bool = False) -> dict:
    """Delete a routine day. Must be called with confirm=true."""
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


def _smoke_test():
    if os.getenv("JEFIT_ROUTINE_SMOKE_TEST") != "1":
        return
    created_id = None
    try:
        created = create_routine_api(
            "MCP Test",
            "Temporary validation routine. Safe to delete.",
            "general",
            "intermediate",
            "number",
        )
        created_id = str(created.get("id"))
        days = created.get("days") if isinstance(created.get("days"), list) else []
        if not created_id or created_id == "None":
            raise RuntimeError("created routine id missing")
        if days:
            first_id = str(days[0].get("id"))
            update_day_api(first_id, name="MCP Test Day", rest_day=False)
        added = add_routine_day_api(created_id, name="MCP Test Rest", rest_day=True, index=2)
        verified = get_routine_api(created_id)
        print(
            f"ROUTINE_SMOKE_TEST_OK id={created_id} days={len(verified.get('days') or [])} added_day={added.get('id')}",
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


def _routine_diag():
    if os.getenv("JEFIT_ROUTINE_DIAG") != "1":
        return
    try:
        raw = api("GET", "/api/v2/user/routines", unwrap=False)
        print("ROUTINE_DIAG_RAW " + json.dumps(raw, ensure_ascii=False, default=str)[:12000], flush=True)
    except Exception as exc:
        print(f"ROUTINE_DIAG_FAILED {type(exc).__name__}: {exc}", flush=True)


def main():
    _smoke_test()
    _routine_diag()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    path = os.getenv("MCP_PATH", "/mcp")
    if not path.startswith("/"):
        path = "/" + path
    mcp.run(host=host, port=port, path=path, transport="streamable-http")


if __name__ == "__main__":
    main()
