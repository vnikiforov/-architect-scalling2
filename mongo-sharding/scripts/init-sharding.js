// Добавляем шарды в кластер
sh.addShard("shard1rs/shard1:27017");
sh.addShard("shard2rs/shard2:27017");

// Включаем шардинг для базы данных
sh.enableSharding("somedb");

// Шардируем коллекцию по полю sale
sh.shardCollection("somedb.helloDoc", { sale: 1 });

print("Sharding configuration completed!");