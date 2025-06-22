#!/bin/sh
set -e

# $1 = file
# $2 = target db

if [ -z "$2" ]; then
    echo "Usage: $0 <backup_file.sql> <target_db>"
    exit 1
fi


VOLUME="oblivionis-postgres"
USER="oblivion"
PASS="oblivion"
DB="$2"

# delete existing volume
docker volume rm "$VOLUME" ||true
docker volume create "$VOLUME" ||true


# start psql container
docker run --name psql -d -v "$VOLUME:/var/lib/postgresql/data" -e POSTGRES_USER="$USER" -e POSTGRES_PASSWORD="$PASS" postgres:17.2

until docker exec psql pg_isready -U "$USER"; do
  sleep 1
done

# (re)create db
docker exec -i psql psql -U "$USER" -d postgres -c "DROP DATABASE IF EXISTS $DB;"
docker exec -i psql psql -U "$USER" -d postgres -c "CREATE DATABASE $DB;"

# restore (mount the SQL file into the container and restore from there)
docker cp "$1" psql:/tmp/restore.sql
docker exec -i psql psql -U "$USER" -d "$DB" -f /tmp/restore.sql


# stop psql container
docker rm -f psql

echo "DONE!"
