import motor.motor_asyncio as motor
from typing import Optional

client = motor.AsyncIOMotorClient('mongodb://localhost:27017')
db = client['requests-manager']


class Customer:
    def __init__(self, channel: int = None) -> None:
        self.customer = db['customer']
        self.query = {'_id': channel}

    async def create(self, query: dict) -> None:
        await self.customer.insert_one(query)

    async def check(self) -> Optional[dict]:
        return await self.customer.find_one(self.query)

    async def update(self, query: dict) -> None:
        set_query = {'$set': query}
        await self.customer.update_one(self.query, set_query, upsert=True)
