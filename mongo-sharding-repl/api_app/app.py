from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import motor.motor_asyncio
from bson import ObjectId

app = FastAPI()

# Подключение к MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongos:27017")
db = client.somedb

class UserModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    age: int = Field(...)
    name: str = Field(...)
    sale: bool = Field(default=False)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}

@app.get("/")
async def root():
    return {"message": "MongoDB Sharded Cluster API"}

@app.get("/health")
async def health_check():
    try:
        # Проверяем подключение к MongoDB
        await db.command("ping")
        return {"status": "healthy", "mongodb": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MongoDB connection failed: {str(e)}")

@app.get("/users/count")
async def count_users():
    try:
        count = await db.helloDoc.count_documents({})
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting users: {str(e)}")

@app.post("/users/")
async def create_user(user: UserModel):
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
    try:
        # Получаем информацию о шардах
        shards = await db.admin.command("listShards")
        
        # Получаем статистику базы данных
        db_stats = await db.command("dbStats")
        
        # Получаем информацию о распределении данных
        shard_distribution = await db.command("shardCollectionStats", "somedb.helloDoc")
        
        return {
            "shards": shards,
            "database_stats": {
                "db": db_stats["db"],
                "collections": db_stats["collections"],
                "objects": db_stats["objects"],
                "dataSize": db_stats["dataSize"]
            },
            "sharding_status": f"Collection sharded: {shard_distribution.get('sharded', False)}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cluster status: {str(e)}")