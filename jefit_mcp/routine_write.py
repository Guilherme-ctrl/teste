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
        detail = (response.text or response.reason or "request_failed")[:500]
        raise JefitApiError(method, path, response.status_code, detail)
    if not response.content:
        return None
    try:
        payload = response.json()
    except ValueError:
        return response.text
    return _unwrap(payload) if unwrap else payload


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


def get_routine_api(routine_id: int) -> dict:
    data = api("GET", f"/api/v2/routines/{int(routine_id)}")
    if isinstance(data, dict):
        return data
    raise RuntimeError("Unexpected JEFIT routine response")


def _routine_id(created: Any) -> int | None:
    if isinstance(created, int):
        return created
    if isinstance(created, str) and created.isdigit():
        return int(created)
    if isinstance(created, dict):
        for key in ("id", "routine_id", "routineId"):
            value = created.get(key)
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                return int(value)
        for key in ("routine", "data"):
            nested = created.get(key)
            value = _routine_id(nested)
            if value is not None:
                return value
    return None


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

    created = api("POST", "/api/v2/user/routines", {"create_day": True})
    rid = _routine_id(created)

    # The current JEFIT builder returns the created routine, but keep a safe
    # fallback in case the response shape changes: locate the newest routine
    # without modifying any pre-existing routine.
    if rid is None:
        routines = list_routines_api()
        candidate_ids = [
            int(r["id"]) for r in routines
            if isinstance(r, dict) and str(r.get("id", "")).isdigit()
        ]
        if not candidate_ids:
            raise RuntimeError("Routine was created but its id could not be resolved")
        rid = max(candidate_ids)

    patch = {
        "name": name.strip(),
        "description": description,
        "focus": focus,
        "difficulty": difficulty,
        "day_indexing_style": day_indexing_style,
    }
    api("PATCH", f"/api/v2/routines/{rid}", {"data": patch})
    return get_routine_api(rid)


def add_routine_day_api(
    routine_id: int,
    name: str | None = None,
    rest_day: bool = False,
    index: int | None = None,
    day_of_week: int | None = None,
) -> dict:
    routine = get_routine_api(routine_id)
    days = routine.get("days") if isinstance(routine.get("days"), list) else []
    idx = int(index) if index is not None else len(days) + 1
    if idx < 1:
        raise ValueError("index must be >= 1")
    if day_of_week is not None and not 0 <= int(day_of_week) <= 6:
        raise ValueError("day_of_week must be 0..6 when provided")

    payload = {
        "rest_day": bool(rest_day),
        "index": idx,
        "day_of_week": int(day_of_week) if day_of_week is not None else None,
        "name": (name or f"Day {idx}").strip(),
        "estimated_duration": None,
        "routine_id": int(routine_id),
        "day_exercises": [],
        "reaction": None,
        "reaction_count": 0,
        "deload": False,
    }
    result = api("POST", f"/api/v2/routines/{int(routine_id)}/days", {"data": payload})
    if isinstance(result, dict):
        return result
    return {"result": result, "routine_id": int(routine_id), "index": idx}


def update_routine_api(routine_id: int, **fields: Any) -> dict:
    allowed = {"name", "description", "focus", "difficulty", "day_indexing_style"}
    patch = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not patch:
        raise ValueError("No supported routine fields supplied")
    api("PATCH", f"/api/v2/routines/{int(routine_id)}", {"data": patch})
    return get_routine_api(routine_id)


def update_day_api(day_id: int, **fields: Any) -> Any:
    allowed = {"name", "rest_day", "index", "day_of_week", "estimated_duration", "deload"}
    patch = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not patch:
        raise ValueError("No supported day fields supplied")
    return api("PATCH", f"/api/v2/days/{int(day_id)}", {"data": patch})


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
    if isinstance(exercise, int) or str(exercise).isdigit():
        wanted = str(exercise)
        for key, item in db.items():
            if str(key) == wanted or str(item.get("id")) == wanted:
                return item
        return {"id": int(wanted), "name": f"Exercise {wanted}"}

    q = _normalize(str(exercise))
    exact = []
    partial = []
    for key, item in db.items():
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        norm = _normalize(name)
        if norm == q:
            exact.append({**item, "id": item.get("id", key)})
        elif q and q in norm:
            partial.append({**item, "id": item.get("id", key)})
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


def add_exercise_to_day_api(
    day_id: int,
    exercise: str | int,
    sets: int = 3,
    reps: int = 8,
    rest_seconds: int = 60,
    weight_lbs: float = 0,
    duration: int = 0,
    set_type: str = "default",
    sort_order: int = 0,
) -> dict:
    if set_type not in {"default", "warm-up", "failure", "drop"}:
        raise ValueError("set_type must be default, warm-up, failure, or drop")
    count = int(sets)
    if count < 1 or count > 30:
        raise ValueError("sets must be between 1 and 30")
    if int(reps) < 0 or int(rest_seconds) < 0 or int(duration) < 0:
        raise ValueError("reps/rest_seconds/duration cannot be negative")

    resolved = resolve_exercise(exercise)
    exercise_id = int(resolved["id"])
    payload = {
        "exercise_id": exercise_id,
        "sort_order": int(sort_order),
        "sets": [
            {
                "id": None,
                "type": set_type,
                "sort_order": i,
                "weight_lbs": float(weight_lbs),
                "reps": int(reps),
                "duration": int(duration),
                "rest_time": int(rest_seconds),
            }
            for i in range(count)
        ],
    }
    result = api("POST", f"/api/v2/days/{int(day_id)}/day_exercises", {"data": payload})
    return {
        "exercise": {"id": exercise_id, "name": resolved.get("name")},
        "day_exercise": result,
    }


def update_day_exercise_sets_api(day_exercise_id: int, sets: list[dict]) -> Any:
    if not sets:
        raise ValueError("sets cannot be empty")
    normalized = []
    for i, item in enumerate(sets):
        if not isinstance(item, dict):
            raise ValueError("each set must be an object")
        set_type = item.get("type", "default")
        if set_type not in {"default", "warm-up", "failure", "drop"}:
            raise ValueError(f"invalid set type at index {i}")
        normalized.append({
            "id": item.get("id"),
            "type": set_type,
            "sort_order": int(item.get("sort_order", i)),
            "weight_lbs": float(item.get("weight_lbs", 0)),
            "reps": int(item.get("reps", 0)),
            "duration": int(item.get("duration", 0)),
            "rest_time": int(item.get("rest_time", 60)),
        })
    return api(
        "PATCH",
        f"/api/v2/day_exercises/{int(day_exercise_id)}",
        {"data": {"sets": normalized}},
    )
