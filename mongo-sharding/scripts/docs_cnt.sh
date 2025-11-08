#!/bin/bash

docker compose exec -T mongos mongo --port 27017 --quiet <<'EOF'
use somedb
db.helloDoc.countDocuments({})
'EOF'  

