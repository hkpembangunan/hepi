import json
def safe_json_dumps(obj):
    return json.dumps(obj, default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o), sort_keys=True, indent=4)