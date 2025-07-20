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
# Email imports for production use (currently simulated)
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart
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

# Email utility functions
def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)

async def send_email(to_email: str, subject: str, html_content: str, text_content: str = None):
    """Send email using SMTP (simulated for MVP)"""
    try:
        # For MVP, we'll log the email instead of actually sending
        print(f"[EMAIL SIMULATION] To: {to_email}")
        print(f"[EMAIL SIMULATION] Subject: {subject}")
        print(f"[EMAIL SIMULATION] Content: {html_content}")
        
        # In production, this would actually send the email:
        # msg = MIMEMultipart("alternative")
        # msg["Subject"] = subject
        # msg["From"] = EMAIL_FROM
        # msg["To"] = to_email
        # 
        # if text_content:
        #     msg.attach(MIMEText(text_content, "plain"))
        # msg.attach(MIMEText(html_content, "html"))
        # 
        # with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SMTP_USERNAME, SMTP_PASSWORD)
        #     server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False

async def send_verification_email(user_email: str, verification_token: str):
    """Send email verification email"""
    verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    
    subject = "Confirme seu email - OrçaZenFinanceiro"
    html_content = f"""
    <html>
    <body>
        <h2>Bem-vindo ao OrçaZenFinanceiro!</h2>
        <p>Obrigado por se cadastrar. Para ativar sua conta, clique no link abaixo:</p>
        <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Confirmar Email</a></p>
        <p>Ou acesse: {verification_url}</p>
        <p>Este link expira em 24 horas.</p>
        <p>Se você não se cadastrou no OrçaZenFinanceiro, ignore este email.</p>
    </body>
    </html>
    """
    
    text_content = f"""
    Bem-vindo ao OrçaZenFinanceiro!
    
    Para ativar sua conta, acesse: {verification_url}
    
    Este link expira em 24 horas.
    """
    
    return await send_email(user_email, subject, html_content, text_content)

async def send_password_reset_email(user_email: str, reset_token: str):
    """Send password reset email"""
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = "Redefinir senha - OrçaZenFinanceiro"
    html_content = f"""
    <html>
    <body>
        <h2>Redefinir sua senha</h2>
        <p>Você solicitou uma redefinição de senha. Clique no link abaixo para criar uma nova senha:</p>
        <p><a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Redefinir Senha</a></p>
        <p>Ou acesse: {reset_url}</p>
        <p>Este link expira em 1 hora por segurança.</p>
        <p>Se você não solicitou esta redefinição, ignore este email.</p>
    </body>
    </html>
    """
    
    text_content = f"""
    Redefinir sua senha
    
    Para redefinir sua senha, acesse: {reset_url}
    
    Este link expira em 1 hora.
    """
    
    return await send_email(user_email, subject, html_content, text_content)

# Intelligent category suggestion function
def suggest_category_from_description(description: str, transaction_type: str) -> str:
    """
    Suggest category based on transaction description using simple keyword matching
    """
    description_lower = description.lower()
    
    # Keywords mapping for intelligent suggestions
    category_keywords = {
        # RECEITAS
        "Salário": ["salario", "salário", "pagamento", "ordenado", "vencimento"],
        "Freelance/PJ": ["freelance", "freela", "projeto", "consultoria", "pj", "pessoa juridica"],
        "Pró-Labore": ["pro labore", "pró-labore", "pro-labore", "prolabore"],
        "Aluguel Recebido": ["aluguel recebido", "locação", "inquilino"],
        "Dividendos/Juros (Investimentos)": ["dividendos", "juros", "rendimento", "yield", "proventos"],
        "Vendas (Produtos/Serviços)": ["venda", "vendas", "produto vendido", "serviço prestado"],
        "13º Salário": ["13 salario", "13º salário", "decimo terceiro"],
        "Férias": ["ferias", "férias", "descanso remunerado"],
        "Bônus": ["bonus", "bônus", "premiação", "gratificação"],
        
        # MORADIA
        "Aluguel": ["aluguel", "locação", "rent"],
        "Condomínio": ["condominio", "condomínio", "administração", "taxa condominial"],
        "IPTU": ["iptu", "imposto territorial", "predial"],
        "Água": ["agua", "água", "saneamento", "cedae", "sabesp"],
        "Luz": ["luz", "energia", "eletricidade", "cemig", "cpfl", "light"],
        "Gás": ["gas", "gás", "comgas", "ultragaz"],
        "Internet": ["internet", "banda larga", "wi-fi", "wifi", "vivo fibra", "claro", "oi", "tim"],
        "Telefone Fixo": ["telefone fixo", "linha fixa"],
        
        # TRANSPORTE
        "Combustível (Gasolina)": ["gasolina", "posto", "combustível", "etanol", "alcool"],
        "Uber/99/Táxi": ["uber", "99", "taxi", "táxi", "corrida", "viagem"],
        "Transporte Público": ["metro", "metrô", "ônibus", "onibus", "trem", "cptm", "bilhete único"],
        "Estacionamento": ["estacionamento", "parking", "zona azul"],
        "IPVA": ["ipva", "imposto veiculo", "licenciamento"],
        "Seguro Auto": ["seguro auto", "seguro carro", "seguro veículo"],
        
        # ALIMENTAÇÃO
        "Supermercado": ["mercado", "supermercado", "compras", "pao de acucar", "carrefour", "extra"],
        "Restaurantes": ["restaurante", "jantar", "almoço", "comida", "refeição"],
        "Delivery": ["delivery", "ifood", "uber eats", "pedido", "entrega"],
        "Feira": ["feira", "hortifruti", "verduras", "frutas"],
        "Bares/Cafés": ["bar", "cafe", "café", "cerveja", "bebida", "starbucks"],
        
        # SAÚDE
        "Plano de Saúde": ["plano saude", "plano de saúde", "unimed", "amil", "bradesco saúde"],
        "Consultas Médicas": ["consulta", "medico", "médico", "clinica", "clínica"],
        "Remédios": ["farmacia", "farmácia", "medicamento", "remedio", "droga"],
        "Odontologia": ["dentista", "odonto", "dental"],
        
        # LAZER
        "Cinema": ["cinema", "filme", "ingresso", "sessão"],
        "Netflix": ["netflix", "streaming"],
        "Spotify": ["spotify", "música", "musica"],
        "Viagens (Passagens)": ["passagem", "avião", "voo", "gol", "tam", "azul"],
        "Viagens (Hospedagem)": ["hotel", "pousada", "hospedagem", "booking"],
        
        # EDUCAÇÃO
        "Mensalidade Escolar": ["escola", "colegio", "colégio", "mensalidade"],
        "Cursos Livres/Idiomas": ["curso", "idioma", "inglês", "espanhol"],
        "Livros": ["livro", "livraria", "amazon", "literatura"],
        
        # COMPRAS
        "Roupas": ["roupa", "vestuário", "camisa", "calça", "vestido", "loja"],
        "Eletrônicos": ["celular", "notebook", "tv", "eletrônico"],
        "Supermercado": ["shampoo", "pasta dente", "produtos limpeza"],
        
        # SERVIÇOS PESSOAIS
        "Salão de Beleza": ["salao", "salão", "cabeleireiro", "beleza"],
        "Academia": ["academia", "gym", "musculação", "smart fit"],
        
        # PETS
        "Ração": ["racao", "ração", "pet", "cachorro", "gato"],
        "Veterinário": ["veterinario", "veterinário", "vet", "animal"]
    }
    
    # Find best match based on keywords
    best_match = None
    max_matches = 0
    
    for category, keywords in category_keywords.items():
        matches = sum(1 for keyword in keywords if keyword in description_lower)
        if matches > max_matches:
            max_matches = matches
            best_match = category
    
    # Return suggestion or default
    if best_match and max_matches > 0:
        return best_match
    else:
        return "Outras Receitas" if transaction_type == "Receita" else "Outras Despesas"

# Endpoint for intelligent category suggestion
@api_router.post("/transactions/suggest-category")
async def suggest_category(request: dict, current_user: User = Depends(get_current_user)):
    description = request.get('description', '')
    transaction_type = request.get('type', 'Despesa')
    
    suggested_category = suggest_category_from_description(description, transaction_type)
    
    # Find the category in the database
    category = await db.categories.find_one({
        "$or": [
            {"user_id": current_user.id, "name": suggested_category},
            {"user_id": None, "name": suggested_category}  # System categories
        ]
    })
    
    if category:
        return {
            "suggested_category": suggested_category,
            "category_id": category["id"],
            "confidence": "high" if suggested_category != "Outras Despesas" and suggested_category != "Outras Receitas" else "low"
        }
    else:
        return {
            "suggested_category": "Outras Despesas" if transaction_type == "Despesa" else "Outras Receitas",
            "category_id": None,
            "confidence": "low"
        }

# Endpoint for recent description suggestions
@api_router.get("/transactions/recent-descriptions")
async def get_recent_descriptions(current_user: User = Depends(get_current_user)):
    """Get recent unique transaction descriptions for autocomplete"""
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {"_id": "$description", "last_used": {"$max": "$transaction_date"}}},
        {"$sort": {"last_used": -1}},
        {"$limit": 20},
        {"$project": {"_id": 0, "description": "$_id"}}
    ]
    
    recent_descriptions = await db.transactions.aggregate(pipeline).to_list(20)
    return [item["description"] for item in recent_descriptions]

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
    
    # Generate email verification token
    verification_token = generate_verification_token()
    
    # Create user
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
        email_verified=False,  # Require email verification
        email_verification_token=verification_token
    )
    
    await db.users.insert_one(user.dict())
    
    # Create default categories for user
    await create_default_categories(user.id)
    
    # Send verification email
    await send_verification_email(user_data.email, verification_token)
    
    return {
        "message": "Usuário criado com sucesso! Verifique seu email para ativar a conta.",
        "email_sent": True
    }

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Check if email is verified
    if not user.get('email_verified', False):
        raise HTTPException(status_code=401, detail="Email não verificado. Verifique sua caixa de entrada.")
    
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

@api_router.post("/auth/verify-email")
async def verify_email(verification_data: EmailConfirmation):
    """Verify user email with token"""
    user = await db.users.find_one({"email_verification_token": verification_data.token})
    if not user:
        raise HTTPException(status_code=400, detail="Token de verificação inválido ou expirado")
    
    # Update user as verified
    await db.users.update_one(
        {"id": user["id"]}, 
        {
            "$set": {
                "email_verified": True,
                "email_verification_token": None
            }
        }
    )
    
    # Create access token for immediate login
    token = create_access_token({"sub": user['id'], "email": user['email'], "name": user['name']})
    
    return {
        "message": "Email verificado com sucesso!",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600,
        "user": {"id": user['id'], "name": user['name'], "email": user['email']}
    }

@api_router.post("/auth/forgot-password")
async def forgot_password(request_data: PasswordResetRequest):
    """Request password reset"""
    user = await db.users.find_one({"email": request_data.email})
    if not user:
        # Don't reveal if email exists for security
        return {"message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha."}
    
    # Generate reset token and expiry
    reset_token = generate_verification_token()
    reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
    
    # Update user with reset token
    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "password_reset_token": reset_token,
                "password_reset_expires": reset_expires
            }
        }
    )
    
    # Send password reset email
    await send_password_reset_email(user["email"], reset_token)
    
    return {"message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha."}

@api_router.post("/auth/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset password with token"""
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(status_code=400, detail="Senhas não coincidem")
    
    user = await db.users.find_one({
        "password_reset_token": reset_data.token,
        "password_reset_expires": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Token de redefinição inválido ou expirado")
    
    # Hash new password
    password_bytes = reset_data.new_password.encode('utf-8')
    salt = bcrypt.gensalt()
    new_password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Update user with new password and clear reset token
    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "password_hash": new_password_hash
            },
            "$unset": {
                "password_reset_token": "",
                "password_reset_expires": ""
            }
        }
    )
    
    return {"message": "Senha redefinida com sucesso!"}

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
    status: Optional[str] = None,  # "Pago" ou "Pendente"
    start_date: Optional[str] = None,  # Format: YYYY-MM-DD
    end_date: Optional[str] = None,    # Format: YYYY-MM-DD
    search: Optional[str] = None,      # Search in description
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Advanced transaction filtering endpoint with comprehensive search options:
    - Date range filtering (start_date, end_date)
    - Search by description
    - Filter by account, category, type, status
    - Value range filtering
    - Pagination support
    """
    # Build query
    query = {"user_id": current_user.id}
    
    # Account filter
    if account_id:
        query["account_id"] = account_id
    
    # Category filter
    if category_id:
        query["category_id"] = category_id
    
    # Type filter (Receita/Despesa)
    if type_filter:
        query["type"] = type_filter
    
    # Status filter (Pago/Pendente)
    if status:
        query["status"] = status
    
    # Date range filter
    date_filter = {}
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            date_filter["$gte"] = start_datetime
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            # Add 23:59:59 to include the entire end date
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            date_filter["$lte"] = end_datetime
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
    
    if date_filter:
        query["transaction_date"] = date_filter
    
    # Description search (case insensitive)
    if search:
        query["description"] = {"$regex": search, "$options": "i"}
    
    # Value range filter
    value_filter = {}
    if min_value is not None:
        value_filter["$gte"] = min_value
    if max_value is not None:
        value_filter["$lte"] = max_value
    if value_filter:
        query["value"] = value_filter
    
    # Get total count for pagination info
    total_count = await db.transactions.count_documents(query)
    
    # Execute query with sorting and pagination
    transactions = await db.transactions.find(query)\
        .sort("transaction_date", -1)\
        .skip(offset)\
        .limit(limit)\
        .to_list(limit)
    
    return [Transaction(**transaction) for transaction in transactions]

# Endpoint to confirm payment of pending transactions
@api_router.patch("/transactions/{transaction_id}/confirm-payment")
async def confirm_payment(transaction_id: str, current_user: User = Depends(get_current_user)):
    """
    Confirm payment for a pending transaction and update account balance
    """
    # Check if transaction belongs to user and is pending
    transaction = await db.transactions.find_one({
        "id": transaction_id, 
        "user_id": current_user.id,
        "status": "Pendente"
    })
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transação pendente não encontrada")
    
    # Update transaction status to "Pago"
    await db.transactions.update_one(
        {"id": transaction_id},
        {"$set": {"status": "Pago", "updated_at": datetime.utcnow()}}
    )
    
    # Update account balance based on transaction type
    balance_change = transaction['value'] if transaction['type'] == "Receita" else -transaction['value']
    await db.accounts.update_one(
        {"id": transaction['account_id']},
        {"$inc": {"current_balance": balance_change}}
    )
    
    return {"message": "Pagamento confirmado com sucesso"}

# Endpoint for transaction statistics
@api_router.get("/transactions/statistics")
async def get_transaction_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get transaction statistics for charts and reports"""
    query = {"user_id": current_user.id}
    
    # Apply date filter if provided
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            date_filter["$lte"] = end_date_obj.replace(hour=23, minute=59, second=59)
        query["transaction_date"] = date_filter
    
    # Aggregate statistics
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "type": "$type",
                "status": "$status"
            },
            "count": {"$sum": 1},
            "total_value": {"$sum": "$value"}
        }},
        {"$group": {
            "_id": None,
            "stats": {
                "$push": {
                    "type": "$_id.type",
                    "status": "$_id.status",
                    "count": "$count",
                    "total_value": "$total_value"
                }
            }
        }}
    ]
    
    result = await db.transactions.aggregate(pipeline).to_list(1)
    
    if result:
        return {"statistics": result[0]["stats"]}
    else:
        return {"statistics": []}

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
        # RECEITAS DETALHADAS
        {"name": "Salário", "type": "Receita"},
        {"name": "Freelance/PJ", "type": "Receita"},
        {"name": "Pró-Labore", "type": "Receita"},
        {"name": "Aluguel Recebido", "type": "Receita"},
        {"name": "Dividendos/Juros (Investimentos)", "type": "Receita"},
        {"name": "Vendas (Produtos/Serviços)", "type": "Receita"},
        {"name": "Restituição de IR", "type": "Receita"},
        {"name": "13º Salário", "type": "Receita"},
        {"name": "Férias", "type": "Receita"},
        {"name": "Indenizações", "type": "Receita"},
        {"name": "Presentes/Doações Recebidas", "type": "Receita"},
        {"name": "Bônus", "type": "Receita"},
        {"name": "Outras Receitas", "type": "Receita"},
        
        # DESPESAS - MORADIA (Principal)
        {"name": "Moradia", "type": "Despesa"},
        {"name": "Aluguel", "type": "Despesa", "parent": "Moradia"},
        {"name": "Condomínio", "type": "Despesa", "parent": "Moradia"},
        {"name": "IPTU", "type": "Despesa", "parent": "Moradia"},
        {"name": "Água", "type": "Despesa", "parent": "Moradia"},
        {"name": "Luz", "type": "Despesa", "parent": "Moradia"},
        {"name": "Gás", "type": "Despesa", "parent": "Moradia"},
        {"name": "Internet", "type": "Despesa", "parent": "Moradia"},
        {"name": "Telefone Fixo", "type": "Despesa", "parent": "Moradia"},
        {"name": "Manutenção e Reparos", "type": "Despesa", "parent": "Moradia"},
        {"name": "Financiamento Imobiliário", "type": "Despesa", "parent": "Moradia"},
        {"name": "Seguro Residencial", "type": "Despesa", "parent": "Moradia"},
        
        # DESPESAS - TRANSPORTE (Principal)
        {"name": "Transporte", "type": "Despesa"},
        {"name": "Combustível (Gasolina)", "type": "Despesa", "parent": "Transporte"},
        {"name": "Combustível (Etanol)", "type": "Despesa", "parent": "Transporte"},
        {"name": "Combustível (GNV)", "type": "Despesa", "parent": "Transporte"},
        {"name": "Estacionamento", "type": "Despesa", "parent": "Transporte"},
        {"name": "Pedágio", "type": "Despesa", "parent": "Transporte"},
        {"name": "Transporte Público", "type": "Despesa", "parent": "Transporte"},
        {"name": "Uber/99/Táxi", "type": "Despesa", "parent": "Transporte"},
        {"name": "Manutenção do Veículo", "type": "Despesa", "parent": "Transporte"},
        {"name": "Seguro Auto", "type": "Despesa", "parent": "Transporte"},
        {"name": "IPVA", "type": "Despesa", "parent": "Transporte"},
        {"name": "Licenciamento", "type": "Despesa", "parent": "Transporte"},
        {"name": "Multas", "type": "Despesa", "parent": "Transporte"},
        {"name": "Lavagem de Carro", "type": "Despesa", "parent": "Transporte"},
        {"name": "Revisões", "type": "Despesa", "parent": "Transporte"},
        
        # DESPESAS - ALIMENTAÇÃO (Principal)
        {"name": "Alimentação", "type": "Despesa"},
        {"name": "Supermercado", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Feira", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Hortifrúti", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Açougue/Padaria", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Restaurantes", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Lanches", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Delivery", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Bares/Cafés", "type": "Despesa", "parent": "Alimentação"},
        {"name": "Suplementos Alimentares", "type": "Despesa", "parent": "Alimentação"},
        
        # DESPESAS - EDUCAÇÃO (Principal)
        {"name": "Educação", "type": "Despesa"},
        {"name": "Mensalidade Escolar", "type": "Despesa", "parent": "Educação"},
        {"name": "Mensalidade Universitária", "type": "Despesa", "parent": "Educação"},
        {"name": "Cursos Livres/Idiomas", "type": "Despesa", "parent": "Educação"},
        {"name": "Material Escolar", "type": "Despesa", "parent": "Educação"},
        {"name": "Livros", "type": "Despesa", "parent": "Educação"},
        {"name": "Pós-graduação", "type": "Despesa", "parent": "Educação"},
        
        # DESPESAS - SAÚDE (Principal)
        {"name": "Saúde", "type": "Despesa"},
        {"name": "Plano de Saúde", "type": "Despesa", "parent": "Saúde"},
        {"name": "Consultas Médicas", "type": "Despesa", "parent": "Saúde"},
        {"name": "Especialistas", "type": "Despesa", "parent": "Saúde"},
        {"name": "Exames", "type": "Despesa", "parent": "Saúde"},
        {"name": "Remédios", "type": "Despesa", "parent": "Saúde"},
        {"name": "Óculos/Lentes", "type": "Despesa", "parent": "Saúde"},
        {"name": "Odontologia", "type": "Despesa", "parent": "Saúde"},
        {"name": "Fisioterapia", "type": "Despesa", "parent": "Saúde"},
        {"name": "Terapias", "type": "Despesa", "parent": "Saúde"},
        {"name": "Vacinas", "type": "Despesa", "parent": "Saúde"},
        
        # DESPESAS - LAZER E ENTRETENIMENTO (Principal)
        {"name": "Lazer e Entretenimento", "type": "Despesa"},
        {"name": "Cinema", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Teatro", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Shows", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Eventos Esportivos", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Viagens (Passagens)", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Viagens (Hospedagem)", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Viagens (Passeios)", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Netflix", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Spotify", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Prime Video", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Globoplay", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Jogos", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Hobbies", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        {"name": "Festas/Eventos Sociais", "type": "Despesa", "parent": "Lazer e Entretenimento"},
        
        # DESPESAS - COMPRAS/VESTUÁRIO (Principal)
        {"name": "Compras/Vestuário", "type": "Despesa"},
        {"name": "Roupas", "type": "Despesa", "parent": "Compras/Vestuário"},
        {"name": "Calçados", "type": "Despesa", "parent": "Compras/Vestuário"},
        {"name": "Acessórios", "type": "Despesa", "parent": "Compras/Vestuário"},
        {"name": "Eletrônicos", "type": "Despesa", "parent": "Compras/Vestuário"},
        {"name": "Eletrodomésticos", "type": "Despesa", "parent": "Compras/Vestuário"},
        {"name": "Móveis", "type": "Despesa", "parent": "Compras/Vestuário"},
        {"name": "Utensílios Domésticos", "type": "Despesa", "parent": "Compras/Vestuário"},
        {"name": "Presentes", "type": "Despesa", "parent": "Compras/Vestuário"},
        {"name": "Artigos de Decoração", "type": "Despesa", "parent": "Compras/Vestuário"},
        
        # DESPESAS - SERVIÇOS PESSOAIS (Principal)
        {"name": "Serviços Pessoais", "type": "Despesa"},
        {"name": "Salão de Beleza", "type": "Despesa", "parent": "Serviços Pessoais"},
        {"name": "Cabeleireiro", "type": "Despesa", "parent": "Serviços Pessoais"},
        {"name": "Manicure", "type": "Despesa", "parent": "Serviços Pessoais"},
        {"name": "Barbearia", "type": "Despesa", "parent": "Serviços Pessoais"},
        {"name": "Academia", "type": "Despesa", "parent": "Serviços Pessoais"},
        {"name": "Personal Trainer", "type": "Despesa", "parent": "Serviços Pessoais"},
        {"name": "Estética", "type": "Despesa", "parent": "Serviços Pessoais"},
        {"name": "Massagem", "type": "Despesa", "parent": "Serviços Pessoais"},
        {"name": "Lavanderia", "type": "Despesa", "parent": "Serviços Pessoais"},
        
        # DESPESAS - DÍVIDAS E EMPRÉSTIMOS (Principal)
        {"name": "Dívidas e Empréstimos", "type": "Despesa"},
        {"name": "Empréstimos Pessoais", "type": "Despesa", "parent": "Dívidas e Empréstimos"},
        {"name": "Financiamento de Veículo", "type": "Despesa", "parent": "Dívidas e Empréstimos"},
        {"name": "Fatura do Cartão de Crédito", "type": "Despesa", "parent": "Dívidas e Empréstimos"},
        {"name": "Juros de Dívidas", "type": "Despesa", "parent": "Dívidas e Empréstimos"},
        {"name": "Cheque Especial", "type": "Despesa", "parent": "Dívidas e Empréstimos"},
        
        # DESPESAS - IMPOSTOS E TAXAS (Principal)
        {"name": "Impostos e Taxas", "type": "Despesa"},
        {"name": "Imposto de Renda", "type": "Despesa", "parent": "Impostos e Taxas"},
        {"name": "Taxas Bancárias", "type": "Despesa", "parent": "Impostos e Taxas"},
        {"name": "Contribuição Sindical", "type": "Despesa", "parent": "Impostos e Taxas"},
        {"name": "Taxas de Condomínio Extras", "type": "Despesa", "parent": "Impostos e Taxas"},
        
        # DESPESAS - INVESTIMENTOS (Principal)
        {"name": "Investimentos", "type": "Despesa"},
        {"name": "Aplicações Financeiras", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Compra de Ações", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Fundos de Investimento", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Poupança Programada", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Custos de Corretagem", "type": "Despesa", "parent": "Investimentos"},
        
        # DESPESAS - DOAÇÕES (Principal)
        {"name": "Doações", "type": "Despesa"},
        {"name": "Caridade", "type": "Despesa", "parent": "Doações"},
        {"name": "Dízimo", "type": "Despesa", "parent": "Doações"},
        
        # DESPESAS - PETS (Principal)
        {"name": "Despesas com Pets", "type": "Despesa"},
        {"name": "Ração", "type": "Despesa", "parent": "Despesas com Pets"},
        {"name": "Veterinário", "type": "Despesa", "parent": "Despesas com Pets"},
        {"name": "Acessórios para Pets", "type": "Despesa", "parent": "Despesas com Pets"},
        {"name": "Banho e Tosa", "type": "Despesa", "parent": "Despesas com Pets"},
        
        # OUTRAS DESPESAS
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