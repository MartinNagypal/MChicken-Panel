import aiosqlite

class SQLITE:
    def __init__(self):
        self.__connection = None
        
    async def connect(self):
        self.__connection = await aiosqlite.connect("mchickenpanel.db")
        
    async def execute(self, query: str, params=()):
        await self.__connection.execute(query, params)
        await self.__connection.commit()
        
    async def fetchone(self, query: str, params=()):
        async with self.__connection.execute(query, params) as cursor:
            return await cursor.fetchone()
        
    async def fetchall(self, query: str, params=()):
        async with self.__connection.execute(query, params) as cursor:
            return await cursor.fetchall()
    
        
    async def close(self):
        await self.__connection.close()
    