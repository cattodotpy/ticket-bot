# import aiomongo
import json
import aiofiles
from dataclasses import dataclass
from abc import ABC


class Database(ABC):
    def __init__(self):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def get(self, key: str):
        pass

    async def set(self, key: str, value: str):
        pass

    async def delete(self, key: str):
        pass


# @dataclass(frozen=True)
# class MongoDatabase(Database):
#     uri: str
#     db_name: str
#     collection: str

#     async def connect(self):
#         self.client = await aiomongo.create_client(self.uri)

#         await self.client.connect()
#         self.db = self.client[self.db_name]

#     async def disconnect(self):
#         self.client.close()

#     async def get(self, key: str):
#         document = await self.client[self.collection].find_one({"key": key})
#         if document is None:
#             return None
#         return document.get("value")

#     async def set(self, key: str, value: str):
#         await self.client[self.collection].update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

#     async def delete(self, key: str):
#         await self.client[self.collection].delete_one({"key": key})

#     async def __aenter__(self):
#         await self.connect()
#         return self

#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         await self.disconnect()


@dataclass
class JsonDatabase(Database):
    file_name: str

    def __post_init__(self):
        if not self.file_name.endswith(".json"):
            raise ValueError("File name must end with .json")
        self.cache = {}

    async def connect(self):
        self.file = await aiofiles.open(self.file_name, mode="r")
        self.data = json.loads(await self.file.read())

    async def disconnect(self):
        wfile = await aiofiles.open(self.file_name, mode="w")
        await wfile.seek(0)
        await wfile.write(json.dumps(self.data))
        await wfile.truncate()
        await wfile.close()

    async def save(self):
        wfile = await aiofiles.open(self.file_name, mode="w")
        self.cache = self.data
        await wfile.seek(0)
        await wfile.write(json.dumps(self.data))
        await wfile.truncate()

    async def get(self, key: str):
        if not hasattr(self, "data"):
            raise RuntimeError(
                "Database not initialized. Did you not use `async with`?")
        return self.data.get(key)

    async def set(self, key: str, value: str):
        if not hasattr(self, "data"):
            raise RuntimeError(
                "Database not initialized. Did you not use `async with`?")
        self.data[key] = value
        await self.save()

    async def delete(self, key: str):
        if not hasattr(self, "data"):
            raise RuntimeError(
                "Database not initialized. Did you not use `async with`?")
        del self.data[key]
        await self.save()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...
