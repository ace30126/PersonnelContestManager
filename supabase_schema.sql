-- ============================================================
-- 공모전 매니저 — Supabase 스키마
-- Supabase 대시보드 > SQL Editor 에 붙여넣고 실행하세요.
-- ============================================================

-- 프로필 (단일 행, id=1)
create table if not exists profile (
    id   int primary key,
    data jsonb not null default '{}'::jsonb
);

-- 프로젝트
create table if not exists projects (
    id            uuid primary key default gen_random_uuid(),
    meta          jsonb not null default '{}'::jsonb,
    status        text  default '준비중',
    submit_date   text  default '',
    announce_date text  default '',
    memo          text  default '',
    prize         text  default '',
    draft         text  default '',
    created_at    timestamptz default now()
);

-- 본(검색 제외) 공모전
create table if not exists seen_contests (
    contest_id text primary key
);

-- 숨긴 공모전
create table if not exists hidden_contests (
    contest_id text primary key,
    data       jsonb not null default '{}'::jsonb
);

-- ============================================================
-- 첨부파일용 Storage 버킷 생성
-- (대시보드 > Storage > New bucket 에서 'attachments' 생성해도 됩니다)
-- ============================================================
insert into storage.buckets (id, name, public)
values ('attachments', 'attachments', false)
on conflict (id) do nothing;

-- 참고: 혼자 쓰는 서비스라 service_role key를 secrets에 넣으면
--       RLS 없이 모든 테이블/스토리지에 접근됩니다(가장 간단).
--       anon key를 쓰려면 각 테이블에 RLS 정책을 별도로 추가해야 합니다.
