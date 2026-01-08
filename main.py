from fastapi import FastAPI,Depends,HTTPException,status
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from datetime import datetime,timedelta,timezone
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
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
    username = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

class TaskCreate(BaseModel):
    description: str
    completed: int

app=FastAPI()

SECRET_KEY ="7b8f9e2c4d6a1b0c3e4f5a6b7c8d9e0f1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES =30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

fakeusers = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$NHCqprvysrc+xXJRuxM47w$HiO2KtW6rFzl9m6JdsJ5QnSKjNPs030nReiBtzXh1MM"
    },
    "Harish": {
        "username": "Harish",
        "full_name": "Harish",
        "email": "harish@example.com",
        "hashed_password":"$argon2id$v=19$m=65536,t=3,p=4$mxUBGYsmUqudnLKSID0GpQ$4BU3FgDNH9Lwt89HEP0WD5QfPDvBJhW7GaOmbEPt3yg"
    }
}

def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    user = fakeusers.get(username)
    return user
    
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

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fakeusers.get(form_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Wrong username")
    
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Wrong password")

    access_token = create_access_token(user["username"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@app.post("/add_task")
async def add_task(task: TaskCreate, db: Session = Depends(get_db),user: dict = Depends(get_current_user)):
    new_task = Task(
        description=task.description,
        completed=0,
        username=user["username"]
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.put("/update/{task_id}")
async def update(task_id:int, db: Session = Depends(get_db)):
    db.query(Task).filter(Task.id==task_id).update({"completed":1})
    db.commit()
    return {"message":"Task updated successfully"}

@app.put("/redotask/{task_id}")
async def redotask(task_id:int, db: Session = Depends(get_db)):
    db.query(Task).filter(Task.id==task_id).update({"completed":0})
    db.commit()
    return {"message":"Task updated successfully"}

@app.delete("/delete/{task_id}")
async def delete(task_id:int, db: Session = Depends(get_db)):
    db.query(Task).filter(Task.id==task_id).delete()
    db.commit()

@app.get("/tasks")
async def get_tasks(db: Session = Depends(get_db),user:dict=Depends(get_current_user)):
    return db.query(Task).filter(Task.username==user["username"]).all()

@app.get("/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
    }