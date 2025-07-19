from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import os
import uuid
import bcrypt
import jwt
from pathlib import Path
from dotenv import load_dotenv
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = "orçazen_financeiro_secret_key_2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days

app = FastAPI(title="OrçaZenFinanceiro API", version="1.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AccountCreate(BaseModel):
    name: str
    type: str
    institution: Optional[str] = None
    initial_balance: float
    color_hex: str = "#4F46E5"

class Account(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    type: str
    institution: Optional[str] = None
    initial_balance: float
    current_balance: float
    color_hex: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CategoryCreate(BaseModel):
    name: str
    type: str  # "Receita" or "Despesa"
    parent_category_id: Optional[str] = None

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # None for system categories
    name: str
    type: str
    parent_category_id: Optional[str] = None
    is_custom: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TransactionCreate(BaseModel):
    description: str
    value: float
    type: str  # "Receita" or "Despesa"
    transaction_date: datetime
    account_id: str
    category_id: Optional[str] = None
    observation: Optional[str] = None

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    description: str
    value: float
    type: str
    transaction_date: datetime
    account_id: str
    category_id: Optional[str] = None
    observation: Optional[str] = None
    status: str = "Pago"
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Utility functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    return User(**user)

# Auth endpoints
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Hash password
    password_bytes = user_data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Create user
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash
    )
    
    await db.users.insert_one(user.dict())
    
    # Create default categories for user
    await create_default_categories(user.id)
    
    # Create access token
    token = create_access_token({"sub": user.id})
    
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "name": user.name, "email": user.email}}

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Verify password
    password_bytes = user_data.password.encode('utf-8')
    stored_hash = user['password_hash'].encode('utf-8')
    
    if not bcrypt.checkpw(password_bytes, stored_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Create access token
    token = create_access_token({"sub": user['id']})
    
    return {"access_token": token, "token_type": "bearer", "user": {"id": user['id'], "name": user['name'], "email": user['email']}}

# Account endpoints
@api_router.post("/accounts", response_model=Account)
async def create_account(account_data: AccountCreate, current_user: User = Depends(get_current_user)):
    account = Account(
        user_id=current_user.id,
        name=account_data.name,
        type=account_data.type,
        institution=account_data.institution,
        initial_balance=account_data.initial_balance,
        current_balance=account_data.initial_balance,
        color_hex=account_data.color_hex
    )
    
    await db.accounts.insert_one(account.dict())
    return account

@api_router.get("/accounts", response_model=List[Account])
async def get_accounts(current_user: User = Depends(get_current_user)):
    accounts = await db.accounts.find({"user_id": current_user.id, "is_active": True}).to_list(1000)
    return [Account(**account) for account in accounts]

# Transaction endpoints
@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction_data: TransactionCreate, current_user: User = Depends(get_current_user)):
    transaction = Transaction(
        user_id=current_user.id,
        description=transaction_data.description,
        value=transaction_data.value,
        type=transaction_data.type,
        transaction_date=transaction_data.transaction_date,
        account_id=transaction_data.account_id,
        category_id=transaction_data.category_id,
        observation=transaction_data.observation
    )
    
    await db.transactions.insert_one(transaction.dict())
    
    # Update account balance
    balance_change = transaction_data.value if transaction_data.type == "Receita" else -transaction_data.value
    await db.accounts.update_one(
        {"id": transaction_data.account_id},
        {"$inc": {"current_balance": balance_change}}
    )
    
    return transaction

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(current_user: User = Depends(get_current_user)):
    transactions = await db.transactions.find({"user_id": current_user.id}).sort("transaction_date", -1).to_list(1000)
    return [Transaction(**transaction) for transaction in transactions]

# Category endpoints
@api_router.get("/categories", response_model=List[Category])
async def get_categories(current_user: User = Depends(get_current_user)):
    # Get both system and user categories
    categories = await db.categories.find({
        "$or": [
            {"user_id": current_user.id},
            {"user_id": None}
        ]
    }).to_list(1000)
    return [Category(**category) for category in categories]

# Dashboard endpoints
@api_router.get("/dashboard/summary")
async def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    # Get total balance from all accounts
    accounts = await db.accounts.find({"user_id": current_user.id, "is_active": True}).to_list(1000)
    total_balance = sum(account['current_balance'] for account in accounts)
    
    # Get current month transactions
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    transactions = await db.transactions.find({
        "user_id": current_user.id,
        "transaction_date": {"$gte": start_of_month}
    }).to_list(1000)
    
    total_income = sum(t['value'] for t in transactions if t['type'] == "Receita")
    total_expenses = sum(t['value'] for t in transactions if t['type'] == "Despesa")
    
    return {
        "total_balance": total_balance,
        "monthly_income": total_income,
        "monthly_expenses": total_expenses,
        "monthly_net": total_income - total_expenses,
        "accounts": [{"id": acc['id'], "name": acc['name'], "balance": acc['current_balance'], "color": acc['color_hex']} for acc in accounts]
    }

# Create default categories
async def create_default_categories(user_id: str):
    default_categories = [
        # Receitas
        {"name": "Salário", "type": "Receita"},
        {"name": "Freelance", "type": "Receita"},
        {"name": "Investimentos", "type": "Receita"},
        {"name": "Outras Receitas", "type": "Receita"},
        
        # Despesas
        {"name": "Alimentação", "type": "Despesa"},
        {"name": "Transporte", "type": "Despesa"},
        {"name": "Moradia", "type": "Despesa"},
        {"name": "Saúde", "type": "Despesa"},
        {"name": "Educação", "type": "Despesa"},
        {"name": "Lazer", "type": "Despesa"},
        {"name": "Compras", "type": "Despesa"},
        {"name": "Outras Despesas", "type": "Despesa"}
    ]
    
    categories_to_insert = []
    for cat_data in default_categories:
        category = Category(
            user_id=user_id,
            name=cat_data["name"],
            type=cat_data["type"],
            is_custom=False
        )
        categories_to_insert.append(category.dict())
    
    await db.categories.insert_many(categories_to_insert)

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()