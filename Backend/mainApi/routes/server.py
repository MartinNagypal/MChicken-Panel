from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, Cookie, Request
import models.models as models
import re
import asyncio
from collections import deque
from services.ssh import SSH
from services.rcon import RCON
from services.roles import ROLES
from services.server import SERVER

router = APIRouter(tags=["Server"])
roles = ROLES()

connectedClients: set[WebSocket] = set()
logBuffer = deque(maxlen=200)

@router.get("/status")
async def status(request: Request): #perm: serverViewStats
    auth = request.app.state.auth
    error = request.app.state.error
    ssh = request.app.state.ssh
    server = request.app.state.server
    dockerContainerName = await server.getDockerContainerName()
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    username = await auth.getUsernameBySession(currentSessionToken)
    username = username.get("username")
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "serverViewStats")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        if not ssh:
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
            
        if not await ssh.checkConnection():
            if not await ssh.reconnect():
                raise HTTPException(status_code=500, detail=error.sshNotConfigured)
                
        try:
            result = await ssh.run(f'docker ps | grep {dockerContainerName}')
            if 'healthy' in result.stdout:
                return {"status": "healthy"}
            elif 'starting' in result.stdout:
                return {"status": "starting"}
            elif 'unhealthy' in result.stdout:
                return {"status": "unhealthy"}
            else:
                return {"status": "offline"}
            
        except Exception as e:
            print(f"Error fetching server status: {str(e)}")
            raise HTTPException(status_code=500, detail=error.serverStatusUnavailable)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.get("/stats")
async def stats(request: Request): #perm: serverViewStats
    auth = request.app.state.auth
    error = request.app.state.error
    ssh = request.app.state.ssh
    rcon = request.app.state.rcon
    server = request.app.state.server
    dockerContainerName = await server.getDockerContainerName()
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    username = await auth.getUsernameBySession(currentSessionToken)
    username = username.get("username")
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "serverViewStats")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        if not ssh:
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
            
        if not await ssh.checkConnection():
            if not await ssh.reconnect():
                raise HTTPException(status_code=500, detail=error.sshNotConfigured)
            
        try:
            await rcon.updateRconPassword()
            playerCount = await rcon.run("list")
            playerCountRegex = re.search(r"There are (\d+) of a max of (\d+) players online:", playerCount)
            if playerCountRegex:
                currentPlayers = int(playerCountRegex.group(1))
                maxPlayers = int(playerCountRegex.group(2))

            cpuUsage = await ssh.run(f'docker stats {dockerContainerName} --no-stream --format "{{{{.CPUPerc}}}}"')
            memUsage = await ssh.run(f'docker stats {dockerContainerName} --no-stream --format "{{{{.MemUsage}}}}"')
            currentMemUsage = memUsage.stdout.strip().split("/")[0]
            maxMem = memUsage.stdout.strip().split("/")[1]
            
            uptimeCmd = (
                f"echo $(( ($(date +%s) - "
                f"$(date -d \"$(docker inspect -f '{{{{.State.StartedAt}}}}' {dockerContainerName})\" +%s)) ))"
            )
            
            uptimeResult = await ssh.run(uptimeCmd)
            uptimeSeconds = int(uptimeResult.stdout.strip())
            uptimeHours, uptimeRemainder = divmod(uptimeSeconds, 3600)
            uptimeMinutes = uptimeRemainder // 60
            uptime = f"{uptimeHours:02d}:{uptimeMinutes:02d}"
            

            return {
                "currentPlayers": currentPlayers,
                "maxPlayers": maxPlayers,
                "cpuUsage": cpuUsage.stdout.strip(),
                "currentMemUsage": currentMemUsage,
                "maxMem": maxMem,
                'uptime': uptime
            }
            
        except Exception as e:
            print(f"Error fetching server stats: {str(e)}")
            raise HTTPException(status_code=500, detail=error.serverStatsUnavailable)
        
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.post("/server/startstop")
async def serverStartStop(request: Request): #perm: serverStartStop
    auth = request.app.state.auth
    error = request.app.state.error
    ssh = request.app.state.ssh
    server = request.app.state.server
    dockerContainerName = await server.getDockerContainerName()
    serverDirectory = await server.getServerDirectory()
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "serverStartStop")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        if not ssh:
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
            
        if not await ssh.checkConnection():
            if not await ssh.reconnect():
                raise HTTPException(status_code=500, detail=error.sshNotConfigured)
                
        try:
            status = await ssh.run(f'docker ps | grep {dockerContainerName}')
            if 'healthy' in status.stdout:
                await ssh.runInDir(serverDirectory, f'docker stop {dockerContainerName}')
                return {"message": "Server stop command executed successfully."}
            else:
                await ssh.runInDir(serverDirectory, f'docker start {dockerContainerName}')
                return {"message": "Server start command executed successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=error.serverStartStopFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.post("/server/restart")
async def serverRestart(request: Request): #perm: serverStartStop
    auth = request.app.state.auth
    error = request.app.state.error
    ssh = request.app.state.ssh
    server = request.app.state.server
    dockerContainerName = await server.getDockerContainerName()
    serverDirectory = await server.getServerDirectory()
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    username = await auth.getUsernameBySession(currentSessionToken)
    username = username.get("username")
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "serverStartStop")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        if not ssh:
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
            
        if not await ssh.checkConnection():
            if not await ssh.reconnect():
                raise HTTPException(status_code=500, detail=error.sshNotConfigured)
        
        try:
            await ssh.runInDir(serverDirectory, f'docker restart {dockerContainerName}')
            return {"message": "Server restart command executed successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=error.serverRestartFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.get("/server/data")
async def serverData(request: Request): #perm: serverViewStats
    auth = request.app.state.auth
    error = request.app.state.error
    ssh = request.app.state.ssh
    server = request.app.state.server
    serverDirectory = await server.getServerDirectory()
    dockerComposeFile = await server.getDockerComposeFile()
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "serverViewStats")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        if not ssh:
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
            
        if not await ssh.checkConnection():
            if not await ssh.reconnect():
                raise HTTPException(status_code=500, detail=error.sshNotReachable)
        try:
            serverNameResult = await ssh.runInDir(serverDirectory, f'cat {dockerComposeFile} | grep container_name')
            serverNameMatch = re.search(r"container_name:\s*([a-zA-Z0-9_-]+)", serverNameResult.stdout)
            serverName = serverNameMatch.group(1) if serverNameMatch else "Unknown"
            
            serverVersionResult = await ssh.runInDir(serverDirectory, f'cat {dockerComposeFile} | grep VERSION')
            serverVersionMatch = re.search(r'VERSION:\s*"([^"]+)"', serverVersionResult.stdout)
            serverVersion = serverVersionMatch.group(1) if serverVersionMatch else "Unknown"
            
            return {
                "serverName": serverName,
                "serverVersion": serverVersion,
                "ip": await ssh.getIp()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=error.serverDataUnavailable)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.post("/server/sendCommand")
async def sendCommand(command:models.commandInput, request: Request): #perm: sendCommand
    auth = request.app.state.auth
    error = request.app.state.error
    ssh = request.app.state.ssh
    rcon = request.app.state.rcon
    watcher = request.app.state.logWatcher
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "sendCommand")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        if not ssh:
            raise HTTPException(status_code=500, detail=error.sshNotConfigured)
            
        if not await ssh.checkConnection():
            if not await ssh.reconnect():
                raise HTTPException(status_code=500, detail=error.sshNotReachable)
        
        if(rcon is None):
            raise HTTPException(status_code=500, detail=error.rconError)

        try:
            await rcon.updateRconPassword()
            response = await rcon.run(command.command)
            watcher.buffer.append(response)
            return {"response": response}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=error.serverCommandFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.websocket("/server/logs")
async def server_logs(websocket: WebSocket): #perm: viewConsole
    auth = websocket.app.state.auth
    watcher = websocket.app.state.logWatcher
    ssh = websocket.app.state.ssh
    error = websocket.app.state.error

    token = websocket.cookies.get("sessionToken")
    is_valid = await auth.verifySession(token)
    
    role = await auth.getUserRole(token)
    role = role.get("role")
    permission = await roles.checkPermission(role, "viewConsole")
    
    if not permission:
        await websocket.accept()
        await websocket.send_text("You do not have permission to view the console.")
        await websocket.close()
        return

    if not is_valid.get("valid"):
        await websocket.accept()
        await websocket.send_text("Invalid session token")
        await websocket.close()
        return

    await websocket.accept()
    
    if not ssh:
        await websocket.send_text(error.sshNotConfigured)
        
    if ssh: 
        if not await ssh.checkConnection():
            if not await ssh.reconnect():
                await websocket.send_text(error.sshNotReachable)

    for line in watcher.buffer:
        await websocket.send_text(line)

    watcher.clients.add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        watcher.clients.discard(websocket)


@router.post("/server/sshConfig")
async def sshConfig(sshConfig: models.sshConfig, request: Request): #perm: setupSSH
    auth = request.app.state.auth
    sql = request.app.state.sql
    encryption = request.app.state.encryption
    error = request.app.state.error
    server = request.app.state.server
    watcher = request.app.state.logWatcher
    
    rconPort = await server.getRconPort()
    serverFilesDirectory = await server.getServerFilesDirectory()
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "setupSSH")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        try:
            testSSH = SSH(sshConfig.ip, sshConfig.port, sshConfig.username, sshConfig.password)
            try:
                await testSSH.connect()
                result = await sql.fetchone("SELECT * FROM server WHERE ip = ? AND port = ?", (sshConfig.ip, sshConfig.port))
                if result:
                    request.app.state.ssh = testSSH
                    newRcon = await RCON.create(sshConfig.ip, rconPort, testSSH, serverFilesDirectory)
                    request.app.state.rcon = newRcon
                    await watcher.restart(request.app)
                    await sql.execute("UPDATE server SET username = ?, password = ? WHERE ip = ? AND port = ?", (sshConfig.username, encryption.encryptSecret(sshConfig.password), sshConfig.ip, sshConfig.port))
                    return {"detail": "SSH configuration updated successfully."}
                else:
                    try:
                        await sql.execute("INSERT INTO server (ip, port, username, password) VALUES (?, ?, ?, ?)", (sshConfig.ip, sshConfig.port, sshConfig.username, encryption.encryptSecret(sshConfig.password)))
                        newSSH = SSH(sshConfig.ip, sshConfig.port, sshConfig.username, sshConfig.password)
                        await newSSH.connect()
                        rcon = await RCON.create(sshConfig.ip, rconPort, newSSH, serverFilesDirectory)
                        request.app.state.ssh = newSSH
                        request.app.state.rcon = rcon
                        await watcher.restart(request.app)
                        return {"detail": "SSH configuration saved and connected successfully."}
                    except Exception as e:
                        print(f"Error saving SSH configuration: {str(e)}")
                        raise HTTPException(status_code=500, detail=error.sshConfigSaveFailed)
                        
            except Exception as e:
                print(f"Error connecting to SSH server: {str(e)}")
                raise HTTPException(status_code=400, detail=error.sshConnectionFailed)
            
        except Exception as e:
            print(f"Error during SSH configuration: {str(e)}")
            raise HTTPException(status_code=500, detail=error.sshConfigFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
    

@router.get("/server/sshReconnect")
async def sshReconnect(request:Request):
    auth = request.app.state.auth
    ssh = request.app.state.ssh
    sql = request.app.state.sql
    encryption = request.app.state.encryption
    error = request.app.state.error
    server = request.app.state.server
    watcher = request.app.state.logWatcher
    
    rconPort = await server.getRconPort()
    serverFilesDirectory = await server.getServerFilesDirectory()
    ip = await server.getIp()
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    if isValidSession == True:
        try:
            if ssh is not None:
                if await ssh.checkConnection():
                    raise HTTPException(status_code=409, detail=error.sshConnectExists)
                
            result = await sql.fetchone("SELECT * FROM server")
            if result:
                try:
                    newSSH = SSH(result[1], result[2], result[3], encryption.decryptSecret(result[4]))
                    await asyncio.wait_for(newSSH.connect(), timeout=1)
                    request.app.state.ssh = newSSH
                    newRcon = await RCON.create(ip, rconPort, newSSH, serverFilesDirectory)
                    request.app.state.rcon = newRcon
                    await watcher.restart(request.app)
                    
                except(asyncio.TimeoutError, TimeoutError):
                    raise HTTPException(status_code=500, detail=error.sshNotReachable)
                
                except Exception as e:
                    print(f'Error establishing new SSH connection: {e}')
                    raise HTTPException(status_code=500, detail=error.sshConnectionFailed)
            else:
                raise HTTPException(status_code=500, detail=error.sshNotConfigured)
        except:
            raise HTTPException(status_code=500, detail=error.internalServerError)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
    
@router.post("/server/configure")
async def configureServer(serverData: models.configureServer, request: Request):
    auth = request.app.state.auth
    sql = request.app.state.sql
    encryption = request.app.state.encryption
    error = request.app.state.error
    watcher = request.app.state.logWatcher
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "sendCommand")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:

        result = await sql.fetchone("SELECT * FROM server WHERE ip = ?", (serverData.sshIp,))
        if result:
            raise HTTPException(status_code=401, detail=error.configurationAlreadyExists)
        
        if not await error.validateIp(serverData.sshIp):
            raise HTTPException(status_code=400, detail=error.invalidIp )
        
        if not await error.validatePort(serverData.sshPort):
            raise HTTPException(status_code=400, detail=error.invalidSshPort)
        
        if not await error.validatePort(serverData.rconPort):
            raise HTTPException(status_code=400, detail=error.invalidRconPort)

        try:
            testSSH = SSH(serverData.sshIp, serverData.sshPort, serverData.sshUsername, serverData.sshPassword)
            await asyncio.wait_for(testSSH.connect(), timeout=2)
            if not await testSSH.checkConnection():
                raise HTTPException(status_code=500, detail=error.sshNotReachable)
            
            if serverData.dirToBackups == "none":
                dirToBackups = None
            else:
                dirToBackups = serverData.dirToBackups
            
            server = SERVER(serverData.containerName, serverData.dirToDC_File, serverData.dirToServerData, request.app.state.compose, serverData.sshIp, serverData.rconPort, request.app.state.rconPassword, request.app.state.allowRegistration)
            request.app.state.server = server
            request.app.state.ssh = testSSH
            rcon = await RCON.create(serverData.sshIp, serverData.rconPort, testSSH, serverData.dirToServerData)
            request.app.state.rcon = rcon
            await sql.execute("INSERT INTO server (ip, port, username, password, rconPort, containerName, dirToServerData, dirToDC_File, dirToBackups) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (serverData.sshIp, serverData.sshPort, serverData.sshUsername, encryption.encryptSecret(serverData.sshPassword), serverData.rconPort, serverData.containerName, serverData.dirToServerData, serverData.dirToDC_File, dirToBackups))
            await watcher.restart(request.app)
            
        except:
            raise HTTPException(status_code=500, detail=error.sshNotReachable)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
        
@router.get("/server/configure/current")
async def getCurrentConfig(request: Request): #perm: viewServerConfig
    auth = request.app.state.auth
    sql = request.app.state.sql
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "viewServerConfig")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        result = await sql.fetchone("SELECT * FROM server")
        if result:
            return {
                "ip": result[1],
                "port": result[2],
                "username": result[3],
                "rconPort": result[5],
                "containerName": result[6],
                "dirToServerData": result[7],
                "dirToDC_File": result[8],
                "dirToBackups": result[8]
            }
        else:
            raise HTTPException(status_code=400, detail=error.noServerConfigured)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
    

@router.post("/server/configure/delete")
async def deleteServerConf(request: Request): #perm: setupSSH
    auth = request.app.state.auth
    sql = request.app.state.sql
    encryption = request.app.state.encryption
    error = request.app.state.error
    watcher = request.app.state.logWatcher
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "setupSSH")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        await sql.execute("DELETE FROM server")
        request.app.state.ssh = None
        request.app.state.rcon = None
        await watcher.stop()
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)
    

@router.post("/server/configure/update")
async def deleteServerConf(serverData:models.configureServer, request: Request): #perm: setupSSH
    auth = request.app.state.auth
    sql = request.app.state.sql
    encryption = request.app.state.encryption
    error = request.app.state.error
    watcher = request.app.state.logWatcher
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "setupSSH")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        result = await sql.fetchone("SELECT * FROM server")
        if result:
            
            searchIp = result[1]
            
            if serverData.sshIp != "none":
                if not await error.validateIp(serverData.sshIp):
                    raise HTTPException(status_code=400, detail=error.invalidIp)

                newSSH = SSH(serverData.sshIp, result[2], result[3], encryption.decryptSecret(result[4]))
                try:
                    await asyncio.wait_for(newSSH.connect(), timeout=3)
                except:
                    raise HTTPException(status_code=500, detail=error.sshConfigSaveFailed)
                
                await sql.execute("UPDATE server SET ip = ? WHERE ip = ?",(serverData.sshIp, result[1],))
                searchIp = serverData.sshIp
      
            if serverData.sshPort != 0:
                if not await error.validatePort(serverData.sshPort):
                    raise HTTPException(status_code=400, detail=error.invalidSshPort)
                
                newSSH = SSH(result[1], serverData.sshPort, result[3], encryption.decryptSecret(result[4]))
                try:
                    await asyncio.wait_for(newSSH.connect(), timeout=3)
                except:
                    raise HTTPException(status_code=500, detail=error.sshConfigSaveFailed)
                
                await sql.execute("UPDATE server SET port = ? WHERE ip = ?",(serverData.sshPort, result[1],))
                
            if serverData.sshUsername != "none":
                
                newSSH = SSH(result[1], result[2], serverData.sshUsername, encryption.decryptSecret(result[4]))
                try:
                    await asyncio.wait_for(newSSH.connect(), timeout=3)
                except:
                    raise HTTPException(status_code=500, detail=error.sshConfigSaveFailed)
                await sql.execute("UPDATE server SET username = ? WHERE ip = ?",(serverData.sshUsername, result[1],))
                
            if serverData.sshPassword != "none":
                newSSH = SSH(result[1], result[2], result[3], serverData.sshPassword)
                try:
                    await asyncio.wait_for(newSSH.connect(), timeout=3)
                except:
                    raise HTTPException(status_code=500, detail=error.sshConfigSaveFailed)
                await sql.execute("UPDATE server SET password = ? WHERE ip = ?",(encryption.encryptSecret(serverData.sshPassword), result[1],))
                
            if serverData.rconPort != 0:
                await sql.execute("UPDATE server SET rconPort = ? WHERE ip = ?",(serverData.rconPort, result[1],))
                
            if serverData.containerName != "none":
                await sql.execute("UPDATE server SET containerName = ? WHERE ip = ?",(serverData.containerName, result[1],))
                
            if serverData.dirToServerData != "none":
                await sql.execute("UPDATE server SET dirToServerData = ? WHERE ip = ?",(serverData.dirToServerData, result[1],))
                
            if serverData.dirToDC_File != "none":
                await sql.execute("UPDATE server SET dirToDC_File = ? WHERE ip = ?",(serverData.dirToDC_File, result[1],))
                
            if serverData.dirToBackups != "none":
                await sql.execute("UPDATE server SET dirToBackups = ? WHERE ip = ?",(serverData.dirToBackups, result[1],))
                
            newData = await sql.fetchone("SELECT * FROM server")
            saveSSH = SSH(result[1], result[2], result[3], encryption.decryptSecret(result[4]))
            try:
                await asyncio.wait_for(saveSSH.connect(), timeout=3)
            except:
                raise HTTPException(status_code=500, detail=error.sshConnectionFailed)
            
            request.app.state.ssh = saveSSH
            saveRcon = RCON(result[1], result[2], request.app.state.ssh, result[7])
            request.app.state.rcon = saveRcon
            newServer = SERVER(result[6], result[8], result[7], request.app.state.compose, result[1], result[5], request.app.state.rconPassword, request.app.state.allowRegistration)
            request.app.state.server = newServer
            await watcher.restart(request.app)
            
        else:
            raise HTTPException(status_code=409, detail=error.nothingToUpdate)