// Настройка шардинга
print("=== Configuring Sharding (SLOW MACHINE MODE) ===");

try {
    // Проверяем доступность mongos
    print("1. Testing mongos connection...");
    db.adminCommand({ping: 1});
    print("✓ Connected to mongos");
    
    // ОЧЕНЬ ДЛИТЕЛЬНОЕ ожидание пока шарды будут готовы
    print("2. Extended waiting for shards to be ready (slow machine)...");
    var maxAttempts = 60; // Увеличиваем для медленной машины
    var shard1Ready = false;
    var shard2Ready = false;
    
    for (var i = 0; i < maxAttempts; i++) {
        try {
            if (!shard1Ready) {
                var shard1Conn = new Mongo("shard1:27017");
                shard1Conn.getDB("admin").runCommand({ping: 1});
                shard1Ready = true;
                print("✓ Shard1 is ready after " + (i + 1) + " attempts");
            }
        } catch (e) {
            // Shard1 not ready yet
        }
        
        try {
            if (!shard2Ready) {
                var shard2Conn = new Mongo("shard2:27017");
                shard2Conn.getDB("admin").runCommand({ping: 1});
                shard2Ready = true;
                print("✓ Shard2 is ready after " + (i + 1) + " attempts");
            }
        } catch (e) {
            // Shard2 not ready yet
        }
        
        if (shard1Ready && shard2Ready) {
            break;
        }
        
        if (i < maxAttempts - 1) {
            print("⏳ Waiting for shards... attempt " + (i + 1) + "/" + maxAttempts);
            sleep(5000); // Увеличиваем до 5 секунд
        }
    }
    
    if (!shard1Ready || !shard2Ready) {
        print("⚠️ WARNING: Some shards not ready after " + maxAttempts + " attempts");
        print("Shard1 ready: " + shard1Ready + ", Shard2 ready: " + shard2Ready);
        print("Trying to continue anyway...");
    }
    
    // Добавляем шарды в кластер
    print("3. Adding shards to cluster...");
    
    var result1 = sh.addShard("shard1rs/shard1:27017");
    print("✓ Shard1 added: " + JSON.stringify(result1));
    
    // Даем время между операциями
    sleep(5000);
    
    var result2 = sh.addShard("shard2rs/shard2:27017");
    print("✓ Shard2 added: " + JSON.stringify(result2));
    
    // Проверяем что шарды добавлены
    print("4. Verifying shards...");
    var shards = db.adminCommand({listShards: 1});
    print("Current shards: " + JSON.stringify(shards.shards));
    
    // Создаем базу данных
    print("5. Creating database...");
    db = db.getSiblingDB("somedb");
    // Создаем коллекцию для активации базы
    db.createCollection("temp");
    print("✓ Database created");
    
    // Включаем шардирование для базы
    print("6. Enabling sharding for database...");
    sh.enableSharding("somedb");
    print("✓ Sharding enabled for somedb");
    
    // Создаем основную коллекцию
    print("7. Creating helloDoc collection...");
    db.createCollection("helloDoc");
    print("✓ Collection created");
    
    // Шардируем коллекцию по полю sale
    print("8. Sharding collection...");
    sh.shardCollection("somedb.helloDoc", { sale: 1 });
    print("✓ Collection sharded with key {sale: 1}");
    
    // Проверяем статус
    print("9. Final sharding status:");
    sh.status();
    
    print("=== SHARDING CONFIGURATION COMPLETED SUCCESSFULLY ===");
    
} catch (e) {
    print("❌ ERROR during sharding configuration:");
    print("Message: " + e.message);
    if (e.stack) {
        print("Stack: " + e.stack);
    }
    
    // Показываем текущий статус для диагностики
    print("=== CURRENT STATUS FOR DEBUGGING ===");
    try {
        print("Shards: " + JSON.stringify(db.adminCommand({listShards: 1})));
    } catch (e2) {
        print("Cannot list shards: " + e2);
    }
    
    try {
        print("Databases: " + JSON.stringify(db.adminCommand({listDatabases: 1})));
    } catch (e2) {
        print("Cannot list databases: " + e2);
    }
    
    quit(1);
}