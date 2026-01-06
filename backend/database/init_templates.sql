-- Ensure pgcrypto exists for gen_random_uuid()
create extension if not exists pgcrypto;

create table if not exists template_registry (
    template_id text primary key,
    dataset_key text not null,
    fingerprint text not null unique,
    schema_version text not null,
    prompt_version text not null,
    prompt text not null,
    prompt_hash text,
    mapping_rules jsonb not null default '{}'::jsonb,
    validation_rules jsonb not null default '{}'::jsonb,
    status text not null default 'active',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_template_registry_status check (status in ('active','draft','deprecated'))
);

create table if not exists template_samples (
    id uuid primary key default gen_random_uuid(),
    template_id text not null,
    sample_name text,
    sample_uri text,
    created_at timestamptz not null default now()
);

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'fk_template_samples_template'
  ) then
    alter table template_samples
      add constraint fk_template_samples_template
      foreign key (template_id) references template_registry(template_id) on delete cascade;
  end if;
end $$;

create index if not exists idx_template_samples_template_id
on template_samples(template_id);

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_template_registry_updated_at on template_registry;
create trigger trg_template_registry_updated_at
before update on template_registry
for each row execute function set_updated_at();
