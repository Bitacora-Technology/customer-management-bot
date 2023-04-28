import motor.motor_asyncio as motor
from typing import Optional

client = motor.AsyncIOMotorClient('mongodb://localhost:27017')
db = client['requests-manager']


class Customer:
    def __init__(self, channel: int = None) -> None:
        self.customers = db['customers']
        self.query = {'_id': channel}

    async def create(self, query: dict) -> None:
        await self.customers.insert_one(query)

    async def check(self) -> Optional[dict]:
        return await self.customers.find_one(self.query)

    async def update(self, query: dict) -> None:
        set_query = {'$set': query}
        await self.customers.update_one(self.query, set_query, upsert=True)

    async def delete(self) -> None:
        await self.customers.delete_one(self.query)

    def cursor(self) -> motor.AsyncIOMotorCursor:
        return self.customers.find()
