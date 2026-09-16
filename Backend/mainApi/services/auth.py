from datetime import datetime, timedelta, timezone

class AUTH:
    def __init__(self, db, encryption, sessionExpirationHours: int = 1):
        self.__db = db
        self.__encryption = encryption
        self.__sessionExpirationHours = sessionExpirationHours

    async def register(self, username: str, password: str, role:str, isFirstUser: bool = False):
        await self.__db.execute("""
            CREATE TABLE IF NOT EXISTS systemUser(
                userId INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                isFirstUser BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        
        encryptedPassword = self.__encryption.hashPassword(password)
        doesUserExist = await self.__db.fetchone("SELECT * FROM systemUser WHERE username = ?", (username,))
        if doesUserExist:
            return {"error": "1"}
        else:
            await self.__db.execute("INSERT INTO systemUser (username, password, role, isFirstUser) VALUES (?, ?, ?, ?)", (username, encryptedPassword, role, isFirstUser))
            session = await self.createSession(username)
            sessionToken = session.get("sessionToken")
            return {"message": "User registered successfully.", "sessionToken": sessionToken, "sessionExpirationHours": self.__sessionExpirationHours}

    async def createSession(self, username: str):
        sessionToken = self.__encryption.generateSessionToken()
        sessionTokenHashed = self.__encryption.hashSessionToken(sessionToken)
        sessionCreatedAt = datetime.now(timezone.utc)
        sessionExpiresAt = sessionCreatedAt + timedelta(hours=self.__sessionExpirationHours)
        
        try:
            await self.__db.execute("""
                CREATE TABLE IF NOT EXISTS userSession(
                    sessionId INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    userId INTEGER NOT NULL,
                    sessionToken TEXT NOT NULL,
                    sessionCreatedAt TEXT NOT NULL,
                    sessionExpiresAt TEXT NOT NULL
                )
            """)
            userId = await self.__db.fetchone("SELECT userId FROM systemUser WHERE username = ?", (username,))
            if userId:
                userId = userId[0]
                await self.__db.execute("INSERT INTO userSession (username, userId, sessionToken, sessionCreatedAt, sessionExpiresAt) VALUES (?, ?, ?, ?, ?)", (username, userId, sessionTokenHashed, sessionCreatedAt.isoformat(), sessionExpiresAt.isoformat()))
                return {"sessionToken": sessionToken, "sessionExpiresAt": sessionExpiresAt}
            else:
                return {"error": "User not found."}
            
        except Exception as e:
            return {"error": str(e)}
        
    async def verifySession(self, sessionToken: str):
        try:
            hashedSessionToken = self.__encryption.hashSessionToken(sessionToken)
            session = await self.__db.fetchone("SELECT * FROM userSession WHERE sessionToken = ?", (hashedSessionToken,))
            if session:
                sessionExpiresAt = session[5]
                if datetime.now(timezone.utc) < datetime.fromisoformat(sessionExpiresAt):
                    return {"valid": True, "username": session[1]}
                else:
                    await self.__db.execute("DELETE FROM userSession WHERE sessionToken = ?", (sessionToken,))
                    return {"valid": False, "error": "Session expired."}
            else:
                return {"valid": False, "error": "Session not found."}
        except Exception as e:
            return {"valid": False, "error": str(e)}
        
    async def login(self, username: str, password: str):
        try:
            user = await self.__db.fetchone("SELECT * FROM systemUser WHERE username = ?", (username,))
            if user:
                hashedPassword = user[2]
                if self.__encryption.verifyPassword(password, hashedPassword):
                    session = await self.createSession(username)
                    sessionToken = session.get("sessionToken")
                    return {"message": "Login successful.", "sessionToken": sessionToken, "sessionExpirationHours": self.__sessionExpirationHours}
                else:
                    return {"error": "Invalid password.", "statusCode": 401}
            else:
                return {"error": "User not found.", "statusCode": 401}
        except Exception as e:
            return {"error": str(e), "statusCode": 500}
        
    async def logout(self, sessionToken: str):
        try:
            hashedSessionToken = self.__encryption.hashSessionToken(sessionToken)
            session = await self.__db.fetchone("SELECT * FROM userSession WHERE sessionToken = ?", (hashedSessionToken,))
            if not session:
                return {"error": "Session not found.", "statusCode": 401}
            
            await self.__db.execute("DELETE FROM userSession WHERE sessionToken = ?", (hashedSessionToken,))
            return {"message": "Logged out successfully."}
        except Exception as e:
            return {"error": str(e)}
        
    async def verifyPassword(self, username: str, password: str):
        try:
            user = await self.__db.fetchone("SELECT * FROM systemUser WHERE username = ?", (username,))
            if user:
                hashedPassword = user[2]
                if self.__encryption.verifyPassword(password, hashedPassword):
                    return {"valid": True}
                else:
                    return {"valid": False, "error": "Invalid password."}
            else:
                return {"valid": False, "error": "User not found."}
        except Exception as e:
            return {"valid": False, "error": str(e)}
        
    async def isFirstUser(self):
        doesTableExist = await self.__db.exists("systemUser")
        if doesTableExist == True:
            result = await self.__db.fetchone("SELECT * FROM systemUser LIMIT 1")
            if result:
                return False
            else:
                return True
        else:
            return True

    async def validatePassword(self, password: str):
        minLength = 8
        hasUpperCase = any(char.isupper() for char in password)
        hasLowerCase = any(char.islower() for char in password)
        hasNumber = any(char.isdigit() for char in password)

        if(len(password) >= minLength and hasUpperCase and hasLowerCase and hasNumber): 
            return {"valid": True}
        else:
            return {"valid": False}
        
    async def validateUsername(self, username: str):
        minLength = 4
        maxLength = 16

        if(len(username) >= minLength and len(username) <= maxLength): 
            return {"valid": True}
        else:
            return {"valid": False}
        
    async def getUserRole(self, sessionToken: str):
        try:
            hashedSessionToken = self.__encryption.hashSessionToken(sessionToken)
            userId = await self.__db.fetchone("SELECT userId FROM userSession WHERE sessionToken = ?", (hashedSessionToken,))
            if userId:
                userId = userId[0]
                role = await self.__db.fetchone("SELECT role FROM systemUser WHERE userId = ?", (userId,))
                if role:
                    return {"role": role[0]}
                else:
                    return {"error": "User not found."}
            else:
                return {"error": "Session not found."}
        except Exception as e:
            print(f"Error in getUserRole: {e}")
            return {"error": str(e)}
        
    async def getUserRoleByUsername(self, username: str):
        try:
            role = await self.__db.fetchone("SELECT role FROM systemUser WHERE username = ?", (username,))
            if role:
                return {"role": role[0]}
            else:
                return {"error": "User not found."}
        except Exception as e:
            print(f"Error in getUserRoleByUsername: {e}")
            return {"error": str(e)}
        
    async def getAllUsers(self):
        try:
            users = await self.__db.fetchall("SELECT userId, username, role FROM systemUser")
            return {"users": [{"userId": user[0], "username": user[1], "role": user[2]} for user in users]}
        except Exception as e:
            print(f"Error in getAllUsers: {e}")
            return {"error": str(e)}
        
    async def getUsernameBySession(self, sessionToken: str):
        try:
            hashedSessionToken = self.__encryption.hashSessionToken(sessionToken)
            username = await self.__db.fetchone("SELECT username FROM userSession WHERE sessionToken = ?", (hashedSessionToken,))
            if username:
                return {"username": username[0]}
            else:
                return {"error": "Session not found."}
        except Exception as e:
            print(f"Error in getUsername: {e}")
            return {"error": str(e)}
        
    async def logoutAllSessions(self, username: str):
        try:
            await self.__db.execute("DELETE FROM userSession WHERE username = ?", (username,))
            return {"message": "Logged out from all sessions successfully."}
        except Exception as e:
            print(f"Error in logoutAllSessions: {e}")
            return {"error": str(e)}
        
    async def countSessions(self, username:str):
        try: 
            count = await self.__db.execute("SELECT COUNT(*) FROM userSession WHERE username = ? GROUP BY username", (username,))
            return {"count": count}
        except Exception as e:
            print(f'Error in countSessions: {e}')
            return {"error": str(e)}
        
    async def deleteUser(self, username: str):
        try:
            await self.__db.execute("DELETE FROM systemUser WHERE username = ?", (username,))
            await self.logoutAllSessions(username)
            return {"message": "User deleted successfully."}
        except Exception as e:
            print(f"Error in deleteUser: {e}")
            return {"error": str(e)}
        
    async def updateUserRole(self, username: str, newRole: str):
        try:
            await self.__db.execute("UPDATE systemUser SET role = ? WHERE username = ?", (newRole, username))
            return {"message": "User role updated successfully."}
        except Exception as e:
            print(f"Error in updateUserRole: {e}")
            return {"error": str(e)}
        
    async def isFirstUserBySession(self, sessionToken: str):
        try:
            hashedSessionToken = self.__encryption.hashSessionToken(sessionToken)
            userId = await self.__db.fetchone("SELECT userId FROM userSession WHERE sessionToken = ?", (hashedSessionToken,))
            if userId:
                userId = userId[0]
                isFirstUser = await self.__db.fetchone("SELECT isFirstUser FROM systemUser WHERE userId = ?", (userId,))
                if isFirstUser:
                    return {"isFirstUser": bool(isFirstUser[0])}
                else:
                    return {"error": "User not found."}
            else:
                return {"error": "Session not found."}
        except Exception as e:
            print(f"Error in isUserFirstUserBySession: {e}")
            return {"error": str(e)}