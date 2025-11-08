#!/bin/bash

host="$1"
port="${2:-27017}"
shift 2
cmd="$@"

echo "Waiting for MongoDB at $host:$port to become available..."

# Ждем пока MongoDB не станет доступна (используем mongo, а не mongosh)
until mongo --host $host --port $port --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
  echo "MongoDB at $host:$port is unavailable - sleeping"
  sleep 5
done

echo "MongoDB at $host:$port is up - executing command: $cmd"
exec $cmd