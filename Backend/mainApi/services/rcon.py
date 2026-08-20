import asyncio
from aiomcrcon import Client
from services.ssh import SSH

class RCON:
    def __init__(self, ip, port, ssh, serverFilesDir):
        self.__ip = ip
        self.__port = int(port)
        self.__ssh = ssh
        self.__serverFilesDir = serverFilesDir
        self.__password = None
        self.__client = None
        
    @classmethod
    async def create(cls, ip, port, ssh, serverFilesDir):
        self = cls(ip, port, ssh, serverFilesDir)
        self.__password = await self.__getRconPassword()
        self.__client = Client(self.__ip, self.__password, self.__port)
        return self

    async def run(self, command:str):
        await self.__client.connect()
        result = await self.__client.command(command)
        await self.__client.close()
        return result
    
    async def __getRconPassword(self):
        result = await self.__ssh.runInDir(self.__serverFilesDir, "cat server.properties | grep rcon.password")
        rconPassword = result.stdout.strip().split("=")[1]
        return rconPassword
    
    async def updateRconPassword(self):
        rconPassword = await self.__getRconPassword()
        if(self.__password != rconPassword):
            self.__password = rconPassword
            self.__client = Client(self.__ip, self.__password, self.__port)