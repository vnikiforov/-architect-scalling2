#!/bin/bash

###
# Инициализируем бд
###

echo "=== Checking cluster status ==="

# Создаем временный файл для проверки статуса кластера
cat > /tmp/check_cluster_status.js << 'EOF'
print('=== Cluster Status ===');
print('Shards:');
db.adminCommand({ listShards: 1 });
print('Databases:');
db.adminCommand({ listDatabases: 1 });
print('Sharding enabled for somedb:');
sh.status().databases.forEach(function(db) {
  if (db.name === 'somedb') {
    printjson(db);
  }
});
EOF

docker compose exec -T mongos mongo < /tmp/check_cluster_status.js

echo "=== Inserting test data ==="

# Создаем временный файл для вставки данных
cat > /tmp/insert_test_data.js << 'EOF'
use somedb
print('Starting data insertion...');
var startTime = new Date();

try {
    for(var i = 0; i < 1000; i++) {
        var isSale = i % 10 === 0;
        db.helloDoc.insertOne({
            age: i, 
            name: 'ly' + i, 
            sale: isSale
        });
        if (i % 100 === 0) {
            print('Inserted ' + i + ' documents');
        }
    }
    var endTime = new Date();
    print('Successfully inserted ' + db.helloDoc.countDocuments({}) + ' documents');
    print('Time taken: ' + (endTime - startTime) + ' ms');
} catch (e) {
    print('Error during insertion: ' + e);
    print('Documents inserted so far: ' + db.helloDoc.countDocuments({}));
}
EOF

docker compose exec -T mongos mongo < /tmp/insert_test_data.js

# Удаляем временные файлы
rm /tmp/check_cluster_status.js /tmp/insert_test_data.js