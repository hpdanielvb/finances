from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import uuid
import bcrypt
import jwt
import base64
import io
from pathlib import Path
from dotenv import load_dotenv
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration - More secure
SECRET_KEY = "orçazen_financeiro_secret_key_2025_ultra_secure_brasil"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30  # 30 days for better persistence

# Email Configuration (para MVP - usar simulado)
EMAIL_FROM = "noreply@orcazenfinanceiro.com.br"
SMTP_SERVER = "smtp.gmail.com"  # Simulado para MVP
SMTP_PORT = 587
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'demo@orcazen.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'demo_password')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://orcazenfinanceiro.com.br')

app = FastAPI(title="OrçaZenFinanceiro API", version="2.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Enhanced Models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class EmailConfirmation(BaseModel):
    token: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    password_hash: str
    email_verified: bool = False
    email_verification_token: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AccountCreate(BaseModel):
    name: str
    type: str
    institution: Optional[str] = None
    initial_balance: float
    credit_limit: Optional[float] = None
    invoice_due_date: Optional[str] = None
    color_hex: str = "#4F46E5"

class Account(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    type: str
    institution: Optional[str] = None
    initial_balance: float
    current_balance: float
    credit_limit: Optional[float] = None
    invoice_due_date: Optional[str] = None
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
    type: str  # "Receita", "Despesa", or "Transferência"
    transaction_date: datetime
    account_id: str
    category_id: Optional[str] = None
    observation: Optional[str] = None
    is_recurring: bool = False
    recurrence_interval: Optional[str] = None  # "Diária", "Semanal", "Mensal", etc.
    recurrence_start_date: Optional[datetime] = None
    recurrence_end_date: Optional[datetime] = None
    status: str = "Pago"

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
    is_recurring: bool = False
    recurrence_interval: Optional[str] = None
    recurrence_start_date: Optional[datetime] = None
    recurrence_end_date: Optional[datetime] = None
    status: str = "Pago"
    proof_url: Optional[str] = None
    related_transaction_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TransferCreate(BaseModel):
    from_account_id: str
    to_account_id: str
    value: float
    description: str
    transaction_date: datetime

class GoalCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_amount: float
    current_amount: float = 0
    target_date: datetime
    category: str  # "Emergência", "Casa Própria", "Viagem", "Aposentadoria", "Outros"
    priority: str = "Média"  # "Alta", "Média", "Baixa"
    auto_contribution: Optional[float] = None  # Valor mensal automático

class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    target_amount: float
    current_amount: float = 0
    target_date: datetime
    category: str
    priority: str
    auto_contribution: Optional[float] = None
    is_active: bool = True
    is_achieved: bool = False
    achieved_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GoalContribution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    goal_id: str
    amount: float
    contribution_date: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    transaction_id: Optional[str] = None  # Link to transaction if applicable

class BudgetCreate(BaseModel):
    category_id: str
    budget_amount: float
    month_year: str  # "YYYY-MM"

class Budget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    category_id: str
    budget_amount: float
    month_year: str
    spent_amount: float = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced utility functions with better session management
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        print(f"Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user_id = verify_token(credentials.credentials)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        return User(**user)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Erro de autenticação")

# Enhanced Auth endpoints
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Validate password confirmation
    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=400, detail="Senhas não coincidem")
    
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
        password_hash=password_hash,
        email_verified=True  # Auto-verify for now
    )
    
    await db.users.insert_one(user.dict())
    
    # Create default categories for user
    await create_default_categories(user.id)
    
    # Create access token with longer expiry
    token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
    
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "expires_in": ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600,
        "user": {"id": user.id, "name": user.name, "email": user.email}
    }

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
    
    # Create access token with longer expiry
    token = create_access_token({"sub": user['id'], "email": user['email'], "name": user['name']})
    
    return {
        "access_token": token, 
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600, 
        "user": {"id": user['id'], "name": user['name'], "email": user['email']}
    }

@api_router.post("/auth/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh token endpoint for better session management"""
    token = create_access_token({"sub": current_user.id, "email": current_user.email, "name": current_user.name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600
    }

# Enhanced Account endpoints
@api_router.post("/accounts", response_model=Account)
async def create_account(account_data: AccountCreate, current_user: User = Depends(get_current_user)):
    account = Account(
        user_id=current_user.id,
        name=account_data.name,
        type=account_data.type,
        institution=account_data.institution,
        initial_balance=account_data.initial_balance,
        current_balance=account_data.initial_balance,
        credit_limit=account_data.credit_limit,
        invoice_due_date=account_data.invoice_due_date,
        color_hex=account_data.color_hex
    )
    
    await db.accounts.insert_one(account.dict())
    return account

@api_router.get("/accounts", response_model=List[Account])
async def get_accounts(current_user: User = Depends(get_current_user)):
    accounts = await db.accounts.find({"user_id": current_user.id, "is_active": True}).to_list(1000)
    return [Account(**account) for account in accounts]

@api_router.put("/accounts/{account_id}", response_model=Account)
async def update_account(account_id: str, account_data: AccountCreate, current_user: User = Depends(get_current_user)):
    # Check if account belongs to user
    account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    # Update account
    update_data = account_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.accounts.update_one({"id": account_id}, {"$set": update_data})
    
    # Return updated account
    updated_account = await db.accounts.find_one({"id": account_id})
    return Account(**updated_account)

@api_router.delete("/accounts/{account_id}")
async def delete_account(account_id: str, current_user: User = Depends(get_current_user)):
    # Check if account has transactions
    transaction_count = await db.transactions.count_documents({"account_id": account_id})
    if transaction_count > 0:
        raise HTTPException(status_code=400, detail="Não é possível excluir conta com transações")
    
    # Delete account
    result = await db.accounts.delete_one({"id": account_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    return {"message": "Conta excluída com sucesso"}

# Enhanced Transaction endpoints
@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction_data: TransactionCreate, current_user: User = Depends(get_current_user)):
    # Verify account belongs to user
    account = await db.accounts.find_one({"id": transaction_data.account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    transaction = Transaction(
        user_id=current_user.id,
        description=transaction_data.description,
        value=transaction_data.value,
        type=transaction_data.type,
        transaction_date=transaction_data.transaction_date,
        account_id=transaction_data.account_id,
        category_id=transaction_data.category_id,
        observation=transaction_data.observation,
        is_recurring=transaction_data.is_recurring,
        recurrence_interval=transaction_data.recurrence_interval,
        recurrence_start_date=transaction_data.recurrence_start_date,
        recurrence_end_date=transaction_data.recurrence_end_date,
        status=transaction_data.status
    )
    
    await db.transactions.insert_one(transaction.dict())
    
    # Update account balance
    balance_change = transaction_data.value if transaction_data.type == "Receita" else -transaction_data.value
    await db.accounts.update_one(
        {"id": transaction_data.account_id},
        {"$inc": {"current_balance": balance_change}}
    )
    
    # Update budget if category is provided
    if transaction_data.category_id and transaction_data.type == "Despesa":
        current_month = transaction_data.transaction_date.strftime("%Y-%m")
        await update_budget_spent(current_user.id, transaction_data.category_id, current_month, transaction_data.value)
    
    return transaction

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    type_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Build query
    query = {"user_id": current_user.id}
    if account_id:
        query["account_id"] = account_id
    if category_id:
        query["category_id"] = category_id
    if type_filter:
        query["type"] = type_filter
    
    transactions = await db.transactions.find(query).sort("transaction_date", -1).skip(offset).limit(limit).to_list(limit)
    return [Transaction(**transaction) for transaction in transactions]

@api_router.put("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(transaction_id: str, transaction_data: TransactionCreate, current_user: User = Depends(get_current_user)):
    # Check if transaction belongs to user
    old_transaction = await db.transactions.find_one({"id": transaction_id, "user_id": current_user.id})
    if not old_transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Revert old balance change
    old_balance_change = old_transaction['value'] if old_transaction['type'] == "Receita" else -old_transaction['value']
    await db.accounts.update_one(
        {"id": old_transaction['account_id']},
        {"$inc": {"current_balance": -old_balance_change}}
    )
    
    # Update transaction
    update_data = transaction_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.transactions.update_one({"id": transaction_id}, {"$set": update_data})
    
    # Apply new balance change
    new_balance_change = transaction_data.value if transaction_data.type == "Receita" else -transaction_data.value
    await db.accounts.update_one(
        {"id": transaction_data.account_id},
        {"$inc": {"current_balance": new_balance_change}}
    )
    
    # Return updated transaction
    updated_transaction = await db.transactions.find_one({"id": transaction_id})
    return Transaction(**updated_transaction)

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, current_user: User = Depends(get_current_user)):
    # Check if transaction belongs to user
    transaction = await db.transactions.find_one({"id": transaction_id, "user_id": current_user.id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Revert balance change
    balance_change = transaction['value'] if transaction['type'] == "Receita" else -transaction['value']
    await db.accounts.update_one(
        {"id": transaction['account_id']},
        {"$inc": {"current_balance": -balance_change}}
    )
    
    # Delete transaction
    await db.transactions.delete_one({"id": transaction_id})
    
    return {"message": "Transação excluída com sucesso"}

# Transfer endpoint
@api_router.post("/transfers")
async def create_transfer(transfer_data: TransferCreate, current_user: User = Depends(get_current_user)):
    # Verify both accounts belong to user
    from_account = await db.accounts.find_one({"id": transfer_data.from_account_id, "user_id": current_user.id})
    to_account = await db.accounts.find_one({"id": transfer_data.to_account_id, "user_id": current_user.id})
    
    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail="Uma das contas não foi encontrada")
    
    # Check if from_account has sufficient balance
    if from_account['current_balance'] < transfer_data.value:
        raise HTTPException(status_code=400, detail="Saldo insuficiente na conta de origem")
    
    # Create withdrawal transaction
    withdrawal_transaction = Transaction(
        user_id=current_user.id,
        description=f"Transferência para {to_account['name']}: {transfer_data.description}",
        value=transfer_data.value,
        type="Despesa",
        transaction_date=transfer_data.transaction_date,
        account_id=transfer_data.from_account_id,
        observation=f"Transferência para {to_account['name']}"
    )
    
    # Create deposit transaction
    deposit_transaction = Transaction(
        user_id=current_user.id,
        description=f"Transferência de {from_account['name']}: {transfer_data.description}",
        value=transfer_data.value,
        type="Receita",
        transaction_date=transfer_data.transaction_date,
        account_id=transfer_data.to_account_id,
        observation=f"Transferência de {from_account['name']}"
    )
    
    # Link transactions
    withdrawal_transaction.related_transaction_id = deposit_transaction.id
    deposit_transaction.related_transaction_id = withdrawal_transaction.id
    
    # Insert both transactions
    await db.transactions.insert_many([withdrawal_transaction.dict(), deposit_transaction.dict()])
    
    # Update account balances
    await db.accounts.update_one({"id": transfer_data.from_account_id}, {"$inc": {"current_balance": -transfer_data.value}})
    await db.accounts.update_one({"id": transfer_data.to_account_id}, {"$inc": {"current_balance": transfer_data.value}})
    
    return {"message": "Transferência realizada com sucesso"}

# Category endpoints
@api_router.get("/categories", response_model=List[Category])
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await db.categories.find({
        "$or": [
            {"user_id": current_user.id},
            {"user_id": None}
        ]
    }).to_list(1000)
    return [Category(**category) for category in categories]

@api_router.post("/categories", response_model=Category)
async def create_category(category_data: CategoryCreate, current_user: User = Depends(get_current_user)):
    category = Category(
        user_id=current_user.id,
        name=category_data.name,
        type=category_data.type,
        parent_category_id=category_data.parent_category_id,
        is_custom=True
    )
    
    await db.categories.insert_one(category.dict())
    return category

# Budget endpoints
@api_router.post("/budgets", response_model=Budget)
async def create_budget(budget_data: BudgetCreate, current_user: User = Depends(get_current_user)):
    # Check if budget already exists for category and month
    existing_budget = await db.budgets.find_one({
        "user_id": current_user.id,
        "category_id": budget_data.category_id,
        "month_year": budget_data.month_year
    })
    
    if existing_budget:
        # Update existing budget
        await db.budgets.update_one(
            {"id": existing_budget['id']},
            {"$set": {"budget_amount": budget_data.budget_amount}}
        )
        updated_budget = await db.budgets.find_one({"id": existing_budget['id']})
        return Budget(**updated_budget)
    else:
        # Create new budget
        budget = Budget(
            user_id=current_user.id,
            category_id=budget_data.category_id,
            budget_amount=budget_data.budget_amount,
            month_year=budget_data.month_year
        )
        
        await db.budgets.insert_one(budget.dict())
        return budget

@api_router.get("/budgets", response_model=List[Budget])
async def get_budgets(month_year: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"user_id": current_user.id}
    if month_year:
        query["month_year"] = month_year
    
    budgets = await db.budgets.find(query).to_list(1000)
    return [Budget(**budget) for budget in budgets]

@api_router.delete("/budgets/{budget_id}")
async def delete_budget(budget_id: str, current_user: User = Depends(get_current_user)):
    # Check if budget belongs to user
    budget = await db.budgets.find_one({"id": budget_id, "user_id": current_user.id})
    if not budget:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    # Delete budget
    result = await db.budgets.delete_one({"id": budget_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    return {"message": "Orçamento excluído com sucesso"}

@api_router.put("/budgets/{budget_id}", response_model=Budget)
async def update_budget(budget_id: str, budget_data: BudgetCreate, current_user: User = Depends(get_current_user)):
    # Check if budget belongs to user
    budget = await db.budgets.find_one({"id": budget_id, "user_id": current_user.id})
    if not budget:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    # Update budget
    update_data = budget_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.budgets.update_one({"id": budget_id}, {"$set": update_data})
    
    # Return updated budget
    updated_budget = await db.budgets.find_one({"id": budget_id})
    return Budget(**updated_budget)

# Goals endpoints
@api_router.post("/goals", response_model=Goal)
async def create_goal(goal_data: GoalCreate, current_user: User = Depends(get_current_user)):
    goal = Goal(
        user_id=current_user.id,
        name=goal_data.name,
        description=goal_data.description,
        target_amount=goal_data.target_amount,
        current_amount=goal_data.current_amount,
        target_date=goal_data.target_date,
        category=goal_data.category,
        priority=goal_data.priority,
        auto_contribution=goal_data.auto_contribution
    )
    
    await db.goals.insert_one(goal.dict())
    return goal

@api_router.get("/goals", response_model=List[Goal])
async def get_goals(current_user: User = Depends(get_current_user)):
    goals = await db.goals.find({"user_id": current_user.id, "is_active": True}).to_list(1000)
    return [Goal(**goal) for goal in goals]

@api_router.put("/goals/{goal_id}", response_model=Goal)
async def update_goal(goal_id: str, goal_data: GoalCreate, current_user: User = Depends(get_current_user)):
    # Check if goal belongs to user
    goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    
    # Update goal
    update_data = goal_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.goals.update_one({"id": goal_id}, {"$set": update_data})
    
    # Return updated goal
    updated_goal = await db.goals.find_one({"id": goal_id})
    return Goal(**updated_goal)

@api_router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str, current_user: User = Depends(get_current_user)):
    # Check if goal belongs to user
    goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    
    # Delete goal (soft delete)
    await db.goals.update_one({"id": goal_id}, {"$set": {"is_active": False}})
    
    return {"message": "Meta excluída com sucesso"}

@api_router.post("/goals/{goal_id}/contribute")
async def contribute_to_goal(goal_id: str, amount: float, current_user: User = Depends(get_current_user)):
    # Check if goal belongs to user and is active
    goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id, "is_active": True})
    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    
    # Create contribution record
    contribution = GoalContribution(
        user_id=current_user.id,
        goal_id=goal_id,
        amount=amount,
        description=f"Contribuição para {goal['name']}"
    )
    
    await db.goal_contributions.insert_one(contribution.dict())
    
    # Update goal current amount
    new_amount = goal['current_amount'] + amount
    
    # Check if goal is achieved
    is_achieved = new_amount >= goal['target_amount']
    update_data = {
        "current_amount": new_amount,
        "updated_at": datetime.utcnow()
    }
    
    if is_achieved and not goal.get('is_achieved'):
        update_data["is_achieved"] = True
        update_data["achieved_date"] = datetime.utcnow()
    
    await db.goals.update_one({"id": goal_id}, {"$set": update_data})
    
    return {"message": "Contribuição adicionada com sucesso", "goal_achieved": is_achieved}

@api_router.get("/goals/{goal_id}/contributions")
async def get_goal_contributions(goal_id: str, current_user: User = Depends(get_current_user)):
    # Check if goal belongs to user
    goal = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    
    contributions = await db.goal_contributions.find({"goal_id": goal_id}).sort("contribution_date", -1).to_list(1000)
    return contributions

@api_router.get("/goals/statistics")
async def get_goals_statistics(current_user: User = Depends(get_current_user)):
    goals = await db.goals.find({"user_id": current_user.id, "is_active": True}).to_list(1000)
    
    total_goals = len(goals)
    achieved_goals = len([g for g in goals if g.get('is_achieved')])
    active_goals = total_goals - achieved_goals
    
    total_target = sum(g['target_amount'] for g in goals)
    total_saved = sum(g['current_amount'] for g in goals)
    
    # Calculate progress by category
    category_stats = {}
    for goal in goals:
        category = goal['category']
        if category not in category_stats:
            category_stats[category] = {
                'count': 0,
                'target': 0,
                'saved': 0,
                'progress': 0
            }
        
        category_stats[category]['count'] += 1
        category_stats[category]['target'] += goal['target_amount']
        category_stats[category]['saved'] += goal['current_amount']
    
    # Calculate progress percentage for each category
    for category in category_stats:
        if category_stats[category]['target'] > 0:
            category_stats[category]['progress'] = (
                category_stats[category]['saved'] / category_stats[category]['target'] * 100
            )
    
    return {
        "total_goals": total_goals,
        "achieved_goals": achieved_goals,
        "active_goals": active_goals,
        "total_target_amount": total_target,
        "total_saved_amount": total_saved,
        "overall_progress": (total_saved / total_target * 100) if total_target > 0 else 0,
        "category_statistics": category_stats
    }

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    # Read file content
    file_content = await file.read()
    
    # Convert to base64 for storage (simple approach)
    file_base64 = base64.b64encode(file_content).decode('utf-8')
    file_url = f"data:{file.content_type};base64,{file_base64}"
    
    return {"file_url": file_url, "filename": file.filename}

# Enhanced Dashboard endpoint
@api_router.get("/dashboard/summary")
async def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    # Get all accounts
    accounts = await db.accounts.find({"user_id": current_user.id, "is_active": True}).to_list(1000)
    total_balance = sum(account['current_balance'] for account in accounts)
    
    # Get current month transactions
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_month = (start_of_month.replace(month=start_of_month.month + 1) - timedelta(days=1)) if start_of_month.month < 12 else start_of_month.replace(year=start_of_month.year + 1, month=1) - timedelta(days=1)
    
    transactions = await db.transactions.find({
        "user_id": current_user.id,
        "transaction_date": {"$gte": start_of_month, "$lte": end_of_month}
    }).to_list(1000)
    
    total_income = sum(t['value'] for t in transactions if t['type'] == "Receita")
    total_expenses = sum(t['value'] for t in transactions if t['type'] == "Despesa")
    
    # Get categories for expense breakdown
    categories = await db.categories.find({
        "$or": [{"user_id": current_user.id}, {"user_id": None}]
    }).to_list(1000)
    
    # Group expenses by category
    expense_by_category = {}
    income_by_category = {}
    
    for transaction in transactions:
        if transaction.get('category_id'):
            category = next((c for c in categories if c['id'] == transaction['category_id']), None)
            if category:
                category_name = category['name']
                if transaction['type'] == "Despesa":
                    expense_by_category[category_name] = expense_by_category.get(category_name, 0) + transaction['value']
                elif transaction['type'] == "Receita":
                    income_by_category[category_name] = income_by_category.get(category_name, 0) + transaction['value']
    
    # Get pending transactions (next 15 days)
    next_15_days = now + timedelta(days=15)
    pending_transactions = await db.transactions.find({
        "user_id": current_user.id,
        "status": "Pendente",
        "transaction_date": {"$gte": now, "$lte": next_15_days}
    }).to_list(100)
    
    return {
        "total_balance": total_balance,
        "monthly_income": total_income,
        "monthly_expenses": total_expenses,
        "monthly_net": total_income - total_expenses,
        "accounts": [{"id": acc['id'], "name": acc['name'], "balance": acc['current_balance'], "color": acc['color_hex'], "type": acc['type']} for acc in accounts],
        "expense_by_category": expense_by_category,
        "income_by_category": income_by_category,
        "pending_transactions": [{"id": t['id'], "description": t['description'], "value": t['value'], "type": t['type'], "transaction_date": t['transaction_date'], "account_id": t['account_id']} for t in pending_transactions]
    }

# Reports endpoints
@api_router.get("/reports/cash-flow")
async def get_cash_flow_report(
    start_date: str,
    end_date: str,
    account_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Build query
    query = {
        "user_id": current_user.id,
        "transaction_date": {"$gte": start, "$lte": end}
    }
    if account_id:
        query["account_id"] = account_id
    
    # Get transactions
    transactions = await db.transactions.find(query).sort("transaction_date", 1).to_list(10000)
    
    # Group by month
    monthly_data = {}
    for transaction in transactions:
        month_key = transaction['transaction_date'].strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {"income": 0, "expenses": 0, "net": 0}
        
        if transaction['type'] == "Receita":
            monthly_data[month_key]["income"] += transaction['value']
        elif transaction['type'] == "Despesa":
            monthly_data[month_key]["expenses"] += transaction['value']
        
        monthly_data[month_key]["net"] = monthly_data[month_key]["income"] - monthly_data[month_key]["expenses"]
    
    return {
        "monthly_data": monthly_data,
        "transactions": [{"id": t['id'], "description": t['description'], "value": t['value'], "type": t['type'], "transaction_date": t['transaction_date']} for t in transactions]
    }

# Helper function to create comprehensive default categories
async def create_default_categories(user_id: str):
    default_categories = [
        # Receitas
        {"name": "Salário", "type": "Receita"},
        {"name": "Freelance/PJ", "type": "Receita"},
        {"name": "Pró-Labore", "type": "Receita"},
        {"name": "Aluguel Recebido", "type": "Receita"},
        {"name": "Dividendos/Juros", "type": "Receita"},
        {"name": "Vendas", "type": "Receita"},
        {"name": "13º Salário", "type": "Receita"},
        {"name": "Férias", "type": "Receita"},
        {"name": "Bônus", "type": "Receita"},
        {"name": "Outras Receitas", "type": "Receita"},
        
        # Despesas - Moradia
        {"name": "Moradia", "type": "Despesa"},
        {"name": "Aluguel", "type": "Despesa", "parent": "Moradia"},
        {"name": "Condomínio", "type": "Despesa", "parent": "Moradia"},
        {"name": "IPTU", "type": "Despesa", "parent": "Moradia"},
        {"name": "Água", "type": "Despesa", "parent": "Moradia"},
        {"name": "Luz", "type": "Despesa", "parent": "Moradia"},
        {"name": "Gás", "type": "Despesa", "parent": "Moradia"},
        {"name": "Internet", "type": "Despesa", "parent": "Moradia"},
        {"name": "Telefone", "type": "Despesa", "parent": "Moradia"},
        
        # Despesas - Transporte
        {"name": "Transporte", "type": "Despesa"},
        {"name": "Combustível", "type": "Despesa", "parent": "Transporte"},
        {"name": "Transporte Público", "type": "Despesa", "parent": "Transporte"},
        {"name": "Uber/99", "type": "Despesa", "parent": "Transporte"},
        {"name": "Estacionamento", "type": "Despesa", "parent": "Transporte"},
        {"name": "IPVA", "type": "Despesa", "parent": "Transporte"},
        
        # Despesas - Alimentação
        {"name": "Alimentação", "type": "Despesa"},
        {"name": "Supermercado", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Restaurantes", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Delivery", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Feira", "type": "Despesa", "parent": "Alimentação"},
        
        # Despesas - Saúde
        {"name": "Saúde", "type": "Despesa"},
        {"name": "Plano de Saúde", "type": "Despesa", "parent": "Saúde"},
        {"name": "Consultas", "type": "Despesa", "parent": "Saúde"},
        {"name": "Remédios", "type": "Despesa", "parent": "Saúde"},
        
        # Despesas - Lazer
        {"name": "Lazer", "type": "Despesa"},
        {"name": "Cinema", "type": "Despesa", "parent": "Lazer"},
        {"name": "Viagens", "type": "Despesa", "parent": "Lazer"},
        {"name": "Streaming", "type": "Despesa", "parent": "Lazer"},
        
        # Outras categorias principais
        {"name": "Educação", "type": "Despesa"},
        {"name": "Compras", "type": "Despesa"},
        {"name": "Investimentos", "type": "Despesa"},
        {"name": "Outras Despesas", "type": "Despesa"}
    ]
    
    # Create parent categories first
    parent_categories = {}
    categories_to_insert = []
    
    for cat_data in default_categories:
        if "parent" not in cat_data:
            category = Category(
                user_id=user_id,
                name=cat_data["name"],
                type=cat_data["type"],
                is_custom=False
            )
            categories_to_insert.append(category.dict())
            parent_categories[cat_data["name"]] = category.id
    
    # Insert parent categories
    await db.categories.insert_many(categories_to_insert)
    
    # Create subcategories
    subcategories_to_insert = []
    for cat_data in default_categories:
        if "parent" in cat_data:
            parent_id = parent_categories.get(cat_data["parent"])
            if parent_id:
                category = Category(
                    user_id=user_id,
                    name=cat_data["name"],
                    type=cat_data["type"],
                    parent_category_id=parent_id,
                    is_custom=False
                )
                subcategories_to_insert.append(category.dict())
    
    if subcategories_to_insert:
        await db.categories.insert_many(subcategories_to_insert)

# Helper function to update budget spent amount
async def update_budget_spent(user_id: str, category_id: str, month_year: str, amount: float):
    await db.budgets.update_one(
        {"user_id": user_id, "category_id": category_id, "month_year": month_year},
        {"$inc": {"spent_amount": amount}},
        upsert=False
    )

# Include router
app.include_router(api_router)

# Enhanced CORS
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