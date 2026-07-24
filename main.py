from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import UserModel
from database import get_session
from fastapi import FastAPI, Depends, HTTPException, status
from schemas.users import UserCreateSchema, UserResponseSchema
from security import hash_password
import uvicorn

app = FastAPI()

@app.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreateSchema, db: AsyncSession = Depends(get_session)):
    """
        Registration Endpoint

        Args:
            payload (UserCreateSchema): Example from Pydantic Schema
            db (AsyncSession): Database session
    """
    query = select(UserModel).where(
        (UserModel.username == payload.username) | (UserModel.phone == payload.phone)
    )
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "user exists"
        )
    
    hashed_pwd = hash_password(payload.password)
    new_user = UserModel(
        first_name = payload.first_name,
        last_name = payload.last_name,
        username = payload.username,
        hashed_password = hashed_pwd,
        phone = payload.phone,
        email = payload.email,
        country = payload.country        
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.get("/users", response_model=list[UserResponseSchema])
async def get_users(db: AsyncSession = Depends(get_session),  
                    username: Optional[str | None] = None):
    query = select(UserModel)
    if username:
        query = query.where(UserModel.username == username)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/users/{user_id}")
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_session)):
    query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user



#########################################
##############| RUNNER |#################
#########################################
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)