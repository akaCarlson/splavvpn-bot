import time
import requests
import base64

class PanelClient:
    def __init__(self, base_url: str, email: str, password: str, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.timeout = timeout
        self._token = None
        self._token_expire_ts = 0

    def _auth(self):
        url = f"{self.base_url}/api/auth/token"
        r = requests.post(url, data={"email": self.email, "password": self.password}, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise RuntimeError(f"Auth failed: {data}")
        self._token = data["token"]
        self._token_expire_ts = time.time() + int(data.get("expires_in", 3600)) - 30

    def _headers(self):
        if not self._token or time.time() >= self._token_expire_ts:
            self._auth()
        return {"Authorization": f"Bearer {self._token}"}

    def get_servers(self):
        url = f"{self.base_url}/api/servers"
        r = requests.get(url, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def create_client(self, server_id: int, name: str):
        url = f"{self.base_url}/api/clients/create"
        r = requests.post(
            url,
            json={"server_id": server_id, "name": name},
            headers=self._headers(),
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def get_client_config_text(self, client_id: int) -> str:
        url = f"{self.base_url}/api/clients/{client_id}/details"
        print(f"Requesting client config for client_id={client_id} with url={url}")
        r = requests.get(url, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return data["client"]["config"]
    
    def healthcheck(self) -> dict:
        result = {
            "auth": False,
            "servers_ok": False,
            "active_server_id": None,
            "clients_list_ok": False,
            "clients_count": None,
            "client_details_ok": None,   # None если клиентов нет
            "config_present": None,      # None если клиентов нет
            "error": None,
        }

        try:
            # 1) servers => также проверяет auth через _headers()
            servers_data = self.get_servers()
            result["auth"] = True
            servers = servers_data.get("servers", []) if isinstance(servers_data, dict) else []
            result["servers_ok"] = True

            # active server
            active = None
            for s in servers:
                if isinstance(s, dict) and s.get("status") == "active":
                    active = s
                    break
            if not active and servers:
                active = servers[0] if isinstance(servers[0], dict) else None

            if not active:
                return result

            server_id = active.get("id")
            result["active_server_id"] = server_id

            # 2) clients list for active server
            clients_data = self.list_clients_by_server(int(server_id))
            result["clients_list_ok"] = True
            clients = clients_data.get("clients", []) if isinstance(clients_data, dict) else []
            result["clients_count"] = len(clients)

            # 3) if there is at least one client -> check details/config endpoint
            if clients:
                cid = clients[0].get("id")
                if cid:
                    details_url = f"{self.base_url}/api/clients/{int(cid)}/details"
                    print(f"Healthcheck: requesting client details url={details_url}")
                    r = requests.get(details_url, headers=self._headers(), timeout=self.timeout)
                    r.raise_for_status()
                    data = r.json()
                    result["client_details_ok"] = True
                    cfg = (data.get("client") or {}).get("config")
                    result["config_present"] = bool(isinstance(cfg, str) and cfg.strip())
                else:
                    result["client_details_ok"] = False
                    result["config_present"] = False

            return result

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}"
            return result

    def get_client_qr_png(self, client_id: int) -> bytes:
        url = f"{self.base_url}/api/clients/{client_id}/qr"
        print(f"Requesting client QR for client_id={client_id} with url={url}")

        r = requests.get(url, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()

        ct = (r.headers.get("Content-Type") or "").lower()
        body = r.content

        # 1) Прямой PNG
        if "image/png" in ct and body.startswith(b"\x89PNG\r\n\x1a\n"):
            return body

        # 2) JSON (часто: {"qr": "data:image/png;base64,..."} или {"qr_code": "..."} )
        if "application/json" in ct or body.lstrip().startswith(b"{"):
            j = r.json()
            # попробуем найти строку с base64
            candidates = []
            for k, v in j.items():
                if isinstance(v, str):
                    candidates.append(v)

            for s in candidates:
                if s.startswith("data:image/png;base64,"):
                    b64 = s.split(",", 1)[1]
                    raw = base64.b64decode(b64)
                    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
                        return raw
                # чистая base64 без data-uri
                try:
                    raw = base64.b64decode(s, validate=True)
                    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
                        return raw
                except Exception:
                    pass

            raise RuntimeError(f"/qr returned JSON but no PNG found. keys={list(j.keys())}")

        # 3) Если панель отдаёт SVG — пока не конвертим, сообщаем
        if "image/svg" in ct or body.lstrip().startswith(b"<svg"):
            raise RuntimeError("Panel returned SVG QR. Need SVG->PNG conversion (cairosvg) or send as document.")

        # 4) Любой другой ответ (HTML error и т.п.)
        head = body[:200]
        raise RuntimeError(f"/qr returned unsupported content-type={ct}, first_bytes={head!r}")



    def iter_servers(self):
        data = self.get_servers()
        return data.get("servers", []) if isinstance(data, dict) else []
    
    def list_clients_by_server(self, server_id: int):
        url = f"{self.base_url}/api/servers/{server_id}/clients"
        print(f"Requesting clients for server_id={server_id} with url={url}")
        r = requests.get(url, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def find_client_by_name_any_server(self, name: str) -> dict | None:
        for s in self.iter_servers():
            sid = s.get("id")
            if not sid:
                continue
            data = self.list_clients_by_server(int(sid))
            clients = data.get("clients", []) if isinstance(data, dict) else []
            for c in clients:
                if isinstance(c, dict) and c.get("name") == name:
                    return {"server": s, "client": c}
        return None


