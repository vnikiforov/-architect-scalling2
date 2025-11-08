// Скрипт для ожидания готовности config server
print("=== Waiting for Config Server to be ready ===");

var maxAttempts = 120;
var configReady = false;

for (var i = 0; i < maxAttempts; i++) {
    try {
        var conn = new Mongo("config:27017");
        var admin = conn.getDB("admin");
        var result = admin.runCommand({ping: 1});
        
        // Проверяем статус replica set
        try {
            var status = admin.runCommand({replSetGetStatus: 1});
            if (status.members && status.members.length > 0) {
                var primary = status.members.find(m => m.state === 1);
                if (primary) {
                    print("✅ Config server is PRIMARY and ready");
                    configReady = true;
                    break;
                }
            }
        } catch (rsError) {
            // Replica set еще не инициализирован, но сервер отвечает
            print("Config server responding but replica set not ready: " + rsError);
        }
        
        print("⏳ Config server responding but not primary yet... attempt " + (i + 1) + "/" + maxAttempts);
        
    } catch (e) {
        print("❌ Config server not ready (attempt " + (i + 1) + "): " + e);
    }
    
    if (i < maxAttempts - 1) {
        sleep(5000);
    }
}

if (!configReady) {
    print("❌ Config server failed to become ready after " + maxAttempts + " attempts");
    quit(1);
}

print("=== Config Server is ready for mongos ===");