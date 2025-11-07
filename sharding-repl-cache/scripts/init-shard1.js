// Инициализация shard1
try {
    print("Initializing shard1 replica set...");
    rs.initiate({
        _id: "shard1rs",
        members: [
            { _id: 0, host: "shard1:27017" }
        ]
    });
    print("Shard1 replica set initiated successfully");
} catch (e) {
    print("Error initiating shard1 replica set: " + e);
}