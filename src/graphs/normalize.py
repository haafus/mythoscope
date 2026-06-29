def is_empty(value) -> bool:
    if value is None or value == "" or value == []:
        return True
    return isinstance(value, str) and value.strip().lower() == "nan"


def norm_name(value) -> str:
    return str(value).strip().lower()
