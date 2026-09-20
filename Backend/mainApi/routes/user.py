from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, Cookie, Request
import models.models as models
from services.roles import ROLES

router = APIRouter(tags=["User"])
roles = ROLES()

@router.get("/users")
async def getUsers(request: Request): #perm: viewUsers
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "viewUsers")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        users = await auth.getAllUsers()
        return {"users": users}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.get("/users/user/session")
async def getUserBySession(request: Request):
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        username = await auth.getUsernameBySession(currentSessionToken)
        username = username.get("username")
        role = await auth.getUserRoleByUsername(username)
        role = role.get("role")
        return {"username": username, "role": role}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.get("/user/role/session")
async def getUserRole(request: Request, response: Response):
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        username = await auth.getUsernameBySession(currentSessionToken)
        username = username.get("username")
        role = await auth.getUserRoleByUsername(username)
        role = role.get("role")
        return{"role": role}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@router.get("/user/username")
async def getUsername(request: Request):
    auth = request.app.state.auth
    error = request.app.state.error
    sql = request.app.state.sql
    encryption = request.app.state.encryption
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        username = await sql.fetchone("SELECT username FROM userSession WHERE sessionToken = ?", (encryption.hashSessionToken(currentSessionToken),))
        return {"username": username}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)

@router.get("/session/count")
async def sessionCount(request: Request, response: Response):
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail=error.noActiveSession)
    
    isValid = await auth.verifySession(currentSessionToken)
    if isValid.get("valid") == True:
        username = isValid.get("username")
        result = await auth.countSessions(username)
        return {"sessionCount": result.get("count")}
        
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.post("/users/user/create")
async def createUser(user: models.createUserInput, request: Request, response: Response): #perm: manageUsers
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "manageUsers")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        role = await auth.getUserRole(currentSessionToken)
        role = role.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail=error.noPermission)
        
        isUsernameValid = await auth.validateUsername(user.username)
        if isUsernameValid.get("valid") == False:
            raise HTTPException(status_code=400, detail=error.usernameRequirementNotFulfilled)
            
        isPasswordValid = await auth.validatePassword(user.password)
        if isPasswordValid.get("valid") == False:
            raise HTTPException(status_code=400, detail=error.passwordRequirementNotFulfilled)
        
        rolesList = await roles.getRolesList()
        if user.role not in rolesList:
            raise HTTPException(status_code=400, detail=error.invalidRole)
        
        result = await auth.register(user.username, user.password, user.role, False, False)
        if result.get("message"):
            return {"message": result.get("message")}
        else:
            if(result.get("error") == "1"):
                raise HTTPException(status_code=409, detail=error.userAlreadyExists)
            else:
                raise HTTPException(status_code=500, detail=error.registrationFailed)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.post("/user/verifyPassword")
async def verifyPassword(password: models.password, request: Request, response: Response):
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    if isValidSession == True:
        username = await auth.getUsernameBySession(currentSessionToken)
        username = username.get("username")
        result = await auth.verifyPassword(username, password.password)
        if result.get("valid") == True:
            return {"valid": True}
        else:
            raise HTTPException(status_code=401, detail=error.invalidPassword)
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.post("/user/delete")
async def deleteUser(username: models.deleteUserInput, request: Request, response: Response): #perm: manageUsers
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "manageUsers")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        currentUsername = await auth.getUsernameBySession(currentSessionToken)
        currentUsername = currentUsername.get("username")
        currentRole = await auth.getUserRole(currentSessionToken)
        currentRole = currentRole.get("role")
        deleteUserRole = await auth.getUserRoleByUsername(username.username)
        
        if currentRole == deleteUserRole.get("role"):
            isFirstUser = await auth.isFirstUserBySession(currentSessionToken)
            isFirstUser = isFirstUser.get("isFirstUser")
            if not isFirstUser:
                raise HTTPException(status_code=403, detail="You cannot delete a user with the same role as you.")
            else:
                pass
        
        if currentUsername == username.username:
            raise HTTPException(status_code=403, detail="You cannot delete your own account.")
        
        validPassword = await auth.verifyPassword(currentUsername, username.password)
        validPassword = validPassword.get("valid")
        if not validPassword:
            raise HTTPException(status_code=401, detail=error.invalidPassword)
        
        result = await auth.deleteUser(username.username)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=error.userDeletionError)
        else:
            return {"message": result.get("message")}


@router.post("/user/role/update")
async def updateUserRole(roleUpdate: models.roleUpdate, request: Request, response: Response): #perm: manageUsers
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    isValidSession = await auth.verifySession(currentSessionToken)
    isValidSession = isValidSession.get("valid")
    
    role = await auth.getUserRole(currentSessionToken)
    role = role.get("role")
    permission = await roles.checkPermission(role, "manageUsers")
    
    if not permission:
        raise HTTPException(status_code=403, detail=error.noPermission)
    
    if isValidSession == True:
        rolesList = await roles.getRolesList()
        if roleUpdate.newRole not in rolesList:
            raise HTTPException(status_code=400, detail=error.invalidRole)
        
        currentUsername = await auth.getUsernameBySession(currentSessionToken)
        currentUsername = currentUsername.get("username")
        if currentUsername == roleUpdate.username:
            raise HTTPException(status_code=403, detail="You cannot change your own role.")
        
        userRole = await auth.getUserRoleByUsername(roleUpdate.username)
        userRole = userRole.get("role")
        if userRole == role:
            raise HTTPException(status_code=403, detail="You cannot change the role of a user with the same role as you.")
        
        validPassword = await auth.verifyPassword(currentUsername, roleUpdate.password)
        validPassword = validPassword.get("valid")
        if not validPassword:
            raise HTTPException(status_code=401, detail=error.invalidPassword)
        
        result = await auth.updateUserRole(roleUpdate.username, roleUpdate.newRole)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=error.userRoleUpdateError)
        
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)