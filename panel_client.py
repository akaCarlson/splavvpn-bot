import time
import requests

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
        r = requests.get(url, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return data["client"]["config"]
    
    def iter_servers(self):
        data = self.get_servers()
        return data.get("servers", []) if isinstance(data, dict) else []
    
    def list_clients_by_server(self, server_id: int):
        url = f"{self.base_url}/api/clients"
        r = requests.get(url, params={"server_id": server_id}, headers=self._headers(), timeout=self.timeout)
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


