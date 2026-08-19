# services/ssh.py

import asyncssh


class SSHManager:

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.connection = None

    async def connect(self):
        self.connection = await asyncssh.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            known_hosts=None
        )

    async def run(self, command: str):
        if self.connection is None:
            await self.connect()

        return await self.connection.run(command)

    async def close(self):
        if self.connection:
            self.connection.close()
            await self.connection.wait_closed()
            self.connection = None