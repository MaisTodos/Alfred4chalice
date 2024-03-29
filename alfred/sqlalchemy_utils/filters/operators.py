from sqlalchemy import func

OPERATORS = {
    "is_null": lambda f: f.is_(None),
    "is_not_null": lambda f: f.isnot(None),
    "==": lambda f, a: f == a,
    "eq": lambda f, a: f == a,
    "!=": lambda f, a: f != a,
    "ne": lambda f, a: f != a,
    ">": lambda f, a: f > a,
    "gt": lambda f, a: f > a,
    "<": lambda f, a: f < a,
    "lt": lambda f, a: f < a,
    ">=": lambda f, a: f >= a,
    "ge": lambda f, a: f >= a,
    "<=": lambda f, a: f <= a,
    "le": lambda f, a: f <= a,
    "like": lambda f, a: f.like(a),
    "ilike": lambda f, a: f.ilike(a),
    "not_ilike": lambda f, a: ~f.ilike(a),
    "in": lambda f, a: f.in_(a),
    "not_in": lambda f, a: ~f.in_(a),
    "any": lambda f, a: f.any(a),
    "not_any": lambda f, a: func.not_(f.any(a)),
    "startswith": lambda f, a: f.startswith(a),
}
