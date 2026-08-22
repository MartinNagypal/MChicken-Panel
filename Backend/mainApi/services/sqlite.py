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
    
    async def exists(self, tableName: str) -> bool:
        cursor = await self.__connection.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
            )
            """,
            (tableName,)
        )

        result = await cursor.fetchone()
        return bool(result[0])


    async def close(self):
        await self.__connection.close()
    