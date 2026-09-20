class SERVER:
    def __init__(self, dockerContainerName, serverDirectory, serverFilesDirectory, dockerComposeFile, ip, rconPort, rconPassword, allowRegistration):
        self.__dockerContainerName = dockerContainerName
        self.__serverDirectory = serverDirectory
        self.__serverFilesDirectory = serverFilesDirectory
        self.__dockerComposeFile = dockerComposeFile
        self.__ip = ip
        self.__rconPort = rconPort
        self.__rconPassword = rconPassword
        self.__allowRegistration = allowRegistration

    async def getDockerContainerName(self):
        return self.__dockerContainerName
    
    async def getServerDirectory(self):
        return self.__serverDirectory
    
    async def getServerFilesDirectory(self):
        return self.__serverFilesDirectory
    
    async def getDockerComposeFile(self):   
        return self.__dockerComposeFile
    
    async def getIp(self):
        return self.__ip
    
    async def getRconPort(self):
        return self.__rconPort
    
    async def getRconPassword(self):
        return self.__rconPassword
    
    async def getAllowRegistration(self):
        return self.__allowRegistration