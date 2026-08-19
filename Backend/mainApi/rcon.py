import asyncio
from aiomcrcon import Client

class RCON:
    def __init__(self, ip, port, password):
        self.__ip = ip
        self.__port = int(port)
        self.__password = password
        
        
    async def run(self, command:str):
        client = Client(self.__ip, self.__password, port=self.__port)
        await client.connect()
        result = await client.send_cmd(command)
        await client.close()
        return result