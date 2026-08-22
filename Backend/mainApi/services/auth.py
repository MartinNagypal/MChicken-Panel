from datetime import datetime, timedelta, timezone

class AUTH:
    def __init__(self, db, encryption, sessionExpirationHours: int = 1):
        self.__db = db
        self.__encryption = encryption
        self.__sessionExpirationHours = sessionExpirationHours

    async def register(self, username: str, password: str):
        await self.__db.execute("""
            CREATE TABLE IF NOT EXISTS systemUser(
                userId INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        
        encryptedPassword = self.__encryption.hashPassword(password)
        isFirstUser = await self.__db.fetchone("SELECT * FROM systemUser LIMIT 1")
        if not isFirstUser:
            role = "admin"
            await self.__db.execute("INSERT INTO systemUser (username, password, role) VALUES (?, ?, ?)", (username, encryptedPassword, role))
            session =await self.createSession(username)
            sessionToken = session.get("sessionToken")
            sessionExpiresAt = session.get("sessionExpiresAt")
            return {"message": "First user registered successfully as admin.", "sessionToken": sessionToken, "sessionExpirationHours": self.__sessionExpirationHours }
        else:
            doesUserExist = await self.__db.fetchone("SELECT * FROM systemUser WHERE username = ?", (username,))
            if doesUserExist:
                return {"error": "User already exists."}
            else:
                role = "user"
                await self.__db.execute("INSERT INTO systemUser (username, password, role) VALUES (?, ?, ?)", (username, encryptedPassword, role))
                session = await self.createSession(username)
                sessionToken = session.get("sessionToken")
                sessionExpiresAt = session.get("sessionExpiresAt")
                return {"message": "User registered successfully.", "sessionToken": sessionToken, "sessionExpirationHours": self.__sessionExpirationHours}

    async def createSession(self, username: str):
        sessionToken = self.__encryption.generateSessionToken()
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
                await self.__db.execute("INSERT INTO userSession (username, userId, sessionToken, sessionCreatedAt, sessionExpiresAt) VALUES (?, ?, ?, ?, ?)", (username, userId, sessionToken, sessionCreatedAt.isoformat(), sessionExpiresAt.isoformat()))
                return {"sessionToken": sessionToken, "sessionExpiresAt": sessionExpiresAt}
            else:
                return {"error": "User not found."}
            
        except Exception as e:
            return {"error": str(e)}
        
    async def verifySession(self, sessionToken: str):
        try:
            session = await self.__db.fetchone("SELECT * FROM userSession WHERE sessionToken = ?", (sessionToken,))
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
                    return {"error": "Invalid password."}
            else:
                return {"error": "User not found."}
        except Exception as e:
            return {"error": str(e)}
        
    async def logout(self, sessionToken: str):
        try:
            await self.__db.execute("DELETE FROM userSession WHERE sessionToken = ?", (sessionToken,))
            return {"message": "Logged out successfully."}
        except Exception as e:
            return {"error": str(e)}