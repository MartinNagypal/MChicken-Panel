from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, Cookie, Request
import models.models as models


router = APIRouter(tags=["Auth"])

@router.post("/login")
async def login(user: models.userInput, request: Request, response: Response):
    auth = request.app.state.auth
    error = request.app.state.error
    secureCookie = request.app.state.secureCookie
    
    #check if user is logged in
    currentSessionToken = request.cookies.get("sessionToken")
    if currentSessionToken:
        isValidSession = await auth.verifySession(currentSessionToken)
        isValidSession = isValidSession.get("valid")
        if isValidSession == True:
            raise HTTPException(status_code=409, detail=error.alreadyLoggedIn)
        else:
            response.delete_cookie("sessionToken", path="/")
    
    #attempt login
    result = await auth.login(user.username, user.password)
    if result.get("error"):
        if result.get("statusCode") == 401:
            raise HTTPException(status_code=401, detail=error.invalidUsernameOrPassword)
        else:
            raise HTTPException(status_code=500, detail=error.loginFailed)
        
    #generate session
    sessionToken = result.get("sessionToken")
    if sessionToken:
        sessionExpirationHours = result.get("sessionExpirationHours")
        response.set_cookie(
            key="sessionToken",
            value=sessionToken,
            httponly=True,
            secure=secureCookie,
            samesite="lax",
            max_age=sessionExpirationHours * 3600,
            path="/",
        )
        return {
            "message": result.get("message"),
        }
    else:
        raise HTTPException(status_code=500, detail=error.loginFailed)
    

@router.post("/register")
async def register(user: models.userInput, request: Request, response: Response):
    auth = request.app.state.auth
    error = request.app.state.error
    secureCookie = request.app.state.secureCookie
    allowRegistration = request.app.state.allowRegistration
    
    #check if its first user
    isFirstUser = await auth.isFirstUser()
    
    #if its first user or registration is allowed -> continue
    if isFirstUser == True or allowRegistration == True:
        if isFirstUser:
            role = "admin"
        else:
            role = "user"
            
        isUsernameValid = await auth.validateUsername(user.username)
        if isUsernameValid.get("valid") == False:
            raise HTTPException(status_code=400, detail=error.usernameRequirementNotFulfilled)
            
        isPasswordValid = await auth.validatePassword(user.password)
        if isPasswordValid.get("valid") == False:
            raise HTTPException(status_code=400, detail=error.passwordRequirementNotFulfilled)
        
        result = await auth.register(user.username, user.password, role, isFirstUser)
        #if resgistration was successful -> set cookie and return message
        if result.get("message"):
            sessionToken = result.get("sessionToken")
            sessionExpirationHours = result.get("sessionExpirationHours")
            response.set_cookie(
                key="sessionToken",
                value=sessionToken,
                httponly=True,
                secure=secureCookie,
                samesite="lax",
                max_age=sessionExpirationHours * 3600,
                path="/",
            )
            return {
                "message": result.get("message"),
            }
        else:
            if(result.get("error") == "1"):
                raise HTTPException(status_code=409, detail=error.userAlreadyExists)
            else:
                raise HTTPException(status_code=500, detail=error.registrationFailed)
    else:
        raise HTTPException(status_code=403, detail=error.registrationDisabled)


@router.post("/logout")
async def logout(request: Request, response: Response):
    error = request.app.state.error
    auth = request.app.state.auth
    
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail=error.noActiveSession)   
    
    result = await auth.logout(currentSessionToken)
    response.delete_cookie("sessionToken", path="/")
    return {"message": result.get("message")}


@router.post("/logout/all")
async def logoutAll(request: Request, response: Response):
    auth = request.app.state.auth
    error = request.app.state.error
    
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail=error.noActiveSession)   
    
    isValid = await auth.verifySession(currentSessionToken)
    if isValid.get("valid")== True:
        username = isValid.get("username")
        result = await auth.logoutAllSessions(username)
        response.delete_cookie("sessionToken", path="/")
        return {"message": error.logoutAllSuccess}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)


@router.get("/verifySession")
async def verifySession(request: Request):
    error = request.app.state.error
    auth = request.app.state.auth
    
    currentSessionToken = request.cookies.get("sessionToken")
    if not currentSessionToken:
        raise HTTPException(status_code=401, detail=error.noActiveSession)
    
    isValid = await auth.verifySession(currentSessionToken)
    if isValid.get("valid")== True:
        return{"valid": True}
    else:
        raise HTTPException(status_code=401, detail=error.invalidSession)





