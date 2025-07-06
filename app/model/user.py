from pydantic import BaseModel,Field,EmailStr
from sqlmodel import SQLModel,Session,Field as sqlmodel_Field,select,update
from datetime import datetime,timezone
import os

class User(BaseModel):
    email: EmailStr = Field(description='Email')
    name: str = Field(description='Name')
    lastName: str = Field(description='Last Name')
    secondLastName: str | None = Field(default=None, description='Second Last Name')
class UserIn(User):
    password: str = Field( description='Password',min_length=8,max_length=20)

class UserOut(User):
    id: int

class UserDB(SQLModel,table=True):
    id: int | None = sqlmodel_Field(default=None, primary_key=True)
    email:str
    name: str
    lastName: str
    secondLastName: str | None
    hashed_password: str
    active: bool
    created_at: datetime = sqlmodel_Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = sqlmodel_Field(default_factory= lambda: datetime.now(timezone.utc))

class PasswordUpdate(BaseModel):
    password:str = Field(description='New Password',min_length=8,max_length=20)

class UserService:
    @staticmethod
    def save_user(user:UserDB,session:Session)->UserDB:
        #First check if the user exists in the database with the same email
       
            statement = select(UserDB).where(UserDB.email == user.email)
            user_exist = session.exec(statement).first()
            if not user_exist:    
                try:
                    user.name = user.name.lower()
                    user.lastName = user.lastName.lower()
                    user.secondLastName = user.secondLastName.lower()
                    session.add(user)
                    session.commit()
                    session.refresh(user)   
                    return user
                except Exception as e:
                    session.rollback()
                    print(f"Error saving user: {e}")
                    raise e
            else:
                raise ValueError(f"User with email {user.email} already exists.")    
  

    @staticmethod
    def get_user_by_email(email:str,session:Session)->UserDB | None:
        try:
            statement = select(UserDB).where(UserDB.email == email)
            user = session.exec(statement).first()
            if user:
                return user
            else: 
                return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            raise e
    @staticmethod
    def update_user(id:int, new_user_data: User, session: Session)-> UserDB | None:
        try:
            statement = select(UserDB).where(UserDB.id == id)
            user = session.exec(statement).first()
            if user:
                user.email = new_user_data.email
                user.name = new_user_data.name.lower()
                user.lastName = new_user_data.lastName.lower()
                user.secondLastName = new_user_data.secondLastName.lower()
                user.updated_at = datetime.now(timezone.utc)
                try:
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    return user
                except Exception as e:
                    session.rollback()
                    print(f"Error updating user in database: {e}")
                    raise e

        except Exception as e:
            print(f"Error updating user: {e}")
            raise e    
    @staticmethod
    def update_password(id:int, new_password, session: Session) -> UserDB | None:
        try:
            statement = select(UserDB).where(UserDB.id == id)
            user= session.exec(statement).first()
            if user: 
                user.hashed_password = new_password
                user.updated_at = datetime.now(timezone.utc)
                try:
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    return user
                except Exception as e:
                    session.rollback()
                    print(f"Error updating password in database: {e}")
                    raise e
        except Exception as e:
            print(f"Error selecting user: {e}")
            raise e
    @staticmethod
    def delete_user(id:int,session: Session) -> bool:
        try:
            statment = select(UserDB).where(UserDB.id == id)
            user = session.exec(statment).first()
            user.active = False
            user.updated_at = datetime.now(timezone.utc)
            try:
                session.add(user)
                session.commit()
                session.refresh(user)
                return True
            except Exception as e:
                session.rollback()
                print(f"Error deleting user in database: {e}")
                return False     
        except Exception as e:
            print(f"Error selecting user: {e}")
            raise e    