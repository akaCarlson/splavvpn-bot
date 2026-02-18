def pick_server(servers_json: dict) -> dict | None:
    items = servers_json.get("servers", []) if isinstance(servers_json, dict) else []
    if not items:
        return None
    # берём первый active, иначе первый
    for s in items:
        if isinstance(s, dict) and s.get("status") == "active":
            return s
    return items[0] if isinstance(items[0], dict) else None