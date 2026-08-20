from pydantic import BaseModel

class commandInput(BaseModel):
    command: str
    
class sshConfig(BaseModel):
    ip: str
    port: int
    username: str
    password: str