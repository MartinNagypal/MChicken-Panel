class ROLES:
    def __init__(self):
        self.__rolePermission = {
            "admin": {
                "serverStartStop": True,
                "serverViewStats": True,
                "manageBackups": True,
                "viewBackups": True,
                "viewConsole": True,
                "sendCommand": True,
                "setupSSH": True,
                "setupRCON": True,
                "manageUsers": True,
                "viewUsers": True,
                "modifyUsers": True
            },
            
            "mod": {
                "serverStartStop": True,
                "serverViewStats": True,
                "manageBackups": True,
                "viewBackups": True,
                "viewConsole": True,
                "sendCommand": True,
                "setupSSH": False,
                "setupRCON": False,
                "manageUsers": False,
                "viewUsers": True,
                "modifyUsers": False
            },
            
            "user": {
                "serverStartStop": False,
                "serverViewStats": True,
                "manageBackups": False,
                "viewBackups": True,
                "viewConsole": True,
                "sendCommand": False,
                "setupSSH": False,
                "setupRCON": False,
                "manageUsers": False,
                "viewUsers": False,
                "modifyUsers": False
            }
        }
        
    async def checkPermission(self, role:str, permission:str):
        if role not in self.__rolePermission:
            return False
        if permission not in self.__rolePermission[role]:
            return False
        return self.__rolePermission[role][permission]