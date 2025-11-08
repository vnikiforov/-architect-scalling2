# app.py
import json
import logging
import os
import time
from typing import List, Optional

import motor.motor_asyncio
from bson import ObjectId
from fastapi import Body, FastAPI, HTTPException, status
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from pymongo import errors
from redis import asyncio as aioredis
from typing_extensions import Annotated

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Конфигурация
DATABASE_URL = os.getenv("MONGO_URI", "mongodb://mongos:27017")
DATABASE_NAME = "somedb"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Инициализация кэширования
def nocache(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

if REDIS_URL:
    cache = cache
else:
    cache = nocache

# Подключение к MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
db = client[DATABASE_NAME]

# Represents an ObjectId field in the database.
PyObjectId = Annotated[str, BeforeValidator(str)]

class UserModel(BaseModel):
    """
    Container for a single user record.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    age: int = Field(...)
    name: str = Field(...)
    sale: bool = Field(default=False)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}

class UserCollection(BaseModel):
    """
    A container holding a list of `UserModel` instances.
    """
    users: List[UserModel]

@app.on_event("startup")
async def startup():
    """Инициализация Redis кэша при запуске"""
    try:
        redis = aioredis.from_url(REDIS_URL, encoding="utf8", decode_responses=True)
        FastAPICache.init(RedisBackend(redis), prefix="api:cache")
        logger.info("✅ Redis cache initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Redis cache initialization failed: {e}")

@app.get("/")
async def root():
    """Корневой endpoint с полной информацией о кластере"""
    try:
        collection_names = await db.list_collection_names()
        collections = {}
        for collection_name in collection_names:
            collection = db.get_collection(collection_name)
            collections[collection_name] = {
                "documents_count": await collection.count_documents({})
            }
        
        # Информация о репликации
        try:
            replica_status = await client.admin.command("replSetGetStatus")
            replica_status = json.dumps(replica_status, indent=2, default=str)
        except errors.OperationFailure:
            replica_status = "No Replicas"

        # Информация о топологии
        topology_description = client.topology_description
        read_preference = client.client_options.read_preference
        topology_type = topology_description.topology_type_name
        replicaset_name = topology_description.replica_set_name

        # Информация о шардах
        shards = None
        if topology_type == "Sharded":
            shards_list = await client.admin.command("listShards")
            shards = {}
            for shard in shards_list.get("shards", []):
                shards[shard["_id"]] = shard["host"]

        cache_enabled = REDIS_URL and FastAPICache.get_enable()

        return {
            "message": "MongoDB Sharded Cluster API",
            "mongo_topology_type": topology_type,
            "mongo_replicaset_name": replicaset_name,
            "mongo_db": DATABASE_NAME,
            "read_preference": str(read_preference),
            "mongo_nodes": [str(node) for node in client.nodes] if client.nodes else [],
            "mongo_primary_host": str(client.primary) if client.primary else None,
            "mongo_secondary_hosts": [str(secondary) for secondary in client.secondaries],
            "mongo_is_primary": client.is_primary,
            "mongo_is_mongos": client.is_mongos,
            "collections": collections,
            "shards": shards,
            "cache_enabled": cache_enabled,
            "status": "OK",
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса и подключений"""
    try:
        # Проверяем подключение к MongoDB
        await db.command("ping")
        mongo_status = "connected"
    except Exception as e:
        mongo_status = f"failed: {str(e)}"

    try:
        # Проверяем подключение к Redis
        if REDIS_URL:
            redis = aioredis.from_url(REDIS_URL)
            await redis.ping()
            redis_status = "connected"
        else:
            redis_status = "not configured"
    except Exception as e:
        redis_status = f"failed: {str(e)}"

    return {
        "status": "healthy" if mongo_status == "connected" else "degraded",
        "mongodb": mongo_status,
        "redis": redis_status
    }

@app.get("/users/count")
async def count_users():
    """Количество пользователей в коллекции"""
    try:
        count = await db.helloDoc.count_documents({})
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting users: {str(e)}")

@app.post("/users/")
async def create_user(user: UserModel):
    """Создание нового пользователя"""
    try:
        user_dict = user.dict(by_alias=True)
        if user_dict.get('_id') is None:
            user_dict.pop('_id', None)
        
        result = await db.helloDoc.insert_one(user_dict)
        return {"id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.get("/users/")
async def list_users(limit: int = 10, skip: int = 0):
    """Список пользователей с пагинацией"""
    try:
        users = []
        cursor = db.helloDoc.find().skip(skip).limit(limit)
        async for document in cursor:
            document['_id'] = str(document['_id'])
            users.append(document)
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Получение пользователя по ID"""
    try:
        document = await db.helloDoc.find_one({"_id": ObjectId(user_id)})
        if document:
            document['_id'] = str(document['_id'])
            return document
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

@app.get("/cluster/status")
async def cluster_status():
    """Статус кластера шардинга"""
    try:
        # Получаем информацию о шардах
        shards = await db.admin.command("listShards")
        
        # Получаем статистику базы данных
        db_stats = await db.command("dbStats")
        
        # Получаем информацию о распределении данных
        try:
            shard_distribution = await db.command("shardCollectionStats", "somedb.helloDoc")
            sharding_status = f"Collection sharded: {shard_distribution.get('sharded', False)}"
        except Exception:
            sharding_status = "Shard collection stats not available"
        
        return {
            "shards": shards,
            "database_stats": {
                "db": db_stats["db"],
                "collections": db_stats["collections"],
                "objects": db_stats["objects"],
                "dataSize": db_stats["dataSize"]
            },
            "sharding_status": sharding_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cluster status: {str(e)}")

# Восстановленные endpoints из оригинальной версии

@app.get(
    "/{collection_name}/users",
    response_description="List all users",
    response_model=UserCollection,
    response_model_by_alias=False,
)
@cache(expire=60 * 1)
async def list_all_users(collection_name: str):
    """
    List all of the user data in the database.
    The response is unpaginated and limited to 1000 results.
    """
    time.sleep(1)  # Имитация долгой операции для демонстрации кэширования
    try:
        collection = db.get_collection(collection_name)
        users = await collection.find().to_list(1000)
        return UserCollection(users=users)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing all users: {str(e)}")

@app.get(
    "/{collection_name}/users/{name}",
    response_description="Get a single user",
    response_model=UserModel,
    response_model_by_alias=False,
)
async def show_user_by_name(collection_name: str, name: str):
    """
    Get the record for a specific user, looked up by `name`.
    """
    try:
        collection = db.get_collection(collection_name)
        if (user := await collection.find_one({"name": name})) is not None:
            return user
        raise HTTPException(status_code=404, detail=f"User {name} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user by name: {str(e)}")

@app.post(
    "/{collection_name}/users",
    response_description="Add new user",
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_user_in_collection(collection_name: str, user: UserModel = Body(...)):
    """
    Insert a new user record.

    A unique `id` will be created and provided in the response.
    """
    try:
        collection = db.get_collection(collection_name)
        new_user = await collection.insert_one(
            user.dict(by_alias=True, exclude=["id"])
        )
        created_user = await collection.find_one({"_id": new_user.inserted_id})
        return created_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user in collection: {str(e)}")

@app.get("/{collection_name}/count")
async def collection_count(collection_name: str):
    """Количество документов в коллекции"""
    try:
        collection = db.get_collection(collection_name)
        items_count = await collection.count_documents({})
        return {
            "status": "OK", 
            "mongo_db": DATABASE_NAME, 
            "collection": collection_name,
            "items_count": items_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting collection items: {str(e)}")