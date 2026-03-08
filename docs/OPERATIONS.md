# SplavVPN Bot — OPERATIONS.md

Практические инструкции эксплуатации: запуск, обновление, диагностика, бэкапы.

---

## 1) Компоненты стенда

- **VPN сервер**: отдельный VPS (AmneziaWG/контейнер).
- **Панель**: `amneziavpnphp` (Web UI + REST API).
- **Бот**: Python `python-telegram-bot`, подключается к панели по API, хранит данные в Postgres.
- **DB бота**: Postgres (локально/на VPS) с таблицами `users`, `profiles`, `invites`, `relationships`, `billing_members`, etc.

---

## 2) Переменные окружения (.env)

Минимально для бота:
- `BOT_TOKEN`
- `PANEL_BASE_URL`
- `PANEL_ADMIN_EMAIL`
- `PANEL_ADMIN_PASSWORD`
- `BOT_DB_DSN`
- `ACCESS_CHAT_ID`
- `ADMIN_TG_IDS`
- `INVITE_TTL_DAYS`

Рекомендации:
- `.env` не коммитить.
- Для VPS использовать отдельного пользователя и ограниченные права.

---

## 3) Локальный запуск бота (Windows)

### 3.1) venv
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 3.2) Postgres (dev)
```powershell
docker compose -f docker-compose.dev.yml up -d
```

### 3.3) Миграция схемы
PowerShell вариант:
```powershell
$cid = docker ps -q --filter "name=bot-db"
Get-Content .pp\db\migrations_init.sql | docker exec -i $cid psql -U vpn_bot -d vpn_bot
```

### 3.4) Запуск
```powershell
python run.py
```

---

## 4) Типовые проверки (диагностика)

### 4.1) Проверка панели из бота
- `/health` (ADMIN/MODERATOR)

### 4.2) Проверка профиля пользователя
- `/status` (у пользователя)

### 4.3) Получение ключа
- `/request` → выбрать `/request_config` / `/request_text` / `/request_qr`

---

## 5) Инвайты и доступ

### 5.1) Admin-invite
1) Админ: `/invite_create`
2) Пользователь открывает ссылку `start admin_<code>`
3) Админ: `/approve_activation_<id>` или `/reject_activation_<id>`

### 5.2) Guest-invite
1) Плательщик: `/request_for`
2) Гость открывает ссылку `start guest_<code>`
3) Гость получает роль INVITED_GUEST

---

## 6) Удаление пользователя (revoke + purge)

Команда (ADMIN/MODERATOR):
- `/delete_<tg_id>`

Семантика:
1) `revoke` клиента в панели (`POST /api/clients/{id}/revoke`)
2) удаление пользователя из БД бота каскадом

---

## 7) Бэкап и восстановление

### 7.1) Бэкап Postgres (DB бота)
Пример для docker dev:
```bash
CID=$(docker ps -q --filter "name=bot-db")
docker exec -t "$CID" pg_dump -U vpn_bot -d vpn_bot > bot_db_backup.sql
```

Восстановление:
```bash
CID=$(docker ps -q --filter "name=bot-db")
cat bot_db_backup.sql | docker exec -i "$CID" psql -U vpn_bot -d vpn_bot
```

### 7.2) Бэкап панели
Зависит от того, где хранится состояние панели (DB + серверные файлы). Минимально:
- бэкап БД панели (MySQL)
- бэкап конфигов/ключей (если панель хранит их на диске или в контейнере)

---

## 8) Частые проблемы

### 8.1) Telegram: “Can't parse entities …”
Причина: неподдерживаемый HTML тег или неэкранированные `<...>`.
Решение: использовать только whitelist тегов и экранировать текст.

### 8.2) QR “Image_process_failed”
Причина: панель вернула не PNG (JSON/SVG/HTML).
Решение: в `PanelClient.get_client_qr_png()` проверять Content-Type и/или декодировать base64.

### 8.3) Пользователь не может открыть доступ
- Проверь его роль через `/status`
- Для billing-member: нужен approve admin-invite
- Для гостя: нужна активация guest-invite

---

## 9) Рекомендации перед production

- Перейти с `print()` на `logging` и убрать чувствительные данные из логов.
- Добавить rate limiting на `/request_*`, `/request_for`, `/invite_create`.
- Включить hardening VPS (ssh keys, fail2ban, firewall).
- Разнести панели и бота на отдельный VPS (как планировалось).
