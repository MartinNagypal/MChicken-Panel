import asyncssh

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
        if self.__connection is None:
            await self.connect()
        return await self.__connection.run(command)
    
    async def runInDir(self, dir:str, command:str):
        if self.__connection is None:
            await self.connect()
        return await self.__connection.run(f'cd {dir} && {command}')
    
    async def close(self):
        if self.__connection is not None:
            self.__connection.close()
            await self.__connection.wait_closed()
            self.__connection = None