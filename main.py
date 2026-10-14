from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from starlette.middleware.sessions import SessionMiddleware

import models
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Diaryme")
app.mount("/static", StaticFiles(directory="static"), name="static")
# เพิ่ม Session Middleware สำหรับจัดการการล็อกอิน
app.add_middleware(SessionMiddleware, secret_key="diaryme-super-secret-key-change-this")

templates = Jinja2Templates(directory="templates")


# --- Helper: ดึง User ปัจจุบันจาก Session ---
def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()


# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="index.html", context={"user": user})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="register.html")


# --- Auth API Actions ---

@app.post("/api/register")
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()
    if existing_user:
        return templates.TemplateResponse(
            request=request, 
            name="register.html", 
            context={"error": "Username หรือ Email นี้ถูกใช้งานแล้ว"}
        )
    
    new_user = models.User(username=username, email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/api/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or user.password != password:
        return templates.TemplateResponse(
            request=request, 
            name="login.html", 
            context={"error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}
        )
    
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


# --- Diary API Endpoints ---

class EntrySchema(BaseModel):
    title: str
    content: str
    mood: str = "Neutral"

@app.get("/entries/")
def get_user_entries(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    entries = db.query(models.DiaryEntry).filter(models.DiaryEntry.user_id == user.id).all()
    return entries

@app.post("/entries/")
def create_entry(data: EntrySchema, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    entry = models.DiaryEntry(
        title=data.title,
        content=data.content,
        mood=data.mood,
        user_id=user.id
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "success", "id": entry.id}

# API แก้ไขไดอารี่ (PUT)
@app.put("/entries/{entry_id}")
def update_entry(entry_id: int, data: EntrySchema, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    entry = db.query(models.DiaryEntry).filter(
        models.DiaryEntry.id == entry_id, 
        models.DiaryEntry.user_id == user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    
    entry.title = data.title
    entry.content = data.content
    entry.mood = data.mood
    db.commit()
    return {"status": "updated"}

# API ลบไดอารี่ (DELETE)
@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    entry = db.query(models.DiaryEntry).filter(
        models.DiaryEntry.id == entry_id, 
        models.DiaryEntry.user_id == user.id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    
    db.delete(entry)
    db.commit()
    return {"status": "deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)