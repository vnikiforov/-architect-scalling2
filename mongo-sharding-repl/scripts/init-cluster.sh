#!/bin/bash

echo "=== Starting Cluster Initialization ==="

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Функция для выполнения команды с повторными попытками
execute_with_retry() {
    local command="$1"
    local description="$2"
    local max_attempts=30
    local attempt=1
    
    log "Starting: $description"
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$command"; then
            log "✅ Success: $description"
            return 0
        fi
        
        log "⚠️ Attempt $attempt/$max_attempts failed for: $description"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log "❌ FAILED: $description after $max_attempts attempts"
    return 1
}

# Config server уже инициализирован сервисом init-config
log "Config server already initialized"

log "Waiting for all services to be ready..."
sleep 30

# Шаг 1: Инициализация shard1
execute_with_retry \
    "mongo --host shard1:27017 /scripts/init-shard1.js" \
    "Initialize shard1 replica set"

log "Waiting for shard1 replication to stabilize..."
sleep 30

# Шаг 2: Инициализация shard2
execute_with_retry \
    "mongo --host shard2:27017 /scripts/init-shard2.js" \
    "Initialize shard2 replica set"

log "Waiting for shard2 replication to stabilize..."
sleep 30

# Шаг 3: Настройка шардинга
execute_with_retry \
    "mongo --host mongos:27017 /scripts/init-sharding.js" \
    "Configure sharding"

log "Waiting for sharding configuration to apply..."
sleep 20

# Шаг 4: Вставка тестовых данных
execute_with_retry \
    "mongo --host mongos:27017 /scripts/init-data.js" \
    "Insert test data (1000 documents)"

# Финальная проверка
log "Performing final cluster check..."
mongo --host mongos:27017 --eval "
print('=== FINAL CLUSTER STATUS ===');
print('Shards:');
shards = db.adminCommand({listShards: 1});
printjson(shards.shards);
print('Databases:');
dbs = db.adminCommand({listDatabases: 1});
print('Document count: ' + db.getSiblingDB('somedb').helloDoc.countDocuments({}));
print('=== CLUSTER READY ===');
"

log "=== CLUSTER INITIALIZATION COMPLETED SUCCESSFULLY ==="