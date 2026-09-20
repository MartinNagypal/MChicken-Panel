from collections import deque
import asyncio

class LogWatcher:
    def __init__(self):
        self.clients = set()
        self.buffer = deque(maxlen=200)
        self.task = None
        self.lock = asyncio.Lock()

    async def watch(self, app):
        ssh = app.state.ssh
        server_files_directory = await app.state.server.getServerFilesDirectory()

        if ssh is None:
            return

        async for line in ssh.stream(
            f"tail -n 150 -F {server_files_directory}logs/latest.log"
        ):
            if line:
                self.buffer.append(line)

                for websocket in self.clients.copy():
                    await websocket.send_text(line)

    async def start(self, app):
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.watch(app))

    async def stop(self):
        if self.task is None:
            return

        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
        finally:
            self.task = None

    async def restart(self, app):
        async with self.lock:
            await self.stop()
            await self.start(app)