#!/bin/sh

CONTAINER_NAME="timeplayedme-postgres-1"

make_backup() {
    FILENAME="$1_$(date +"%Y-%m-%d_%H-%M-%S").sql" 
    docker exec "$CONTAINER_NAME" pg_dump -U oblivion -d "$1" > "$FILENAME" || rm "$FILENAME"
}

make_backup "oblivionis"
make_backup "storage_v2"
