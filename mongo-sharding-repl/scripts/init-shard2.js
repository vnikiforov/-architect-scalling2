// Инициализация shard2
try {
    print("Initializing shard2 replica set...");
    rs.initiate({
        _id: "shard2rs",
        members: [
            { _id: 0, host: "shard2:27017" }
        ]
    });
    print("Shard2 replica set initiated successfully");
} catch (e) {
    print("Error initiating shard2 replica set: " + e);
}