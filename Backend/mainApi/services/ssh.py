import asyncssh
import asyncio

class SSH:
    def __init__(self, ip, port, username, password):
        self.__ip = ip
        self.__port = port
        self.__username = username
        self.__password = password
        self.__connection = None
        
    async def connect(self):
        self.__connection = await asyncssh.connect(self.__ip, port=self.__port, username=self.__username, password=self.__password, known_hosts=None)
        
    async def run(self, command:str):
        await self._ensureConnection()
        
        try:
            return await self.__connection.run(command)
        except (asyncssh.Error, OSError, ConnectionError):
            self.__connection = None
            await self.connect()
            return await self.__connection.run(command)
    
    async def runInDir(self, dir:str, command:str):
        await self._ensureConnection()

        try:
            return await self.__connection.run(f'cd {dir} && {command}')
        except (asyncssh.Error, OSError, ConnectionError):
            self.__connection = None
            await self.connect()
            return await self.__connection.run(f'cd {dir} && {command}')
    
    async def stream(self, command: str):
        await self._ensureConnection()
        
        try:
            process = await self.__connection.create_process(command)
            async for line in process.stdout:
                yield line.rstrip()
        
        except (asyncssh.Error, OSError, ConnectionError):
            self.__connection = None
            await self.connect()
            
            process = await self.__connection.create_process(command)
            async for line in process.stdout:
                yield line.rstrip()

    async def close(self):
        if self.__connection is not None:
            self.__connection.close()
            await self.__connection.wait_closed()
            self.__connection = None
            
    async def getIp(self):
        return self.__ip
    
    async def _ensureConnection(self):
        if self.__connection is None or self.__connection.is_closed():
            await asyncio.wait_for(self.connect(), timeout=1)
            
    async def checkConnection(self):
        if self.__connection is None:
            return False
        
        if self.__connection.connection_lost():
            return False
        
        if self.__connection.is_closed():
            return False
        
        return True
        
    async def reconnect(self):
        try:
            await self._ensureConnection()
            return await self.checkConnection()
        except:
            return False
            

    