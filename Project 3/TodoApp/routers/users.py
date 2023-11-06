from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from models import Users
from database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext


router = APIRouter()
router = APIRouter(
    prefix='/user',
    tags=['user']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)
    verify_password: str

@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code= 401, detail='Authentication Failed')
    return db.query(Users).filter(Users.id == user.get('id')).first()

@router.put("/password", status_code=status.HTTP_200_OK)
async def change_password(user: user_dependency, db: db_dependency, change_password_request: ChangePasswordRequest):
    if user is None:
        raise HTTPException(status_code= 401, detail='Authentication Failed')
    if change_password_request.current_password == change_password_request.new_password:
        raise HTTPException(status_code=401, detail='The same password')
    if change_password_request.new_password != change_password_request.verify_password:
        raise HTTPException(status_code=401, detail='Wrong verified password')
    user = db.query(Users).filter(Users.id == user.get('id')).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt_context.verify(change_password_request.current_password, user.hashed_password):
        raise HTTPException(status_code=404, detail="Password is incorrect")
    
    user.hashed_password = bcrypt_context.hash(change_password_request.new_password)
    db.add(user)
    db.commit()


    