-- 001_init.sql
-- Schema for SplavVPN bot (FR-01..FR-05 baseline, with hooks for FR-07)

-- USERS: минимальный реестр пользователей бота
create table if not exists users (
  tg_id            bigint primary key,
  username         text,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

-- INVITES: два типа инвайтов:
-- ADMIN_INVITE: создаёт ADMIN/MODERATOR, TTL=7d, требует activation approve
-- GUEST_INVITE: создаёт плательщик (/request_for), TTL=7d, активирует INVITED_GUEST и owner relationship
create type invite_type as enum ('ADMIN_INVITE', 'GUEST_INVITE');
create type invite_status as enum ('ACTIVE', 'USED', 'EXPIRED', 'REVOKED');

create table if not exists invites (
  code             text primary key,
  type             invite_type not null,
  created_by_tg_id  bigint not null references users(tg_id) on delete cascade,
  owner_tg_id       bigint references users(tg_id) on delete set null,  -- только для GUEST_INVITE
  status           invite_status not null default 'ACTIVE',
  expires_at       timestamptz not null,
  used_by_tg_id     bigint references users(tg_id) on delete set null,
  created_at       timestamptz not null default now()
);

create index if not exists idx_invites_status_expires on invites(status, expires_at);

-- ACTIVATION REQUESTS: только для admin-invite
create type activation_status as enum ('PENDING', 'APPROVED', 'REJECTED');

create table if not exists activation_requests (
  id               bigserial primary key,
  tg_id            bigint not null references users(tg_id) on delete cascade,
  invite_code      text not null references invites(code) on delete cascade,
  status           activation_status not null default 'PENDING',
  decided_by_tg_id  bigint references users(tg_id) on delete set null,
  decided_at       timestamptz,
  created_at       timestamptz not null default now()
);

create index if not exists idx_activation_pending on activation_requests(status);

-- RELATIONSHIPS: guest -> owner (контур плательщика)
create type relationship_status as enum ('ACTIVE', 'DISABLED');

create table if not exists relationships (
  guest_tg_id      bigint primary key references users(tg_id) on delete cascade,
  owner_tg_id      bigint not null references users(tg_id) on delete cascade,
  status           relationship_status not null default 'ACTIVE',
  created_at       timestamptz not null default now()
);

create index if not exists idx_relationships_owner on relationships(owner_tg_id);

-- BILLING MEMBERS: “назначенные” плательщики после approve admin-invite
-- CHAT_MEMBER определяется динамически через getChatMember и в БД не хранится.
create table if not exists billing_members (
  tg_id            bigint primary key references users(tg_id) on delete cascade,
  activated_by_tg_id bigint references users(tg_id) on delete set null,
  activated_at     timestamptz not null default now()
);

-- PROFILES: FR-05 “1 пользователь = 1 профиль”
-- Это связка tg_id -> client_id/server_id в панели, чтобы не плодить дубликаты.
create table if not exists profiles (
  tg_id            bigint primary key references users(tg_id) on delete cascade,
  server_id        bigint,     -- id сервера в панели
  client_id        bigint,     -- id клиента в панели
  name             text,       -- tg_<id>_<username> или иной
  updated_at       timestamptz not null default now()
);

-- KEY REQUESTS: любая выдача/показ ключа через approve (FR-05)
create type key_request_status as enum ('PENDING', 'APPROVED', 'REJECTED', 'ISSUED', 'FAILED');

create table if not exists key_requests (
  id               bigserial primary key,
  tg_id            bigint not null references users(tg_id) on delete cascade,         -- кому ключ
  requested_by_tg_id bigint not null references users(tg_id) on delete cascade,       -- кто запросил
  status           key_request_status not null default 'PENDING',
  server_id        bigint,           -- выбранный сервер в панели (если нужно)
  client_id        bigint,           -- выданный/существующий client_id
  error_message    text,
  decided_by_tg_id  bigint references users(tg_id) on delete set null,
  decided_at       timestamptz,
  created_at       timestamptz not null default now()
);

create index if not exists idx_key_requests_status on key_requests(status);

-- (Hook for FR-07) PAYMENTS: минимально для "Оплатил" + подтверждение админом (позже)
create type payment_status as enum ('OPEN', 'PAYMENT_PENDING', 'PAID', 'CANCELLED');

create table if not exists payments (
  id               bigserial primary key,
  owner_tg_id      bigint not null references users(tg_id) on delete cascade,
  period_ym        text not null,  -- например "2026-02"
  amount_rub       integer not null,
  status           payment_status not null default 'OPEN',
  marked_by_tg_id  bigint references users(tg_id) on delete set null,
  confirmed_by_tg_id bigint references users(tg_id) on delete set null,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  unique(owner_tg_id, period_ym)
);
