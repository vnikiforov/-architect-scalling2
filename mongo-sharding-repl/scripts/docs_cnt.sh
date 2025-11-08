#!/bin/bash

docker compose exec -T mongos mongo --host mongos --port 27017 --quiet <<'EOF'
use somedb
db.helloDoc.countDocuments({})
EOF