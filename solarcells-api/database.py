from motor.motor_asyncio import AsyncIOMotorClient
from config.config import MONGO_DB, MONGO_URL


class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[MONGO_DB]

    async def close(self):
        if self.client:
            self.client.close()

    async def get_collection(self, collection: str):
        if self.db is None:
            await self.connect()
        return self.db[collection]


mongodb = MongoDB()


async def get_logs_collection():
    return await mongodb.get_collection("test-collection")


async def get_panels_collection():
    return await mongodb.get_collection("panels")


async def connect_to_db():
    await mongodb.connect()


async def close_db_connection():
    await mongodb.close()
