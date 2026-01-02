from fastapi import FastAPI,Depends
from sqlalchemy import create_engine,Column,Integer,String
from sqlalchemy.orm import sessionmaker, declarative_base,Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
DATABASE_URL="sqlite:///./todo.db"
engine=create_engine(DATABASE_URL)
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base=declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    completed = Column(Integer, default=0)
    
class TaskCreate(BaseModel):
    description: str
    completed: int
    
Base.metadata.create_all(bind=engine)

app=FastAPI()

orgins=[
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=orgins,
    allow_credentials=True,
    allow_methods=["*"],    
    allow_headers=["*"],
)

async def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/add_task")
def add_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(
        description=task.description,
        completed=task.completed
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.put("/update/{task_id}")
def update(task_id:int, db: Session = Depends(get_db)):
    db.query(Task).filter(Task.id==task_id).update({"completed":1})
    db.commit()
    return {"message":"Task updated successfully"}

@app.put("/redotask/{task_id}")
def redotask(task_id:int, db: Session = Depends(get_db)):
    db.query(Task).filter(Task.id==task_id).update({"completed":0})
    db.commit()
    return {"message":"Task updated successfully"}

@app.delete("/delete/{task_id}")
async def delete(task_id:int, db: Session = Depends(get_db)):
    db.query(Task).filter(Task.id==task_id).delete()
    db.commit()

@app.get("/tasks")
async def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()