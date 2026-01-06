-- backend/database/init_postgres.sql
-- PostgreSQL schema for Supabase

create extension if not exists pgcrypto;

-- update timestamp trigger function
create or replace function trigger_set_timestamp()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create table if not exists professional_data (
    id uuid primary key default gen_random_uuid(),
    project_id text not null,
    node_id text not null,
    run_id uuid,
    test_item text not null,
    test_result numeric, -- nullable
    test_unit text, -- nullable
    record_code text,
    test_location_text text,
    design_strength_grade text,
    strength_estimated_mpa numeric,
    carbonation_depth_avg_mm numeric,
    test_date date,
    casting_date date,
    test_value_json jsonb,
    component_type text,
    location jsonb,
    evidence_refs jsonb not null default '[]'::jsonb,
    raw_result jsonb not null,
    confirmed_result jsonb,
    result_version int not null default 1,
    source_prompt_version text not null,
    schema_version text not null,
    raw_hash text,
    input_fingerprint text,
    confirmed_by text,
    confirmed_at timestamptz,
    source_hash text,
    confidence numeric check (confidence >= 0 and confidence <= 1),
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index if not exists idx_professional_data_project_id on professional_data(project_id);
create index if not exists idx_professional_data_project_node_time on professional_data(project_id, node_id, created_at desc);
create index if not exists idx_professional_data_project_time on professional_data(project_id, created_at desc);
create index if not exists idx_professional_data_run_id on professional_data(run_id);
drop index if exists idx_professional_data_dedup;
drop index if exists ux_professional_data_dedup;
create unique index if not exists ux_professional_data_dedup
on professional_data(input_fingerprint)
where input_fingerprint is not null;

drop trigger if exists set_timestamp on professional_data;
create trigger set_timestamp
before update on professional_data
for each row
execute function trigger_set_timestamp();

create table if not exists run_log (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null,
    project_id text not null,
    node_id text,
    record_id uuid,
    status text not null,
    stage text not null,
    prompt_version text,
    schema_version text,
    input_file_hashes jsonb,
    skill_steps jsonb,
    llm_usage jsonb,
    total_cost numeric default 0,
    created_at timestamptz default now(),
    error_message text
);

create index if not exists idx_run_log_project_id on run_log(project_id);
create index if not exists idx_run_log_project_node_time on run_log(project_id, node_id, created_at desc);
create index if not exists idx_run_log_status on run_log(status);
create index if not exists idx_run_log_run_id_time on run_log(run_id, created_at desc);
create unique index if not exists ux_run_log_run_stage on run_log(run_id, stage);

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'fk_run_log_record'
  ) then
    alter table run_log
      add constraint fk_run_log_record
      foreign key (record_id) references professional_data(id) on delete set null;
  end if;
end $$;
