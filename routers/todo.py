from fastapi import APIRouter, Depends, status, Path, HTTPException
from pydantic import BaseModel, Field
from models import Base, Todo
from database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter(
    prefix="/todo",#docsdaki görünüşü değiştirir
    tags=["Todo"]
)

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(default=0, gt=0, lt=6)
    complete: bool
    


def get_db():
    db = SessionLocal()
    try:
        yield db #return ile aynı ama birden fazla veri gelirse onları da döndürür
    finally:
        db.close()



db_dependency = Annotated[Session, Depends(get_db)] 


@router.get("/read_all")
async def read_all(db: db_dependency):
    db.query(Todo).all()


@router.get(path= "/get_by_id/{todo_id}", status_code=status.HTTP_200_OK)
async def read_by_id(db: db_dependency, todo_id: int = Path(gt= 0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Todo is not found")


@router.get(path="/create_todo", status_code= status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: TodoRequest):
    todo = Todo(**todo_request.dict())
    db.add(todo)
    db.commit()


@router.put(path="/update_todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="todo is not found")
    
    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.complete = todo_request.complete

    db.add(todo)
    db.commit()


@router.delete(path="/delete_todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="todo not found")

    db.delete(todo)
    db.commit()