create table if not exists users (
  tg_id bigint primary key,
  username text,
  role text not null,              -- ADMIN|MODERATOR|BILLING_MEMBER|INVITED
  status text not null,            -- ACTIVE|PENDING_APPROVAL|BLOCKED
  inviter_tg_id bigint,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists invites (
  code text primary key,
  created_by bigint not null,
  status text not null,            -- ACTIVE|USED|EXPIRED|REVOKED
  expires_at timestamptz not null,
  used_by bigint,
  created_at timestamptz not null default now()
);
