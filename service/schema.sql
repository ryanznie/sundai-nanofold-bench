create table if not exists teams (
    id text primary key,
    name text not null unique,
    created_at text not null default current_timestamp
);

create table if not exists users (
    id text primary key,
    email text not null unique,
    display_name text not null,
    team_id text not null references teams(id),
    created_at text not null default current_timestamp
);

create table if not exists submissions (
    id text primary key,
    team_id text not null references teams(id),
    created_by_user_id text not null references users(id),
    status text not null,
    storage_key text not null,
    runtime_spec text not null,
    original_filename text,
    config_json text,
    description text,
    track text,
    runtime_sec real,
    valid integer,
    invalid_reason text,
    created_at text not null default current_timestamp,
    started_at text,
    completed_at text
);

create table if not exists scores (
    submission_id text primary key references submissions(id),
    track text,
    foldscore_auc_hidden real,
    final_hidden_foldscore real,
    public_val_foldscore real,
    gdt_ha_ca_auc real,
    lddt_atom14_auc real,
    molprobity_clash_atom14_auc real,
    total_runtime_sec real,
    raw_summary_json text
);

create table if not exists submission_targets (
    submission_id text not null references submissions(id),
    target_id text not null,
    primary key (submission_id, target_id)
);

create index if not exists idx_submissions_team_created_at on submissions(team_id, created_at desc);
