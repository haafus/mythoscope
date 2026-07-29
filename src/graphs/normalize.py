def is_empty(value) -> bool:
    if value is None or value == "" or value == [] or value == {}:
        return True
    # includes the null-placeholders the LLM emits for a missing value (N/A, none, …);
    # "unknown" is intentionally excluded — it can be legitimate metadata (e.g. "Origin: Unknown").
    return isinstance(value, str) and value.strip().lower() in ("", "nan", "n/a", "na", "none", "null")


def norm_name(value) -> str:
    return str(value).strip().lower()
