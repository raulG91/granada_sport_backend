from fastapi import APIRouter,HTTPException,Depends,status,Body
from jwt.exceptions import InvalidTokenError
from ..model.user import UserIn,UserOut,UserDB, UserService, User, PasswordUpdate
from passlib.context import CryptContext
from datetime import datetime,timezone
from ..database import SessionDep
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from typing import Annotated
from ..model.token import Token
import jwt
import os
from datetime import datetime, timedelta,timezone

ALGORITHM = "HS256"
SECRET_KEY = "e277c8bd460bfeac66a0a0b888d0ee4858a93ab6e3978285a329f594a801d9d7"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # Hashing algorithm

#OAuth scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") #/token endpoint to get token

'''Functions for authentication'''
def hash_password(password:str) ->str:
    '''Hash a password using bcrypt algorithm.'''
    return pwd_context.hash(password)

def verify_pasword(plain_password:str,hashed_password:str) ->bool:
    '''Verify input password agains hashed password'''
    return pwd_context.verify(plain_password,hashed_password)


def authenticate_user(username:str, password:str,session) -> UserDB | None:
    user = UserService.get_user_by_email(username,session)
    if user and user.active:
        if verify_pasword(password,user.hashed_password):
            return user
        else:
            return None
    else:
        '''User was not found in the database'''
        return None
def create_access_token(username:str) -> str:
    data_dic = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(data_dic,SECRET_KEY,algorithm=ALGORITHM)
    return token 

def get_current_user(token:Annotated[str,Depends(oauth2_scheme)],session:SessionDep) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        username = payload.get("sub",None)
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = UserService.get_user_by_email(username,session)

    if user:
        return user
    else:
        raise credentials_exception

async def get_current_active_user(current_user: Annotated[UserDB, Depends(get_current_user)])->UserOut:
    if current_user.active:
        return UserOut(**current_user.model_dump())
    else:
        raise HTTPException(status_code=400, detail="Inactive user")


user_router = APIRouter(tags=["User"])
@user_router.post("/user",response_model=UserOut, description="Create a new user", status_code=status.HTTP_201_CREATED)
async def create_user(user:UserIn,session:SessionDep):
    '''Create a new user in the database'''
    hashed_passsword = hash_password(user.password)
    date_now = datetime.now(timezone.utc)
    userDB = UserDB(name=user.name,lastName=user.lastName,email=user.email,secondLastName=user.secondLastName,hashed_password=hashed_passsword,active=True,created_at=date_now,updated_at=date_now)
    try:
        UserService.save_user(userDB,session)
        return userDB
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        return HTTPException(status_code=500, detail="Error creating user")

@user_router.get("/user/me", response_model=UserOut,description='Get current user information')
async def get_me(current_user: Annotated[UserOut, Depends(get_current_active_user)]):
    return current_user

@user_router.put("/user/me", response_model=UserOut,description='Update current user information')
async def update_user_profile(new_user_data: Annotated[User, Body()],current_user : Annotated[UserOut, Depends(get_current_active_user)],session:SessionDep):
    '''Update current user profile'''
    try: 
        #Update user data
        updated_user = UserService.update_user(current_user.id,new_user_data,session)
        return UserOut(**updated_user.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating user")    
    
@user_router.put("/user/me/password", response_model=UserOut,description='Update current user password')
async def update_password(data: Annotated[PasswordUpdate, Body()],current_user : Annotated[UserOut, Depends(get_current_active_user)],session:SessionDep):
    '''Update current user password'''
    try:
        hashed_password = hash_password(data.password)
        #Update user password
        updated_user = UserService.update_password(current_user.id,hashed_password,session)
        return UserOut(**updated_user.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating password")


@user_router.delete("/user/me")
def delete_user(current_user: Annotated[UserOut, Depends(get_current_active_user)],session:SessionDep)->dict:
    '''Delete current user'''
    try:
        result  = UserService.delete_user(current_user.id,session)
        return {"message": "User delted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting user")

@user_router.post("/token",response_model=Token)
async def login_user(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],session:SessionDep):
    #First check the user exist in the dabasa and the password is correct
    user = authenticate_user(form_data.username, form_data.password,session)
    if user:
        #Generate access token
        access_token = create_access_token(user.email)
        return Token(access_token=access_token,token_type='bearer')   
    else:
        #User doesn't exist or password is incorrect
        raise HTTPException(status_code=401, detail="Incorrect user or password")