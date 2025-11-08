// Инициализация config server
print("=== Initializing Config Server ===");

// Ждем полного запуска MongoDB
sleep(15000);

var maxAttempts = 10;
var initialized = false;

// Принудительная инициализация replica set
for (var i = 0; i < maxAttempts; i++) {
    try {
        print("Initialization attempt " + (i + 1) + "...");
        
        var result = rs.initiate({
            _id: "configrs",
            configsvr: true,
            members: [
                { _id: 0, host: "config:27017" }
            ]
        });
        
        print("✅ Replica set initiated successfully");
        initialized = true;
        break;
        
    } catch (initError) {
        // Если replica set уже существует, проверяем статус
        if (initError.codeName === "AlreadyInitialized" || initError.message.includes("already initialized")) {
            print("✅ Replica set already initialized");
            initialized = true;
            break;
        }
        
        print("Init attempt " + (i + 1) + " failed: " + initError);
        
        if (i < maxAttempts - 1) {
            sleep(5000);
        }
    }
}

if (!initialized) {
    print("❌ Failed to initialize replica set after " + maxAttempts + " attempts");
    
    // Показываем диагностическую информацию
    try {
        var admin = db.getSiblingDB("admin");
        var isMaster = admin.runCommand({isMaster: 1});
        print("isMaster result: " + JSON.stringify(isMaster));
    } catch (e) {
        print("Diagnostic failed: " + e);
    }
    
    quit(1);
}

// Даем время для election
print("Waiting for election process...");
sleep(20000);

// Проверяем статус replica set
print("Checking replica set status...");
for (var j = 0; j < 30; j++) {
    try {
        var status = rs.status();
        
        if (status.ok === 1) {
            print("✅ Replica set is healthy");
            print("Set name: " + status.set);
            print("My state: " + status.myState);
            
            if (status.myState === 1) {
                print("✅ Config server is PRIMARY");
                break;
            } else {
                print("Current state: " + status.myState + " (waiting for PRIMARY) - attempt " + (j + 1));
            }
        }
        
    } catch (e) {
        print("Error getting status: " + e);
    }
    
    if (j < 29) {
        sleep(3000);
    }
}

// Финальная проверка
try {
    var finalStatus = rs.status();
    if (finalStatus.myState === 1) {
        print("✅ SUCCESS: Config server is PRIMARY and ready");
    } else {
        print("❌ Config server failed to become PRIMARY. Final state: " + finalStatus.myState);
        quit(1);
    }
} catch (e) {
    print("❌ Final check failed: " + e);
    quit(1);
}

print("=== Config Server Initialization Complete ===");