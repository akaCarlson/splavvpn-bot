# SplavVPN Bot — FRD v1.1

**Дата:** 2026-02-20  
**Скоуп:** Telegram-бот + Amnezia Panel (amneziavpnphp) + VPN сервер(а)  
**Цель:** самообслуживание по получению ключей AmneziaWG/Amnezia, инвайты, базовая админка.

---

## 1. Термины

- **Панель** — `amneziavpnphp` (Web UI + REST API с JWT).
- **Профиль** — 1:1 соответствие Telegram-пользователя и VPN-клиента в панели (`profiles` в БД бота).
- **Легитимный пользователь** — role ∈ {ADMIN, MODERATOR, CHAT_MEMBER, BILLING_MEMBER, INVITED_GUEST}.
- **Клубный чат** — Telegram-чат, членство в котором даёт доступ “по умолчанию”.
- **Owner** — плательщик, который создал guest-invite; гость входит в его контур.

---

## 2. FR-01. Канал и базовые ограничения

### FR-01.1 Private-only
- Бот работает **только в личных сообщениях** (`private_only`).
- Любые сообщения в group/channel игнорируются.

### FR-01.2 Role-first
- Любое действие начинается с вычисления **effective role** (`with_role`).
- Далее применяется проверка доступа (`require_roles`).

### FR-01.3 Форматирование сообщений
- Системные меню и справка используют **Telegram HTML** (`parse_mode="HTML"`) из-за нестабильности Markdown entities.
- Используются только поддерживаемые теги Telegram HTML (`<b> <i> <code> <pre> <a>`).  
  Пример: `<hr>` **не поддерживается**.

---

## 3. FR-02. Роли

### FR-02.1 Набор ролей
- **ADMIN**
- **MODERATOR**
- **CHAT_MEMBER** — член клубного чата (через `getChatMember`)
- **BILLING_MEMBER** — плательщик (назначается через admin-invite + approve)
- **INVITED_GUEST** — гость, приглашённый плательщиком
- **NO_ACCESS**

### FR-02.2 Приоритет определения роли (effective role)
1) ADMIN (по списку `ADMIN_TG_IDS`)  
2) MODERATOR (если настроен список модераторов)  
3) CHAT_MEMBER (проверка членства в клубном чате)  
4) BILLING_MEMBER (запись в `billing_members`)  
5) INVITED_GUEST (активная запись в `relationships`)  
6) NO_ACCESS

---

## 4. FR-03. Доступ в бота

### FR-03.1 Доступ по членству в клубном чате
- Если пользователь состоит в клубном чате → роль **CHAT_MEMBER**, доступ разрешён.

### FR-03.2 Активация по admin-invite
- Пользователь запускает бота по `start admin_<code>`.
- Создаётся `ActivationRequest(PENDING)`.
- ADMIN/MODERATOR выполняет:
  - `/approve_activation_<id>` → пользователь становится **BILLING_MEMBER**
  - `/reject_activation_<id>` → активация отклоняется

### FR-03.3 Активация по guest-invite
- Пользователь запускает бота по `start guest_<code>`.
- Создаётся связь `relationships(guest → owner)` и роль **INVITED_GUEST**.

---

## 5. FR-04. Инвайты

### FR-04.1 Admin-invite
- Команда: `/invite_create` (только ADMIN/MODERATOR)
- Создаёт `ADMIN_INVITE` с TTL = **7 дней** (`INVITE_TTL_DAYS`)
- Требует approve через ActivationRequest
- Не делегируется: BILLING_MEMBER не может создавать admin-invite

### FR-04.2 Guest-invite
- Команда: `/request_for` (только CHAT_MEMBER/BILLING_MEMBER)
- Создаёт `GUEST_INVITE` с TTL = **7 дней**
- Owner = плательщик, создавший invite
- Активированный пользователь становится INVITED_GUEST и входит в контур owner

---

## 6. FR-05. Выдача VPN-ключей (актуальная)

### FR-05.1 Профилирование
- **1 пользователь = 1 профиль**.
- Имя профиля стабильно: `tg_<tg_id>` (не зависит от username).

### FR-05.2 Выдача без Approve
- Любой легитимный пользователь получает ключ **без approve**.

### FR-05.3 Команды
- `/request` — меню форматов выдачи:
  - `/request_qr` — QR (берётся из панели `/api/clients/{id}/qr`, приводится к PNG)
  - `/request_text` — текст (HTML `<pre>...</pre>`)
  - `/request_config` — файл `.conf`
- `/status` — агрегированный статус: роль, tg_id, профиль в панели, sent/received (если доступно)

### FR-05.4 Алгоритм “ensure profile”
При выдаче ключа бот:
1) читает `profiles` по `tg_id`
2) если профиля нет:
   - ищет клиента в панели по имени `tg_<tg_id>`
   - если не найден — создаёт клиента в панели
3) сохраняет `profiles(tg_id, server_id, client_id, name)`
4) выдаёт ключ в выбранном формате

---

## 7. FR-06. Инструкции и справка

### FR-06.1 Help-архитектура
- `/start` отображает **меню команд по роли** (с секциями/разделителями/эмодзи).
- `/help` показывает **оглавление** справки по роли.
- Help-страницы — отдельные команды:
  - `/help_android`, `/help_iphone`, `/help_windows`, `/help_macos`
  - `/help_bot`
  - `/help_billing` (пока заглушка)
- Контент справки хранится в `content/help/*.html` и отдаётся с `parse_mode="HTML"`.

> Примечание: исходные `/rules /howitworks /setup /support` заменены на help-команды, т.к. это проще поддерживать и фильтровать по роли.

---

## 8. FR-07. Биллинг (упрощённый) — статус

### FR-07.1 Задумано
- Счета/напоминания: только плательщикам (CHAT_MEMBER и BILLING_MEMBER)
- Счёт owner включает owner + всех активных INVITED_GUEST, приглашённых им
- Рассылка: 1/5/10 числа
- “Оплатил” → PAYMENT_PENDING → подтверждение админом → PAID
- Санкции: “не продлевать” / expiry

### FR-07.2 Реализация
- В БД заложена таблица `payments`, в меню есть секция “Денежки” (placeholder).
- **Функционал биллинга пока не реализован**.

---

## 9. FR-08. Рассылки и миграции — статус

### FR-08.1 `/broadcast`
- План: `/broadcast` для сегментов (минимум 2 сегмента) — ADMIN/MODERATOR
- **Пока не реализовано**

### FR-08.2 Миграции ключей
- План: персональная рассылка обновлённых ключей при миграции сервера — v1
- **Пока не реализовано**

---

## 10. FR-ADM-01. Админское удаление пользователя (реализовано)

- Команда: `/delete_<tg_id>` (только ADMIN/MODERATOR)
- Семантика:
  1) находит профиль пользователя (`profiles.client_id`)
  2) выполняет **revoke** в панели (`POST /api/clients/{id}/revoke`)
  3) удаляет пользователя из БД бота (каскадно чистит связи)
  4) уведомляет пользователя (best effort)

---

# Command Reference (v1.1)

## Легенда ролей
- **LEGIT**: ADMIN, MODERATOR, CHAT_MEMBER, BILLING_MEMBER, INVITED_GUEST  
- **PAYERS**: ADMIN, MODERATOR, CHAT_MEMBER, BILLING_MEMBER  
- **ADMINS**: ADMIN, MODERATOR  

## Пользовательские команды
| Команда | Роли | Назначение |
|---|---|---|
| `/start` | любые | Показывает меню команд по роли; обрабатывает `start admin_<code>` и `start guest_<code>` |
| `/request` | LEGIT | Показывает меню форматов выдачи ключа |
| `/request_qr` | LEGIT | Выдаёт QR для импорта в клиент |
| `/request_text` | LEGIT | Выдаёт текстовый ключ (в `<pre>`) |
| `/request_config` | LEGIT | Выдаёт `.conf` файлом |
| `/status` | LEGIT, NO_ACCESS | Статус: role, tg_id, профиль в панели, метрики (если есть); для NO_ACCESS — ограниченная версия |
| `/help` | любые | Оглавление справки по роли |
| `/help_android` | LEGIT | Настройка Android |
| `/help_iphone` | LEGIT | Настройка iPhone/iOS |
| `/help_windows` | LEGIT | Настройка Windows |
| `/help_macos` | LEGIT | Настройка macOS |
| `/help_bot` | LEGIT | Логика работы бота, роли, ключи, инвайты |
| `/help_billing` | PAYERS | Биллинг (пока заглушка) |

## Инвайты
| Команда | Роли | Назначение |
|---|---|---|
| `/invite_create` | ADMINS | Создать admin-invite (TTL 7d) |
| `/request_for` | PAYERS | Создать guest-invite (TTL 7d) |

## Служебные (админские)
| Команда | Роли | Назначение |
|---|---|---|
| `/approve_activation_<id>` | ADMINS | Одобрить ActivationRequest |
| `/reject_activation_<id>` | ADMINS | Отклонить ActivationRequest |
| `/health` | ADMINS | Проверка панели |
| `/delete_<tg_id>` | ADMINS | Revoke в панели + purge пользователя в БД бота |

---

# NFR — нефункциональные требования (v1.1)

## NFR-01. Безопасность и секреты
- Все секреты хранятся **только в `.env`** (не коммитятся):  
  `BOT_TOKEN`, `PANEL_*`, `BOT_DB_DSN`, `ACCESS_CHAT_ID`, `ADMIN_TG_IDS`, т.п.
- JWT-токены панели:
  - не логируются целиком (в логах допускаются только маскированные значения при отладке; в идеале — не логировать).
- Секреты и ключи пользователей (PrivateKey) не сохраняются в БД бота — бот хранит только `client_id/server_id` для доступа к панели.

## NFR-02. Контроль доступа
- Любые админские действия закрыты `require_roles(Role.ADMIN, Role.MODERATOR)`.
- Бот игнорирует все не-private апдейты.
- Для команд с параметрами требуется строгая валидация входа.

## NFR-03. Идемпотентность и отсутствие дублей
- 1 пользователь = 1 профиль обеспечивается:
  - стабильным именем `tg_<tg_id>`
  - и таблицей `profiles` (source of truth)
- `/request_*` идемпотентны: повторная выдача не создаёт новый клиент.

## NFR-04. Надёжность и обработка ошибок
- Везде используется `tg_error_guard`:
  - ошибки сети/HTTP превращаются в понятное сообщение пользователю (без утечки секретов).
- Все операции с панелью должны иметь таймаут.

## NFR-05. Логирование
- Разрешены `print()` логи (dev/stage).
- Перед production:
  - заменить на `logging` со строгими уровнями (`INFO/WARN/ERROR`)
  - исключить любые ключи/токены/конфиги из логов.

## NFR-06. Производительность и лимиты
- Сетевая работа минимизируется:
  - сначала `profiles` из БД, затем панель
- Рекомендовано (в v1):
  - ограничение частоты `/request_*` на пользователя (rate limit)
  - защита от спама командами `/invite_create` и `/request_for`.

## NFR-07. Совместимость Telegram HTML
- Справка хранится в `.html` и использует только поддерживаемые теги.
- Все потенциально опасные символы (`<`, `>`) в меню экранируются.

## NFR-08. Эксплуатация (observability)
- Админ должен иметь возможность быстро проверить:
  - доступность панели (`/health`)
  - статус пользователя (`/status`)
- Рекомендовано (v1):
  - структурированный health (panel auth, endpoints, db connectivity).
