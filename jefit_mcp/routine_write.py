import re
import unicodedata
from typing import Any

import requests

from auth import get_access_token
from workout_info import load_exercise_db

BASE = "https://www.jefit.com"
TIMEOUT = 25


class JefitApiError(RuntimeError):
    def __init__(self, method: str, path: str, status: int, detail: str):
        self.method = method
        self.path = path
        self.status = status
        self.detail = detail
        super().__init__(f"JEFIT {method} {path} failed: HTTP {status}: {detail}")


def _headers() -> dict[str, str]:
    token = get_access_token()
    return {
        "content-type": "application/json",
        "accept": "application/json",
        "Cookie": f"jefitAccessToken={token}",
    }


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def api(method: str, path: str, body: dict | None = None, *, unwrap: bool = True) -> Any:
    response = requests.request(
        method,
        BASE + path,
        headers=_headers(),
        json=body,
        timeout=TIMEOUT,
    )
    if not response.ok:
        detail = (response.text or response.reason or "request_failed")[:1000]
        raise JefitApiError(method, path, response.status_code, detail)
    if not response.content:
        return None
    try:
        payload = response.json()
    except ValueError:
        return response.text
    return _unwrap(payload) if unwrap else payload


def _safe_id(value: Any, label: str = "id") -> str:
    value = str(value).strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError(f"Invalid {label}")
    return value


def _extract_id(payload: Any) -> str | None:
    if isinstance(payload, (int, str)):
        value = str(payload).strip()
        return value if value else None
    if isinstance(payload, dict):
        for key in ("id", "routine_id", "routineId", "day_id", "dayId", "day_exercise_id", "dayExerciseId"):
            if key in payload and payload[key] not in (None, ""):
                return str(payload[key])
        for key in ("routine", "day", "day_exercise", "data"):
            if key in payload:
                nested = _extract_id(payload[key])
                if nested:
                    return nested
    return None


def list_routines_api() -> list[dict]:
    data = api("GET", "/api/v2/user/routines")
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("routines", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    raise RuntimeError(f"Unexpected JEFIT routines response: {type(data).__name__}")


def get_routine_api(routine_id: str | int) -> dict:
    rid = _safe_id(routine_id, "routine_id")
    data = api("GET", f"/api/v2/routines/{rid}")
    if isinstance(data, dict):
        return data
    raise RuntimeError("Unexpected JEFIT routine response")


def create_routine_api(
    name: str,
    description: str = "",
    focus: str = "general",
    difficulty: str = "intermediate",
    day_indexing_style: str = "number",
) -> dict:
    if not name.strip():
        raise ValueError("name cannot be empty")
    if focus not in {"general", "bulking", "cutting", "sport"}:
        raise ValueError("focus must be general, bulking, cutting, or sport")
    if difficulty not in {"beginner", "intermediate", "advanced"}:
        raise ValueError("difficulty must be beginner, intermediate, or advanced")
    if day_indexing_style not in {"number", "weekday"}:
        raise ValueError("day_indexing_style must be number or weekday")

    # Exact current Routine Builder flow: create a private routine and its first day.
    created = api("POST", "/api/v2/user/routines", {"create_day": True})
    rid = _extract_id(created)
    if not rid:
        raise RuntimeError(f"Routine was created but its id could not be resolved: {created!r}")
    rid = _safe_id(rid, "routine_id")

    patch = {
        "name": name.strip(),
        "description": description,
        "focus": focus,
        "difficulty": difficulty,
        "day_indexing_style": day_indexing_style,
    }
    api("PATCH", f"/api/v2/routines/{rid}", {"data": patch})
    return get_routine_api(rid)


def update_routine_api(routine_id: str | int, **fields: Any) -> dict:
    rid = _safe_id(routine_id, "routine_id")
    allowed = {"name", "description", "focus", "difficulty", "day_indexing_style"}
    patch = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not patch:
        raise ValueError("No supported routine fields supplied")
    api("PATCH", f"/api/v2/routines/{rid}", {"data": patch})
    return get_routine_api(rid)


def delete_routine_api(routine_id: str | int) -> None:
    rid = _safe_id(routine_id, "routine_id")
    api("DELETE", f"/api/v2/routines/{rid}")


def add_routine_day_api(
    routine_id: str | int,
    name: str | None = None,
    rest_day: bool = False,
    index: int | None = None,
    day_of_week: int | None = None,
) -> dict:
    rid = _safe_id(routine_id, "routine_id")
    routine = get_routine_api(rid)
    days = routine.get("days") if isinstance(routine.get("days"), list) else []

    if index is None:
        existing_indexes = [int(d.get("index", 0) or 0) for d in days if isinstance(d, dict)]
        idx = max(existing_indexes, default=0) + 1
    else:
        idx = int(index)
    if idx < 1:
        raise ValueError("index must be >= 1")

    if day_of_week is None:
        existing_dows = [int(d.get("day_of_week", -1) or -1) for d in days if isinstance(d, dict)]
        dow = min(max(existing_dows, default=-1) + 1, 7)
    else:
        dow = int(day_of_week)
    if not 0 <= dow <= 7:
        raise ValueError("day_of_week must be 0..7")

    payload = {
        "day_of_week": dow,
        "name": (name or "New Day").strip(),
        "index": idx,
    }
    result = api("POST", f"/api/v2/routines/{rid}/days", {"data": payload})
    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected add-day response: {result!r}")

    day_id = _extract_id(result)
    if rest_day and day_id:
        result = update_day_api(day_id, rest_day=True)
    return result


def update_day_api(day_id: str | int, **fields: Any) -> dict:
    did = _safe_id(day_id, "day_id")
    allowed = {"name", "rest_day", "index", "day_of_week", "estimated_duration", "deload", "sort_order"}
    patch = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not patch:
        raise ValueError("No supported day fields supplied")
    data = api("PATCH", f"/api/v2/days/{did}", {"data": patch})
    return data if isinstance(data, dict) else {"id": did, "result": data}


def delete_day_api(day_id: str | int) -> None:
    did = _safe_id(day_id, "day_id")
    api("DELETE", f"/api/v2/days/{did}")


def copy_day_api(day_id: str | int, day_of_week: int) -> dict:
    did = _safe_id(day_id, "day_id")
    dow = int(day_of_week)
    if not 0 <= dow <= 7:
        raise ValueError("day_of_week must be 0..7")
    query = (
        "method=copy"
        "&expand=days.day_exercises.interval,days.day_exercises.sets"
        "&sort=days.day_exercises.sort_order,days.day_exercises.index,days.day_exercises.sets.index"
    )
    data = api("POST", f"/api/v2/days/{did}?{query}", {"data": {"day_of_week": dow}})
    if isinstance(data, dict):
        return data
    raise RuntimeError(f"Unexpected copy-day response: {data!r}")


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _exercise_db() -> dict:
    db = load_exercise_db()
    return db if isinstance(db, dict) else {}


def search_exercises_api(query: str, limit: int = 10) -> list[dict]:
    if not query.strip():
        raise ValueError("query cannot be empty")
    limit = max(1, min(int(limit), 50))
    q = _normalize(query)
    matches = []
    for key, exercise in _exercise_db().items():
        if not isinstance(exercise, dict):
            continue
        name = str(exercise.get("name") or "")
        norm = _normalize(name)
        if q in norm:
            score = 0 if norm == q else (1 if norm.startswith(q) else 2)
            matches.append((score, len(name), {
                "id": exercise.get("id", key),
                "name": name,
                "body_parts": exercise.get("body_parts", []),
                "equipment": exercise.get("equipment", []),
                "input_format": exercise.get("input_format"),
            }))
    matches.sort(key=lambda item: (item[0], item[1], item[2]["name"].lower()))
    return [item[2] for item in matches[:limit]]


def resolve_exercise(exercise: str | int) -> dict:
    db = _exercise_db()
    raw = str(exercise).strip()
    if not raw:
        raise ValueError("exercise cannot be empty")

    # Current JEFIT ids include encoded ids such as d_... and u_..., not only numbers.
    for key, item in db.items():
        if not isinstance(item, dict):
            continue
        if str(key) == raw or str(item.get("id", "")) == raw:
            return {**item, "id": item.get("id", key)}

    q = _normalize(raw)
    exact = []
    partial = []
    for key, item in db.items():
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        norm = _normalize(name)
        candidate = {**item, "id": item.get("id", key)}
        if norm == q:
            exact.append(candidate)
        elif q and q in norm:
            partial.append(candidate)
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise ValueError(f"Exercise name is ambiguous: {[x.get('name') for x in exact[:10]]}")
    if len(partial) == 1:
        return partial[0]
    if not partial:
        raise ValueError(f"No JEFIT exercise found matching '{exercise}'")
    names = [f"{x.get('name')} (id={x.get('id')})" for x in partial[:10]]
    raise ValueError("Exercise name is ambiguous. Candidates: " + "; ".join(names))


def update_day_exercise_api(day_exercise_id: str | int, **fields: Any) -> dict:
    deid = _safe_id(day_exercise_id, "day_exercise_id")
    allowed = {
        "rest_time", "number_of_reps", "count", "interval", "superset",
        "index", "sets", "interval_time_enabled",
    }
    patch = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not patch:
        raise ValueError("No supported day-exercise fields supplied")
    data = api("PATCH", f"/api/v2/day_exercises/{deid}", {"data": patch})
    return data if isinstance(data, dict) else {"id": deid, "result": data}


def _normalize_set_change(item: dict, *, fill_defaults: bool) -> dict:
    if not isinstance(item, dict):
        raise ValueError("each set must be an object")
    allowed = {"type", "weight_lbs", "reps", "duration", "rest_time"}
    if fill_defaults:
        result = {
            "reps": int(item.get("reps", 8)),
            "rest_time": int(item.get("rest_time", 60)),
            "duration": int(item.get("duration", 0)),
            "type": item.get("type", "default"),
            "weight_lbs": item.get("weight_lbs", None),
        }
    else:
        result = {k: v for k, v in item.items() if k in allowed}
        for key in ("reps", "rest_time", "duration"):
            if key in result and result[key] is not None:
                result[key] = int(result[key])
    if "weight_lbs" in result and result["weight_lbs"] is not None:
        result["weight_lbs"] = float(result["weight_lbs"])
    if result.get("type", "default") not in {"default", "warm-up", "failure", "drop"}:
        raise ValueError("set type must be default, warm-up, failure, or drop")
    for key in ("reps", "rest_time", "duration"):
        if key in result and result[key] is not None and result[key] < 0:
            raise ValueError(f"{key} cannot be negative")
    return result


def update_day_exercise_sets_api(day_exercise_id: str | int, sets: list[dict]) -> dict:
    if not sets:
        raise ValueError("sets cannot be empty")
    if len(sets) > 30:
        raise ValueError("sets cannot contain more than 30 items")
    # JEFIT treats this as a positional patch array. Supplying a complete change
    # object at every index also lets us establish the exact requested set count.
    changes = [_normalize_set_change(item, fill_defaults=True) for item in sets]
    return update_day_exercise_api(day_exercise_id, sets=changes)


def patch_one_set_api(
    day_exercise_id: str | int,
    set_index: int,
    set_count: int,
    changes: dict,
) -> dict:
    index = int(set_index)
    count = int(set_count)
    if count < 1 or count > 30:
        raise ValueError("set_count must be between 1 and 30")
    if index < 0 or index >= count:
        raise ValueError("set_index is out of range")
    sparse = [{} for _ in range(count)]
    sparse[index] = _normalize_set_change(changes, fill_defaults=False)
    if not sparse[index]:
        raise ValueError("No supported set fields supplied")
    return update_day_exercise_api(day_exercise_id, sets=sparse)


def add_set_api(
    day_exercise_id: str | int,
    current_set_count: int,
    reps: int = 8,
    rest_time: int = 60,
    duration: int = 0,
    set_type: str = "default",
    weight_lbs: float | None = None,
) -> dict:
    count = int(current_set_count)
    if count < 1 or count >= 30:
        raise ValueError("current_set_count must be between 1 and 29")
    payload = [{} for _ in range(count)]
    payload.append(_normalize_set_change({
        "reps": reps,
        "rest_time": rest_time,
        "duration": duration,
        "type": set_type,
        "weight_lbs": weight_lbs,
    }, fill_defaults=True))
    return update_day_exercise_api(day_exercise_id, sets=payload)


def remove_last_set_api(day_exercise_id: str | int, current_set_count: int) -> dict:
    count = int(current_set_count)
    if count <= 1:
        raise ValueError("A day exercise must keep at least one set")
    return update_day_exercise_api(day_exercise_id, sets=[{} for _ in range(count - 1)])


def add_exercise_to_day_api(
    day_id: str | int,
    exercise: str | int,
    sets: int = 3,
    reps: int = 8,
    rest_seconds: int = 60,
    weight_lbs: float | None = None,
    duration: int = 0,
    set_type: str = "default",
) -> dict:
    did = _safe_id(day_id, "day_id")
    count = int(sets)
    if count < 1 or count > 30:
        raise ValueError("sets must be between 1 and 30")
    resolved = resolve_exercise(exercise)
    exercise_id = _safe_id(resolved["id"], "exercise_id")

    # Exact current Routine Builder payload.
    created = api(
        "POST",
        f"/api/v2/days/{did}/day_exercises",
        {"data": {"exercise": {"id": exercise_id}}},
    )
    if not isinstance(created, dict):
        raise RuntimeError(f"Unexpected add-exercise response: {created!r}")
    day_exercise_id = _extract_id(created)
    if not day_exercise_id:
        raise RuntimeError(f"Exercise was added but day_exercise id was not returned: {created!r}")

    prescription = [
        {
            "reps": int(reps),
            "rest_time": int(rest_seconds),
            "duration": int(duration),
            "type": set_type,
            "weight_lbs": weight_lbs,
        }
        for _ in range(count)
    ]
    updated = update_day_exercise_sets_api(day_exercise_id, prescription)
    return {
        "exercise": {"id": exercise_id, "name": resolved.get("name")},
        "day_exercise_id": day_exercise_id,
        "created": created,
        "configured": updated,
    }


def delete_day_exercise_api(day_exercise_id: str | int) -> None:
    deid = _safe_id(day_exercise_id, "day_exercise_id")
    api("DELETE", f"/api/v2/day_exercises/{deid}")


def create_routine_with_days_api(
    name: str,
    days: list[dict],
    description: str = "",
    focus: str = "general",
    difficulty: str = "intermediate",
    day_indexing_style: str = "number",
    cleanup_on_error: bool = True,
) -> dict:
    if not days:
        raise ValueError("days cannot be empty")

    routine = create_routine_api(name, description, focus, difficulty, day_indexing_style)
    rid = _extract_id(routine)
    if not rid:
        raise RuntimeError("Created routine id is missing")

    try:
        routine = get_routine_api(rid)
        existing_days = routine.get("days") if isinstance(routine.get("days"), list) else []
        if not existing_days:
            first = add_routine_day_api(rid, name=str(days[0].get("name") or "Day 1"), index=1,
                                        day_of_week=days[0].get("day_of_week"))
        else:
            first = existing_days[0]
            first_id = _extract_id(first)
            if not first_id:
                raise RuntimeError("Initial routine day id is missing")
            update_day_api(
                first_id,
                name=str(days[0].get("name") or "Day 1"),
                rest_day=bool(days[0].get("rest_day", False)),
                index=int(days[0].get("index", 1)),
                day_of_week=days[0].get("day_of_week"),
            )
            first = {**first, "id": first_id}

        created_days = [first]
        for pos, spec in enumerate(days[1:], start=2):
            created_days.append(add_routine_day_api(
                rid,
                name=str(spec.get("name") or f"Day {pos}"),
                rest_day=bool(spec.get("rest_day", False)),
                index=int(spec.get("index", pos)),
                day_of_week=spec.get("day_of_week"),
            ))

        for spec, day in zip(days, created_days):
            if bool(spec.get("rest_day", False)):
                continue
            day_id = _extract_id(day)
            if not day_id:
                raise RuntimeError(f"Could not resolve created day id for {spec!r}")
            exercises = spec.get("exercises") or []
            if not isinstance(exercises, list):
                raise ValueError("day.exercises must be a list")
            for ex in exercises:
                if not isinstance(ex, dict) or "exercise" not in ex:
                    raise ValueError("each exercise must be an object with an 'exercise' name or id")
                add_exercise_to_day_api(
                    day_id,
                    ex["exercise"],
                    sets=int(ex.get("sets", 3)),
                    reps=int(ex.get("reps", 8)),
                    rest_seconds=int(ex.get("rest_seconds", 60)),
                    weight_lbs=ex.get("weight_lbs", None),
                    duration=int(ex.get("duration", 0)),
                    set_type=str(ex.get("set_type", "default")),
                )
        return get_routine_api(rid)
    except Exception:
        if cleanup_on_error:
            try:
                delete_routine_api(rid)
            except Exception:
                pass
        raise
