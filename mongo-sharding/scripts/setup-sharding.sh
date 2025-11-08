#!/bin/bash

echo "=== Setting up MongoDB Sharding ==="

# Проверяем статус шардов
echo "1. Checking shard status..."
docker compose exec -T shard1 mongo --eval "rs.status().ok" | grep -q 1 && echo "Shard1: OK" || echo "Shard1: Not ready"
docker compose exec -T shard2 mongo --eval "rs.status().ok" | grep -q 1 && echo "Shard2: OK" || echo "Shard2: Not ready"

# Добавляем шарды в кластер
echo "2. Adding shards to cluster..."
docker compose exec -T mongos mongo --eval "sh.addShard('shard1rs/shard1:27017')"
docker compose exec -T mongos mongo --eval "sh.addShard('shard2rs/shard2:27017')"

# Включаем шардинг
echo "3. Enabling sharding..."
docker compose exec -T mongos mongo --eval "sh.enableSharding('somedb')"
docker compose exec -T mongos mongo --eval "sh.shardCollection('somedb.helloDoc', { sale: 1 })"

# Проверяем результат
echo "4. Verifying setup..."
docker compose exec -T mongos mongo --eval "
print('Shards:');
db.adminCommand({ listShards: 1 });
print('Sharding status:');
sh.status();
"

echo "=== Sharding setup completed ==="