CREATE SCHEMA IF NOT EXISTS trip_db;


CREATE TABLE IF NOT EXISTS trip_db.trip_history (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
plan_json JSONB NOT NULL
);


CREATE INDEX IF NOT EXISTS idx_trip_history_created_at
  ON trip_db.trip_history (created_at DESC);

-- Shared by existing POI/weather services and the asynchronous replanning matrix.
CREATE TABLE IF NOT EXISTS public.api_cache (
    cache_key TEXT PRIMARY KEY,
    cache_type TEXT NOT NULL,
    request_params JSONB NOT NULL,
    response_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_cache_expires_at
  ON public.api_cache (expires_at);
