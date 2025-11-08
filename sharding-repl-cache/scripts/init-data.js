// Скрипт для вставки тестовых данных
print("=== Starting Data Initialization ===");

try {
    // Переключаемся на базу данных
    db = db.getSiblingDB('somedb');
    print("Using database: " + db.getName());
    
    // Проверяем существование коллекции
    var collections = db.getCollectionNames();
    print("Existing collections: " + JSON.stringify(collections));
    
    // Проверяем что шардинг работает
    print("Checking sharding status...");
    var shards = db.adminCommand({listShards: 1});
    if (shards.shards.length === 0) {
        throw new Error("No shards found! Sharding is not configured properly.");
    }
    print("✓ Shards available: " + shards.shards.length);
    
    // Очищаем коллекцию перед вставкой (если существует)
    if (collections.includes("helloDoc")) {
        print("Clearing existing data...");
        var deleteResult = db.helloDoc.deleteMany({});
        print("Cleared " + deleteResult.deletedCount + " documents");
    } else {
        print("Creating helloDoc collection...");
        db.createCollection("helloDoc");
    }
    
    // Вставляем тестовые данные
    print("Inserting test data...");
    var startTime = new Date();
    var insertedCount = 0;
    
    // Вставляем небольшими батчами
    for (var batch = 0; batch < 40; batch++) {
        for (var i = 1; i <= 25; i++) {
            var docNum = batch * 25 + i;
            var isSale = docNum % 10 === 0;
            
            db.helloDoc.insertOne({
                age: docNum,
                name: 'user_' + docNum,
                sale: isSale,
                price: Math.round(Math.random() * 100 * 100) / 100,
                category: 'category_' + (docNum % 5),
                createdAt: new Date(),
                description: 'Test product ' + docNum + (isSale ? ' (ON SALE!)' : '')
            });
            
            insertedCount++;
        }
        print("Batch " + (batch + 1) + " completed: " + insertedCount + " documents inserted");
    }
    
    var endTime = new Date();
    var duration = endTime - startTime;
    
    print("");
    print("=== INSERTION COMPLETED ===");
    print("✅ Successfully inserted " + insertedCount + " documents");
    print("⏱️  Time taken: " + duration + " ms");
    
    // Статистика
    var totalDocs = db.helloDoc.countDocuments({});
    var saleDocs = db.helloDoc.countDocuments({sale: true});
    var regularDocs = db.helloDoc.countDocuments({sale: false});
    
    print("");
    print("=== COLLECTION STATISTICS ===");
    print("Total documents: " + totalDocs);
    print("Sale items (sale:true): " + saleDocs);
    print("Regular items (sale:false): " + regularDocs);
    
    // Показываем распределение по шардам
    print("");
    print("=== SHARD DISTRIBUTION ===");
    try {
        db.helloDoc.getShardDistribution();
    } catch (e) {
        print("Shard distribution not available: " + e.message);
    }
    
} catch (error) {
    print("");
    print("❌ ERROR during data initialization:");
    print("Message: " + error.message);
    print("Please check if sharding is properly configured.");
    quit(1);
}

print("");
print("=== DATA INITIALIZATION FINISHED ===");