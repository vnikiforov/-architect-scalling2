from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional
import motor.motor_asyncio

app = FastAPI()

# Подключение к MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongos:27017")
db = client.somedb

class UserModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    age: int = Field(...)
    name: str = Field(...)
    sale: bool = Field(default=False)

@app.get("/")
async def root():
    return {"message": "MongoDB Sharded Cluster API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mongodb": "connected"}

@app.get("/users/count")
async def count_users():
    count = await db.helloDoc.count_documents({})
    return {"count": count}

@app.post("/users/")
async def create_user(user: UserModel):
    result = await db.helloDoc.insert_one(user.dict(by_alias=True))
    return {"id": str(result.inserted_id)}