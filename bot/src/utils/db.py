import os
from typing import List, Any

import motor.motor_asyncio
from pydantic import BaseModel

from src.models.adv import Adv
from src.models.channels import Channels
from src.models.referrals import Referrals
from src.models.user import User

# Используем MONGO_URI если она задана, иначе старую систему
MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
elif all([os.getenv("MONGO_HOST"), os.getenv("MONGO_PORT"), os.getenv("MONGO_USERNAME"), os.getenv("MONGO_PASSWORD")]):
    client = motor.motor_asyncio.AsyncIOMotorClient(
        f'mongodb://{os.getenv("MONGO_USERNAME")}:{os.getenv("MONGO_PASSWORD")}@{os.getenv("MONGO_HOST")}:{os.getenv("MONGO_PORT")}')
else:
    # Если переменные не заданы, используем переменные от Railway
    MONGOHOST = os.getenv("MONGOHOST", "localhost")
    MONGOPORT = os.getenv("MONGOPORT", "27017")
    MONGOUSER = os.getenv("MONGOUSER")
    MONGOPASSWORD = os.getenv("MONGOPASSWORD")
    
    if all([MONGOHOST, MONGOPORT, MONGOUSER, MONGOPASSWORD]):
        client = motor.motor_asyncio.AsyncIOMotorClient(
            f'mongodb://{MONGOUSER}:{MONGOPASSWORD}@{MONGOHOST}:{MONGOPORT}')
    else:
        # Если и переменные от Railway не заданы, используем локальное подключение
        client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")

raw_db = client[os.getenv("MONGO_DB_NAME", "default_db")]

external_MONGO_URI = os.getenv("EXTERNAL_MONGO_URI")
if external_MONGO_URI:
    external_client = motor.motor_asyncio.AsyncIOMotorClient(external_MONGO_URI)
elif all([os.getenv("MONGO_HOST_EXTERNAL"), os.getenv("MONGO_PORT_EXTERNAL"), os.getenv("MONGO_USERNAME"), os.getenv("MONGO_PASSWORD")]):
    external_client = motor.motor_asyncio.AsyncIOMotorClient(
        f'mongodb://{os.getenv("MONGO_USERNAME")}:{os.getenv("MONGO_PASSWORD")}@{os.getenv("MONGO_HOST_EXTERNAL")}:{os.getenv("MONGO_PORT_EXTERNAL")}')
else:
    # Если переменные не заданы, используем переменные от Railway для внешнего подключения
    MONGOHOST = os.getenv("MONGOHOST", "localhost")
    MONGOPORT = os.getenv("MONGOPORT", "27017")
    MONGOUSER = os.getenv("MONGOUSER")
    MONGOPASSWORD = os.getenv("MONGOPASSWORD")
    
    if all([MONGOHOST, MONGOPORT, MONGOUSER, MONGOPASSWORD]):
        external_client = motor.motor_asyncio.AsyncIOMotorClient(
            f'mongodb://{MONGOUSER}:{MONGOPASSWORD}@{MONGOHOST}:{MONGOPORT}')
    else:
        # Если и переменные от Railway не заданы, используем локальное подключение
        external_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")

external_db = external_client[os.getenv("MONGO_DB_NAME", "default_db")]


class Collection:

    def __init__(self, model, collection_name: str):
        db_name = os.getenv("MONGO_DB_NAME", "default_db")
        self.collection = client[db_name][collection_name]
        self.model = model

    async def find_one(self, f: dict):
        data = await self.collection.find_one(f)
        if not data:
            return None
        data['_id'] = str(data['_id'])
        model = self.model(**data)
        return model

    async def find(self, f: dict, count: int = 100) -> List:
        data = self.collection.find(f).to_list(length=count)
        list_models = []
        for item in await data:
            item['_id'] = str(item['_id'])
            list_models.append(self.model(**item))
        return list_models

    async def update_one(self, f: dict, s: dict, upsert: bool = False):
        res = await self.collection.update_one(f, {'$set': s}, upsert=upsert)
        return res

    async def delete_one(self, f: dict, ):
        res = await self.collection.delete_one(f)
        return res

    async def delete_many(self, f: dict, ):
        res = await self.collection.delete_many(f)
        return res

    async def update_many(self, f: dict, s: dict):
        res = await self.collection.update_many(f, s)
        return res

    async def count(self, f: dict):
        res = await self.collection.count_documents(f)
        return res

    async def insert_one(self, i: dict):
        res = await self.collection.insert_one(i)
        return res

    async def find_one_with_min_adv_id(self):
        data = await self.collection.find().sort('adv_id', 1).limit(1).to_list(length=1)
        if not data:
            return None
        data[0]['_id'] = str(data[0]['_id'])
        model = self.model(**data[0])
        return model

    async def find_one_with_next_adv_id(self, current_adv_id: int):
        data = await self.collection.find({'adv_id': {'$gt': current_adv_id}}).sort('adv_id', 1).limit(1).to_list(length=1)
        if not data:
            return None
        data[0]['_id'] = str(data[0]['_id'])
        model = self.model(**data[0])
        return model

    async def find_one_with_prev_adv_id(self, current_adv_id: int):
        data = await self.collection.find({'adv_id': {'$lt': current_adv_id}}).sort('adv_id', -1).limit(1).to_list(length=1)
        if not data:
            return None
        data[0]['_id'] = str(data[0]['_id'])
        model = self.model(**data[0])
        return model

    async def find_one_with_max_adv_id(self):
        data = await self.collection.find().sort('adv_id', -1).limit(1).to_list(length=1)
        if not data:
            return None
        data[0]['_id'] = str(data[0]['_id'])
        model = self.model(**data[0])
        return model


class MongoDbClient(BaseModel):
    users: Any
    channels: Any
    referrals: Any
    adv: Any



class MongoDbClient(BaseModel):
    users: Any
    channels: Any
    referrals: Any
    adv: Any


db = MongoDbClient(
    users=Collection(collection_name='users', model=User),
    channels=Collection(collection_name='channels', model=Channels),
    referrals = Collection(collection_name='referrals', model=Referrals),
    adv=Collection(collection_name='adv', model=Adv)
)
