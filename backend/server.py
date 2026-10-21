from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import os, uuid, bcrypt, jwt, logging

mongo_url = os.environ["MONGO_URL"]
db = AsyncIOMotorClient(mongo_url)[os.environ["DB_NAME"]]
JWT_SECRET = os.environ["JWT_SECRET"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"].lower()
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
router = APIRouter(prefix="/api")
app = FastAPI(title="DockSync")

app.add_middleware(CORSMiddleware, allow_origins=[os.environ["FRONTEND_URL"]], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class LoginInput(BaseModel):
    email: str
    password: str

class AppointmentInput(BaseModel):
    carrier_name: str = Field(min_length=2)
    supplier_name: str = Field(min_length=2)
    invoice_number: str = Field(min_length=1)
    appointment_date: str
    appointment_time: str
    volume_count: int = Field(ge=1)
    dock_door: Optional[str] = "A-01"
    status: str = "Agendado"

def public_doc(doc):
    doc = dict(doc)
    doc.pop("_id", None)
    return doc

def token_for(user_id):
    return jwt.encode({"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}, JWT_SECRET, algorithm="HS256")

async def current_admin(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else None
    if not token:
        raise HTTPException(401, "Faça login para acessar esta área.")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await db.users.find_one({"id": payload["sub"], "role": "admin"}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(401, "Sessão inválida.")
        return user
    except jwt.PyJWTError:
        raise HTTPException(401, "Sessão expirada.")

async def seed_data():
    existing = await db.users.find_one({"email": ADMIN_EMAIL})
    hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
    if not existing:
        await db.users.insert_one({"id": str(uuid.uuid4()), "email": ADMIN_EMAIL, "name": "Administrador", "role": "admin", "password_hash": hashed})
    elif not bcrypt.checkpw(ADMIN_PASSWORD.encode(), existing["password_hash"].encode()):
        await db.users.update_one({"email": ADMIN_EMAIL}, {"$set": {"password_hash": hashed}})
    if await db.appointments.count_documents({}) == 0:
        today = datetime.now(timezone.utc).date()
        samples = [
            {"id": str(uuid.uuid4()), "carrier_name": "Rota Sul Express", "supplier_name": "Metalúrgica Horizonte", "invoice_number": "NF 004821", "appointment_date": today.isoformat(), "appointment_time": "08:30", "volume_count": 18, "dock_door": "A-01", "status": "Em chegada", "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "carrier_name": "Transvale Logística", "supplier_name": "Papelaria Norte", "invoice_number": "NF 004822", "appointment_date": today.isoformat(), "appointment_time": "10:00", "volume_count": 42, "dock_door": "B-02", "status": "Agendado", "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "carrier_name": "Cargas União", "supplier_name": "Alimentos Serra", "invoice_number": "NF 004901", "appointment_date": (today + timedelta(days=1)).isoformat(), "appointment_time": "14:30", "volume_count": 9, "dock_door": "A-03", "status": "Agendado", "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        await db.appointments.insert_many(samples)

@app.on_event("startup")
async def startup():
    await seed_data()

@router.get("/")
async def root(): return {"message": "DockSync API online"}

@router.post("/auth/login")
async def login(data: LoginInput, response: Response):
    user = await db.users.find_one({"email": data.email.lower()})
    if not user or not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()):
        raise HTTPException(401, "E-mail ou senha incorretos.")
    response.set_cookie("access_token", token_for(user["id"]), httponly=True, secure=True, samesite="none", max_age=28800)
    return {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}

@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}

@router.get("/auth/me")
async def me(user=Depends(current_admin)): return user

@router.get("/appointments")
async def list_appointments(start: Optional[str] = None, end: Optional[str] = None, carrier: Optional[str] = None, supplier: Optional[str] = None):
    query = {}
    if start or end:
        query["appointment_date"] = {}
        if start: query["appointment_date"]["$gte"] = start
        if end: query["appointment_date"]["$lte"] = end
    if carrier: query["carrier_name"] = {"$regex": carrier, "$options": "i"}
    if supplier: query["supplier_name"] = {"$regex": supplier, "$options": "i"}
    docs = await db.appointments.find(query, {"_id": 0}).sort([("appointment_date", 1), ("appointment_time", 1)]).to_list(500)
    return docs

@router.post("/appointments")
async def create_appointment(data: AppointmentInput, user=Depends(current_admin)):
    doc = data.model_dump(); doc.update({"id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat()})
    await db.appointments.insert_one(doc)
    return public_doc(doc)

@router.put("/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, data: AppointmentInput, user=Depends(current_admin)):
    updated = data.model_dump()
    result = await db.appointments.update_one({"id": appointment_id}, {"$set": updated})
    if not result.matched_count: raise HTTPException(404, "Agendamento não encontrado.")
    return {"id": appointment_id, **updated}

@router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, user=Depends(current_admin)):
    result = await db.appointments.delete_one({"id": appointment_id})
    if not result.deleted_count: raise HTTPException(404, "Agendamento não encontrado.")
    return {"ok": True}

app.include_router(router)
logging.basicConfig(level=logging.INFO)