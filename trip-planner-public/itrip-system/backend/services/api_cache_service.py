# backend/services/api_cache_service.py

import json
import hashlib
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime, timedelta
from core.config import settings


def get_connection():
    return psycopg2.connect(**settings.postgres_kwargs())


def make_cache_key(cache_type: str, params: dict):
    raw = json.dumps(
        {
            "cache_type": cache_type,
            "params": params
        },
        sort_keys=True
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_valid_cache(cache_type: str, params: dict):
    cache_key = make_cache_key(cache_type, params)

    try:
        conn = get_connection()
    except psycopg2.Error:
        return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT response_data
                FROM api_cache
                WHERE cache_key = %s
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                (cache_key,)
            )
            row = cur.fetchone()

            if row:
                return row["response_data"]

            return None
    except psycopg2.Error:
        return None
    finally:
        conn.close()


def save_cache(cache_type: str, params: dict, response_data, ttl_minutes: int):
    cache_key = make_cache_key(cache_type, params)
    expires_at = datetime.now() + timedelta(minutes=ttl_minutes)

    try:
        conn = get_connection()
    except psycopg2.Error:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_cache (
                    cache_key,
                    cache_type,
                    request_params,
                    response_data,
                    expires_at
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (cache_key)
                DO UPDATE SET
                    response_data = EXCLUDED.response_data,
                    created_at = CURRENT_TIMESTAMP,
                    expires_at = EXCLUDED.expires_at
                """,
                (
                    cache_key,
                    cache_type,
                    Json(params),
                    Json(response_data),
                    expires_at
                )
            )

        conn.commit()
    except psycopg2.Error:
        conn.rollback()
        return False
    finally:
        conn.close()

    return True
