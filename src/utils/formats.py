def truncate_string(value, max_length=128, suffix="..."):
    string_value = str(value)
    string_truncated = string_value[: min(len(string_value), (max_length - len(suffix)))]
    suffix = suffix if len(string_value) > max_length else ""
    return string_truncated + suffix


class plural:
    def __init__(self, value):
        self.value = value

        if isinstance(self.value, list):
            self.value = len(self.value)

    def __format__(self, format_spec):
        v = self.value
        singular, sep, plural = format_spec.partition("|")
        plural = plural or f"{singular}s"
        return f"{v} {plural}" if abs(v) != 1 else f"{v} {singular}"
