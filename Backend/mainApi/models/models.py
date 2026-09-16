from pydantic import BaseModel

class commandInput(BaseModel):
    command: str
    
class sshConfig(BaseModel):
    ip: str
    port: int
    username: str
    password: str
    
class userInput(BaseModel):
    username: str
    password: str
    
class username(BaseModel):
    username: str
    
class password(BaseModel):
    password: str
    
class deleteUserInput(BaseModel):
    username: str
    password: str
    
class roleUpdate(BaseModel):
    username: str
    newRole: str
    password: str
    
class createUserInput(BaseModel):
    username: str
    password: str
    role: str