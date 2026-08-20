import asyncio
from aiomcrcon import Client

class RCON:
    def __init__(self, ip, port, password):
        self.__ip = ip
        self.__port = int(port)
        self.__password = password
        self.__client = Client(self.__ip, self.__password, port=self.__port)

    async def run(self, command:str):
        await self.__client.connect()
        result = await self.__client.command(command)
        await self.__client.close()
        return result