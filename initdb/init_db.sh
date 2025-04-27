#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE airflow;
    CREATE DATABASE ticker;
    
    \c airflow
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    
    \c ticker
    $(cat /docker-entrypoint-initdb.d/ticker-schema.sql)
EOSQL