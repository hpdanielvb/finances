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
import re
import statistics
import random
from collections import defaultdict, Counter
import pytesseract
import pandas as pd
from pdf2image import convert_from_bytes
from PIL import Image

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

# Email Configuration
EMAIL_FROM = os.environ.get('EMAIL_FROM', "OrçaZenFinanceiro <noreply@orcazenfinanceiro.com>")
SMTP_SERVER = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USER', 'demo@orcazen.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'demo_password')
EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
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

class ProfileUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

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
    icon: Optional[str] = None
    color: Optional[str] = None
    keywords: Optional[List[str]] = []  # Keywords for AI classification

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # None for system categories
    name: str
    type: str
    parent_category_id: Optional[str] = None
    parent_category_name: Optional[str] = None  # For easier display
    icon: Optional[str] = None  # Emoji or icon name
    color: Optional[str] = "#6B7280"  # Default gray
    keywords: List[str] = []  # Keywords for AI matching
    is_custom: bool = False
    is_active: bool = True
    usage_count: int = 0  # Track usage for smart suggestions
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
    tags: Optional[List[str]] = []  # List of tag IDs

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
    tags: List[str] = []  # List of tag IDs
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
    category: str  # "Emergência", "Casa Própria", "Viagem", "Aposentadoria", "Lazer", "Outros"
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

# ============================================================================
# 🧠 MODELOS DE IA - SISTEMA INTELIGENTE
# ============================================================================

class AIInsight(BaseModel):
    type: str  # "prediction", "anomaly", "suggestion", "classification"
    category: str  # "spending", "income", "savings", "budget"
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    actionable: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = {}

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    response: str
    intent: Optional[str] = None  # "balance_inquiry", "expense_analysis", "budget_help"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PredictionRequest(BaseModel):
    days_ahead: int = 30
    category: Optional[str] = None

class AnomalyAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    transaction_id: str
    anomaly_type: str  # "unusual_amount", "unusual_category", "unusual_frequency"
    severity: str  # "low", "medium", "high"
    description: str
    suggested_action: str
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# 🏠 MODELOS DE CONSÓRCIO
# ============================================================================

class Consortium(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    type: str  # "Imóvel", "Veículo", "Moto"
    total_value: float  # Valor da carta
    installment_count: int  # Parcelas totais
    paid_installments: int = 0  # Parcelas pagas
    monthly_installment: float  # Valor da parcela
    remaining_balance: float  # Saldo devedor
    contemplated: bool = False  # Contemplado
    contemplation_date: Optional[datetime] = None
    bid_value: Optional[float] = None  # Valor do lance
    status: str = "Ativo"  # "Ativo", "Pago", "Contemplado", "Suspenso"
    due_day: int = 15  # Dia do vencimento
    start_date: datetime
    administrator: str  # Administradora do consórcio
    group_number: Optional[str] = None
    quota_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ConsortiumPayment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consortium_id: str
    user_id: str
    installment_number: int
    payment_date: datetime
    amount_paid: float
    payment_type: str = "Regular"  # "Regular", "Antecipado", "Lance", "Quitação"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ConsortiumBid(BaseModel):
    consortium_id: str
    bid_value: float
    bid_date: datetime
    notes: Optional[str] = None

class ConsortiumContemplation(BaseModel):
    consortium_id: str
    contemplation_type: str  # "Sorteio", "Lance"
    contemplation_date: datetime
    notes: Optional[str] = None

# ============================================================================
# 💳 CREDIT CARD INVOICE MODELS
# ============================================================================

class CreditCardInvoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    account_id: str  # Credit card account
    invoice_month: str  # YYYY-MM format
    due_date: datetime
    closing_date: datetime
    total_amount: float = 0
    paid_amount: float = 0
    status: str = "Pending"  # "Pending", "Paid", "Overdue"
    transactions: List[str] = []  # List of transaction IDs included in this invoice
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None

class TransactionTag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    color: str = "#6B7280"
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

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

# File Import Models
class FileImportSession(BaseModel):
    session_id: str
    user_id: str
    files_processed: int
    preview_data: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "processing"  # processing, completed, error

class ImportTransaction(BaseModel):
    data: str
    descricao: str
    valor: float
    categoria: Optional[str] = None
    conta: Optional[str] = None
    tipo: str = "Despesa"  # Receita or Despesa
    is_duplicate: bool = False
    confidence_score: float = 1.0  # For OCR results

class ImportConfirmRequest(BaseModel):
    session_id: str
    selected_transactions: List[ImportTransaction]

# ============================================================================
# 🏠 CONSORTIUM AND CONSIGNED LOAN MODELS - PHASE 2
# ============================================================================

class ContractBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tipo: str  # "consórcio" ou "consignado"
    nome: str
    valor_total: float
    parcela_mensal: float
    quantidade_parcelas: int
    parcela_atual: int = 0
    juros_mensal: float
    taxa_administrativa: float
    seguro: float
    data_inicio: datetime
    data_vencimento: datetime
    status: str = "ativo"  # "ativo", "quitado", "cancelado"
    observacoes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContractCreate(BaseModel):
    tipo: str  # "consórcio" ou "consignado"
    nome: str
    valor_total: float
    parcela_mensal: float
    quantidade_parcelas: int
    parcela_atual: int = 0
    juros_mensal: float
    taxa_administrativa: float
    seguro: float
    data_inicio: datetime
    data_vencimento: datetime
    status: str = "ativo"
    observacoes: Optional[str] = None

class ContractUpdate(BaseModel):
    nome: Optional[str] = None
    parcela_atual: Optional[int] = None
    juros_mensal: Optional[float] = None
    taxa_administrativa: Optional[float] = None
    seguro: Optional[float] = None
    data_vencimento: Optional[datetime] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None

# ============================================================================
# 🐾 PET SHOP MODULE MODELS - PHASE 3
# ============================================================================

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    sku: str
    name: str
    description: Optional[str] = None
    cost_price: float  # Preço de custo
    sale_price: float  # Preço de venda
    current_stock: int
    minimum_stock: int = 10
    expiry_date: Optional[datetime] = None
    supplier: Optional[str] = None
    category: str = "Geral"  # Categoria do produto
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    cost_price: float
    sale_price: float
    current_stock: int
    minimum_stock: int = 10
    expiry_date: Optional[datetime] = None
    supplier: Optional[str] = None
    category: str = "Geral"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    sale_price: Optional[float] = None
    current_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    expiry_date: Optional[datetime] = None
    supplier: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class Sale(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: List[dict]  # List of {product_id, product_name, quantity, unit_price, total}
    subtotal: float
    discount: float = 0.0
    total: float
    payment_method: str  # "Dinheiro", "Cartão de Débito", "Cartão de Crédito", "PIX"
    payment_status: str = "Pago"  # "Pago", "Pendente"
    sale_date: datetime = Field(default_factory=datetime.utcnow)
    receipt_number: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SaleCreate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: List[dict]
    subtotal: float
    discount: float = 0.0
    total: float
    payment_method: str
    payment_status: str = "Pago"
    notes: Optional[str] = None

class StockMovement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    movement_type: str  # "entrada", "saída", "ajuste", "venda"
    quantity: int
    reason: str
    previous_stock: int
    new_stock: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # ID do usuário que fez a movimentação

# ============================================================================
# 🔄 AUTOMATIC RECURRENCE SYSTEM MODELS - PHASE 2
# ============================================================================

class RecurrenceRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str  # Nome da regra (ex: "Salário Mensal", "Aluguel")
    description: Optional[str] = None
    
    # Dados da transação base
    transaction_description: str
    transaction_value: float
    transaction_type: str  # "Receita" ou "Despesa"
    account_id: str
    category_id: Optional[str] = None
    
    # Configurações de recorrência
    recurrence_pattern: str  # "diario", "semanal", "mensal", "anual"
    interval: int = 1  # A cada X períodos (ex: a cada 2 semanas)
    start_date: datetime
    end_date: Optional[datetime] = None  # Se None, recorre indefinidamente
    next_execution_date: datetime
    
    # Configurações de execução
    auto_create: bool = False  # Se True, cria automaticamente. Se False, apenas sugere
    require_confirmation: bool = True  # Se True, requer confirmação antes de criar
    
    # Estado
    is_active: bool = True
    last_execution_date: Optional[datetime] = None
    total_executions: int = 0
    max_executions: Optional[int] = None  # Limite de execuções
    
    # Observações e tags
    observation: Optional[str] = None
    tags: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RecurrenceRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    transaction_description: str
    transaction_value: float
    transaction_type: str
    account_id: str
    category_id: Optional[str] = None
    recurrence_pattern: str
    interval: int = 1
    start_date: datetime
    end_date: Optional[datetime] = None
    auto_create: bool = False
    require_confirmation: bool = True
    max_executions: Optional[int] = None
    observation: Optional[str] = None
    tags: Optional[List[str]] = []

class RecurrenceRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    transaction_description: Optional[str] = None
    transaction_value: Optional[float] = None
    transaction_type: Optional[str] = None
    account_id: Optional[str] = None
    category_id: Optional[str] = None
    recurrence_pattern: Optional[str] = None
    interval: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    auto_create: Optional[bool] = None
    require_confirmation: Optional[bool] = None
    is_active: Optional[bool] = None
    max_executions: Optional[int] = None
    observation: Optional[str] = None
    tags: Optional[List[str]] = None

class PendingRecurrence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    recurrence_rule_id: str
    suggested_date: datetime
    transaction_data: dict  # Dados da transação que será criada
    status: str = "pending"  # "pending", "approved", "rejected", "expired"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # Data de expiração da sugestão
    
class RecurrencePreview(BaseModel):
    recurrence_rule_id: str
    rule_name: str
    next_transactions: List[dict]  # Lista de próximas transações (até 12 meses à frente)
    preview_period_months: int = 12
    
class RecurrenceConfirmation(BaseModel):
    pending_recurrence_ids: List[str]
    action: str  # "approve", "reject", "approve_all", "reject_all"
    created_by: str  # user_id who made the movement

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
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Erro de autenticação")

# Email utility functions
def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)

async def send_email(to_email: str, subject: str, html_content: str, text_content: str = None):
    """Send email using SMTP"""
    try:
        if not EMAIL_ENABLED:
            # For MVP/testing, log the email instead of actually sending
            print(f"[EMAIL SIMULATION] To: {to_email}")
            print(f"[EMAIL SIMULATION] Subject: {subject}")
            print(f"[EMAIL SIMULATION] Content: {html_content[:200]}...")
            return True
        
        # Production email sending
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        
        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"[EMAIL SENT] Successfully sent to: {to_email}")
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

# =====================================================
# PROFILE ENDPOINTS
# =====================================================

@api_router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if hasattr(current_user, 'created_at') else None,
        "email_verified": getattr(current_user, 'email_verified', True)
    }

@api_router.put("/profile")
async def update_profile(request: ProfileUpdateRequest, current_user: User = Depends(get_current_user)):
    """Update user profile (name and email)"""
    try:
        # Check if email is already taken by another user
        if request.email != current_user.email:
            existing_user = await db.users.find_one({"email": request.email})
            if existing_user:
                raise HTTPException(status_code=400, detail="Este email já está em uso")
        
        # Update user profile
        update_data = {
            "name": request.name,
            "email": request.email
        }
        
        # If email changed, might need to re-verify
        if request.email != current_user.email:
            update_data["email_verified"] = False
            # In production, send verification email here
        
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": update_data}
        )
        
        print(f"[LOG] Profile updated for user: {current_user.email} -> {request.email}")
        return {"message": "Perfil atualizado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@api_router.put("/profile/password")
async def change_password(request: PasswordChangeRequest, current_user: User = Depends(get_current_user)):
    """Change user password"""
    try:
        # Verify current password
        password_bytes = request.current_password.encode('utf-8')
        stored_hash = current_user.password_hash.encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, stored_hash):
            raise HTTPException(status_code=400, detail="Senha atual incorreta")
        
        # Validate new password confirmation
        if request.new_password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Nova senha e confirmação não coincidem")
        
        # Check if new password is different from current
        new_password_bytes = request.new_password.encode('utf-8')
        if bcrypt.checkpw(new_password_bytes, stored_hash):
            raise HTTPException(status_code=400, detail="A nova senha deve ser diferente da atual")
        
        # Hash new password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password_bytes, salt).decode('utf-8')
        
        # Update password
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"password_hash": hashed_password}}
        )
        
        print(f"[LOG] Password changed for user: {current_user.email}")
        return {"message": "Senha alterada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Password change error: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

# Balance Audit and Correction Endpoint
@api_router.post("/admin/audit-and-fix-balances")
async def audit_and_fix_balances(current_user: User = Depends(get_current_user)):
    """
    ADMIN ENDPOINT: Audit and fix balance calculation errors
    This addresses the critical R$ 84.08 discrepancy issue
    """
    print(f"[AUDIT] Starting balance audit and correction for user: {current_user.id}")
    
    try:
        # Get all user accounts
        accounts = await db.accounts.find({"user_id": current_user.id}).to_list(100)
        
        corrections = []
        total_discrepancy = 0
        
        for account in accounts:
            account_id = account["id"]
            account_name = account["name"]
            initial_balance = account["initial_balance"]
            current_system_balance = account["current_balance"]
            
            # Calculate correct balance from transactions
            transactions = await db.transactions.find({
                "user_id": current_user.id,
                "account_id": account_id,
                "status": "Pago"  # Only paid transactions should affect balance
            }).to_list(1000)
            
            calculated_balance = initial_balance
            
            for trans in transactions:
                if trans["type"] == "Receita":
                    calculated_balance += trans["value"]
                elif trans["type"] == "Despesa":
                    calculated_balance -= trans["value"]
            
            discrepancy = abs(calculated_balance - current_system_balance)
            
            if discrepancy > 0.01:  # More than 1 cent difference
                # Fix the balance
                await db.accounts.update_one(
                    {"id": account_id},
                    {"$set": {"current_balance": calculated_balance}}
                )
                
                corrections.append({
                    "account_name": account_name,
                    "old_balance": current_system_balance,
                    "correct_balance": calculated_balance,
                    "discrepancy": current_system_balance - calculated_balance,
                    "fixed": True
                })
                
                total_discrepancy += discrepancy
                
                print(f"[AUDIT] Fixed {account_name}: {current_system_balance:.2f} → {calculated_balance:.2f}")
            else:
                corrections.append({
                    "account_name": account_name,
                    "old_balance": current_system_balance,
                    "correct_balance": calculated_balance,
                    "discrepancy": 0,
                    "fixed": False
                })
        
        return {
            "message": "Auditoria de saldos concluída com sucesso!",
            "corrections_made": len([c for c in corrections if c["fixed"]]),
            "total_discrepancy_fixed": total_discrepancy,
            "corrections": corrections,
            "audit_successful": True
        }
        
    except Exception as e:
        print(f"[AUDIT ERROR] Failed to audit balances: {e}")
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")

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
    
    # Update account data
    update_data = account_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    # 🔧 CORREÇÃO: Se initial_balance mudou, atualizar current_balance também
    old_initial_balance = account.get("initial_balance", 0)
    new_initial_balance = account_data.initial_balance
    
    if old_initial_balance != new_initial_balance:
        # Calcular diferença
        difference = new_initial_balance - old_initial_balance
        new_current_balance = account.get("current_balance", 0) + difference
        
        update_data["current_balance"] = new_current_balance
        
        print(f"[BALANCE UPDATE] Account {account['name']}: "
              f"Initial {old_initial_balance} → {new_initial_balance}, "
              f"Current {account.get('current_balance', 0)} → {new_current_balance}")
    
    await db.accounts.update_one({"id": account_id}, {"$set": update_data})
    
    # Return updated account
    updated_account = await db.accounts.find_one({"id": account_id})
    return Account(**updated_account)

@api_router.delete("/accounts/{account_id}")
async def delete_account(account_id: str, current_user: User = Depends(get_current_user)):
    """Delete account and all associated transactions"""
    try:
        # Check if account exists and belongs to user
        account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
        if not account:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        
        account_name = account["name"]
        
        # Count and delete transactions associated with this account
        transaction_count = await db.transactions.count_documents({"account_id": account_id})
        
        if transaction_count > 0:
            await db.transactions.delete_many({"account_id": account_id})
        
        # Delete account
        result = await db.accounts.delete_one({"id": account_id, "user_id": current_user.id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Erro ao excluir conta")
        
        return {
            "message": "Conta excluída com sucesso",
            "transactions_deleted": transaction_count,
            "account_name": account_name,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete account error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

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
        status=transaction_data.status,
        tags=transaction_data.tags or []
    )
    
    await db.transactions.insert_one(transaction.dict())
    
    # Update account balance ONLY if transaction is "Pago" (not pending)
    if transaction_data.status == "Pago":
        balance_change = transaction_data.value if transaction_data.type == "Receita" else -transaction_data.value
        await db.accounts.update_one(
            {"id": transaction_data.account_id},
            {"$inc": {"current_balance": balance_change}}
        )
        
        # Update budget if category is provided and transaction is paid
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

@api_router.get("/reports/expenses-by-category")
async def get_expenses_by_category_report(
    start_date: str,
    end_date: str,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Enhanced expenses by category with subcategory drill-down"""
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Build transaction query
    query = {
        "user_id": current_user.id,
        "transaction_date": {"$gte": start, "$lte": end},
        "type": "Despesa",
        "status": "Pago"
    }
    if account_id:
        query["account_id"] = account_id
    if category_id:
        query["category_id"] = category_id
    
    # Get transactions and categories
    transactions = await db.transactions.find(query).to_list(10000)
    categories = await db.categories.find({
        "$or": [
            {"user_id": current_user.id},
            {"user_id": None}  # System categories
        ]
    }).to_list(1000)
    
    # Create category lookup
    category_lookup = {cat['id']: cat for cat in categories}
    
    # Group by categories and subcategories
    category_data = {}
    subcategory_data = {}
    
    for transaction in transactions:
        cat_id = transaction.get('category_id')
        if not cat_id or cat_id not in category_lookup:
            continue
            
        category = category_lookup[cat_id]
        category_name = category['name']
        parent_id = category.get('parent_category_id')
        
        # Handle parent categories
        if parent_id and parent_id in category_lookup:
            parent_name = category_lookup[parent_id]['name']
            
            # Initialize parent category data
            if parent_name not in category_data:
                category_data[parent_name] = {
                    'total': 0,
                    'count': 0,
                    'subcategories': {}
                }
            
            # Add to parent category
            category_data[parent_name]['total'] += transaction['value']
            category_data[parent_name]['count'] += 1
            
            # Add to subcategory
            if category_name not in category_data[parent_name]['subcategories']:
                category_data[parent_name]['subcategories'][category_name] = {
                    'total': 0,
                    'count': 0,
                    'transactions': []
                }
            
            category_data[parent_name]['subcategories'][category_name]['total'] += transaction['value']
            category_data[parent_name]['subcategories'][category_name]['count'] += 1
            category_data[parent_name]['subcategories'][category_name]['transactions'].append({
                'id': transaction['id'],
                'description': transaction['description'],
                'value': transaction['value'],
                'date': transaction['transaction_date']
            })
        else:
            # Handle standalone categories
            if category_name not in category_data:
                category_data[category_name] = {
                    'total': 0,
                    'count': 0,
                    'subcategories': {},
                    'transactions': []
                }
            
            category_data[category_name]['total'] += transaction['value']
            category_data[category_name]['count'] += 1
            if 'transactions' not in category_data[category_name]:
                category_data[category_name]['transactions'] = []
            category_data[category_name]['transactions'].append({
                'id': transaction['id'],
                'description': transaction['description'],
                'value': transaction['value'],
                'date': transaction['transaction_date']
            })
    
    # Calculate totals and percentages
    total_expenses = sum(cat['total'] for cat in category_data.values())
    
    for category in category_data.values():
        category['percentage'] = (category['total'] / total_expenses * 100) if total_expenses > 0 else 0
        for subcat in category.get('subcategories', {}).values():
            subcat['percentage'] = (subcat['total'] / total_expenses * 100) if total_expenses > 0 else 0
    
    return {
        "category_data": category_data,
        "total_expenses": total_expenses,
        "date_range": {"start": start_date, "end": end_date},
        "filters": {"account_id": account_id, "category_id": category_id}
    }

@api_router.get("/reports/income-by-category")
async def get_income_by_category_report(
    start_date: str,
    end_date: str,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Enhanced income by category with subcategory drill-down"""
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Build transaction query
    query = {
        "user_id": current_user.id,
        "transaction_date": {"$gte": start, "$lte": end},
        "type": "Receita",
        "status": "Pago"
    }
    if account_id:
        query["account_id"] = account_id
    if category_id:
        query["category_id"] = category_id
    
    # Get transactions and categories
    transactions = await db.transactions.find(query).to_list(10000)
    categories = await db.categories.find({
        "$or": [
            {"user_id": current_user.id},
            {"user_id": None}
        ]
    }).to_list(1000)
    
    # Create category lookup
    category_lookup = {cat['id']: cat for cat in categories}
    
    # Group by categories
    category_data = {}
    
    for transaction in transactions:
        cat_id = transaction.get('category_id')
        if not cat_id or cat_id not in category_lookup:
            continue
            
        category = category_lookup[cat_id]
        category_name = category['name']
        
        if category_name not in category_data:
            category_data[category_name] = {
                'total': 0,
                'count': 0,
                'transactions': []
            }
        
        category_data[category_name]['total'] += transaction['value']
        category_data[category_name]['count'] += 1
        category_data[category_name]['transactions'].append({
            'id': transaction['id'],
            'description': transaction['description'],
            'value': transaction['value'],
            'date': transaction['transaction_date']
        })
    
    # Calculate percentages
    total_income = sum(cat['total'] for cat in category_data.values())
    
    for category in category_data.values():
        category['percentage'] = (category['total'] / total_income * 100) if total_income > 0 else 0
    
    return {
        "category_data": category_data,
        "total_income": total_income,
        "date_range": {"start": start_date, "end": end_date},
        "filters": {"account_id": account_id, "category_id": category_id}
    }

@api_router.get("/reports/detailed-cash-flow")
async def get_detailed_cash_flow_report(
    start_date: str,
    end_date: str,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Detailed cash flow with daily, weekly, and monthly breakdowns"""
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Build query
    query = {
        "user_id": current_user.id,
        "transaction_date": {"$gte": start, "$lte": end},
        "status": "Pago"
    }
    if account_id:
        query["account_id"] = account_id
    if category_id:
        query["category_id"] = category_id
    
    # Get transactions
    transactions = await db.transactions.find(query).sort("transaction_date", 1).to_list(10000)
    
    # Group by different time periods
    daily_data = {}
    weekly_data = {}
    monthly_data = {}
    
    for transaction in transactions:
        trans_date = transaction['transaction_date']
        value = transaction['value']
        trans_type = transaction['type']
        
        # Daily grouping
        day_key = trans_date.strftime("%Y-%m-%d")
        if day_key not in daily_data:
            daily_data[day_key] = {"income": 0, "expenses": 0, "net": 0, "transactions": []}
        
        # Weekly grouping (ISO week)
        year, week, _ = trans_date.isocalendar()
        week_key = f"{year}-W{week:02d}"
        if week_key not in weekly_data:
            weekly_data[week_key] = {"income": 0, "expenses": 0, "net": 0, "start_date": None, "end_date": None}
        
        # Monthly grouping
        month_key = trans_date.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {"income": 0, "expenses": 0, "net": 0}
        
        # Add values
        if trans_type == "Receita":
            daily_data[day_key]["income"] += value
            weekly_data[week_key]["income"] += value
            monthly_data[month_key]["income"] += value
        elif trans_type == "Despesa":
            daily_data[day_key]["expenses"] += value
            weekly_data[week_key]["expenses"] += value
            monthly_data[month_key]["expenses"] += value
        
        # Add transaction to daily data
        daily_data[day_key]["transactions"].append({
            'id': transaction['id'],
            'description': transaction['description'],
            'value': value,
            'type': trans_type
        })
    
    # Calculate net values
    for data in daily_data.values():
        data["net"] = data["income"] - data["expenses"]
    
    for data in weekly_data.values():
        data["net"] = data["income"] - data["expenses"]
    
    for data in monthly_data.values():
        data["net"] = data["income"] - data["expenses"]
    
    return {
        "daily_data": daily_data,
        "weekly_data": weekly_data,
        "monthly_data": monthly_data,
        "summary": {
            "total_income": sum(data["income"] for data in daily_data.values()),
            "total_expenses": sum(data["expenses"] for data in daily_data.values()),
            "net_flow": sum(data["net"] for data in daily_data.values()),
            "period": {"start": start_date, "end": end_date}
        }
    }

@api_router.get("/reports/export-excel")
async def export_excel_report(
    report_type: str,  # "transactions", "cash-flow", "expenses-by-category"
    start_date: str,
    end_date: str,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export report data in Excel format"""
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Build base query
    query = {
        "user_id": current_user.id,
        "transaction_date": {"$gte": start, "$lte": end}
    }
    if account_id:
        query["account_id"] = account_id
    if category_id:
        query["category_id"] = category_id
    
    # Get data based on report type
    if report_type == "transactions":
        transactions = await db.transactions.find(query).sort("transaction_date", -1).to_list(10000)
        
        # Get accounts and categories for lookups
        accounts = await db.accounts.find({"user_id": current_user.id}).to_list(100)
        categories = await db.categories.find({
            "$or": [{"user_id": current_user.id}, {"user_id": None}]
        }).to_list(1000)
        
        account_lookup = {acc['id']: acc['name'] for acc in accounts}
        category_lookup = {cat['id']: cat['name'] for cat in categories}
        
        excel_data = []
        for trans in transactions:
            excel_data.append({
                "Data": trans['transaction_date'].strftime("%d/%m/%Y"),
                "Descrição": trans['description'],
                "Tipo": trans['type'],
                "Valor": trans['value'],
                "Conta": account_lookup.get(trans['account_id'], 'N/A'),
                "Categoria": category_lookup.get(trans.get('category_id'), 'N/A'),
                "Status": trans['status'],
                "Observação": trans.get('observation', '')
            })
    
    elif report_type == "cash-flow":
        transactions = await db.transactions.find({
            **query, "status": "Pago"
        }).sort("transaction_date", 1).to_list(10000)
        
        # Group by month
        monthly_data = {}
        for transaction in transactions:
            month_key = transaction['transaction_date'].strftime("%m/%Y")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"Receitas": 0, "Despesas": 0}
            
            if transaction['type'] == "Receita":
                monthly_data[month_key]["Receitas"] += transaction['value']
            elif transaction['type'] == "Despesa":
                monthly_data[month_key]["Despesas"] += transaction['value']
        
        excel_data = []
        for month, data in monthly_data.items():
            excel_data.append({
                "Mês": month,
                "Receitas": data["Receitas"],
                "Despesas": data["Despesas"],
                "Saldo Líquido": data["Receitas"] - data["Despesas"]
            })
    
    # Convert to CSV format (Excel-compatible)
    if not excel_data:
        return {"error": "Nenhum dado encontrado para o período selecionado"}
    
    # Create CSV content
    headers = list(excel_data[0].keys())
    csv_content = [','.join(headers)]
    
    for row in excel_data:
        csv_row = []
        for header in headers:
            value = row[header]
            if isinstance(value, (int, float)):
                csv_row.append(str(value).replace('.', ','))  # Brazilian decimal format
            else:
                csv_row.append(f'"{str(value)}"')
        csv_content.append(','.join(csv_row))
    
    return {
        "csv_content": '\n'.join(csv_content),
        "filename": f"relatorio-{report_type}-{start_date}-{end_date}.csv",
        "total_records": len(excel_data)
    }

# ============================================================================
# 💳 CREDIT CARD INVOICE MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.post("/credit-cards/generate-invoices")
async def generate_monthly_invoices(current_user: User = Depends(get_current_user)):
    """Generate credit card invoices for all credit card accounts"""
    try:
        # Get all credit card accounts
        credit_accounts = await db.accounts.find({
            "user_id": current_user.id,
            "type": "Cartão de Crédito",
            "is_active": True
        }).to_list(100)
        
        generated_invoices = []
        current_date = datetime.utcnow()
        
        for account in credit_accounts:
            # Get invoice due date (default to 15th if not set)
            due_day = 15
            if account.get('invoice_due_date'):
                try:
                    due_day = int(account['invoice_due_date'])
                except:
                    due_day = 15
            
            # Calculate current invoice period - simplified logic for testing
            invoice_month = current_date.strftime("%Y-%m")
            closing_date = datetime(current_date.year, current_date.month, due_day - 7) if due_day > 7 else current_date
            due_date = datetime(current_date.year, current_date.month, due_day)
            
            # Check if invoice already exists
            existing_invoice = await db.credit_card_invoices.find_one({
                "account_id": account["id"],
                "invoice_month": invoice_month
            })
            
            if existing_invoice:
                continue  # Skip if invoice already exists
            
            # Get transactions for this account (last 30 days to ensure we capture recent transactions)
            period_start = current_date - timedelta(days=30)
            transactions = await db.transactions.find({
                "user_id": current_user.id,
                "account_id": account["id"],
                "type": "Despesa",
                "transaction_date": {"$gte": period_start},
                "status": "Pago"
            }).to_list(1000)
            
            # Calculate total amount
            total_amount = sum(t['value'] for t in transactions)
            
            # Create invoice even if total is 0 (for testing purposes)
            invoice = CreditCardInvoice(
                user_id=current_user.id,
                account_id=account["id"],
                invoice_month=invoice_month,
                due_date=due_date,
                closing_date=closing_date,
                total_amount=total_amount,
                transactions=[t['id'] for t in transactions]
            )
            
            await db.credit_card_invoices.insert_one(invoice.dict())
            generated_invoices.append({
                "account_name": account["name"],
                "account_id": account["id"],
                "invoice_month": invoice_month,
                "total_amount": total_amount,
                "due_date": due_date.isoformat(),
                "transaction_count": len(transactions)
            })
        
        return {
            "message": f"Geradas {len(generated_invoices)} faturas de cartão de crédito",
            "invoices_generated": len(generated_invoices),
            "invoices": generated_invoices
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar faturas: {str(e)}")

@api_router.get("/credit-cards/invoices")
async def get_credit_card_invoices(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get credit card invoices"""
    query = {"user_id": current_user.id}
    
    if account_id:
        query["account_id"] = account_id
    if status:
        query["status"] = status
    
    invoices = await db.credit_card_invoices.find(query).sort("due_date", -1).to_list(100)
    
    # Enrich with account information
    accounts = await db.accounts.find({"user_id": current_user.id}).to_list(100)
    account_lookup = {acc['id']: acc for acc in accounts}
    
    enriched_invoices = []
    for invoice in invoices:
        account = account_lookup.get(invoice['account_id'])
        
        # Convert invoice to proper format, handling ObjectId and datetime serialization
        enriched_invoice = {
            "id": invoice.get('id'),
            "user_id": invoice.get('user_id'),
            "account_id": invoice.get('account_id'),
            "invoice_month": invoice.get('invoice_month'),
            "due_date": invoice.get('due_date').isoformat() if invoice.get('due_date') else None,
            "closing_date": invoice.get('closing_date').isoformat() if invoice.get('closing_date') else None,
            "total_amount": invoice.get('total_amount', 0),
            "paid_amount": invoice.get('paid_amount', 0),
            "status": invoice.get('status', 'Pending'),
            "transactions": invoice.get('transactions', []),
            "created_at": invoice.get('created_at').isoformat() if invoice.get('created_at') else None,
            "paid_at": invoice.get('paid_at').isoformat() if invoice.get('paid_at') else None,
            "account_name": account['name'] if account else 'N/A',
            "account_color": account['color_hex'] if account else '#6B7280'
        }
        enriched_invoices.append(enriched_invoice)
    
    return enriched_invoices

@api_router.patch("/credit-cards/invoices/{invoice_id}/pay")
async def pay_credit_card_invoice(
    invoice_id: str,
    payment_data: dict,  # {"payment_amount": float}
    current_user: User = Depends(get_current_user)
):
    """Mark credit card invoice as paid"""
    try:
        payment_amount = payment_data.get('payment_amount', 0.0)
        if payment_amount <= 0:
            raise HTTPException(status_code=400, detail="Valor do pagamento deve ser maior que zero")
        
        invoice = await db.credit_card_invoices.find_one({
            "id": invoice_id,
            "user_id": current_user.id
        })
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Fatura não encontrada")
        
        # Update invoice
        update_data = {
            "paid_amount": payment_amount,
            "paid_at": datetime.utcnow(),
            "status": "Paid" if payment_amount >= invoice['total_amount'] else "Partial"
        }
        
        await db.credit_card_invoices.update_one(
            {"id": invoice_id},
            {"$set": update_data}
        )
        
        # Create payment transaction
        account = await db.accounts.find_one({"id": invoice["account_id"]})
        if account:
            payment_transaction = Transaction(
                user_id=current_user.id,
                description=f"Pagamento Fatura {account['name']} - {invoice['invoice_month']}",
                value=payment_amount,
                type="Despesa",
                transaction_date=datetime.utcnow(),
                account_id=invoice["account_id"],
                status="Pago"
            )
            
            await db.transactions.insert_one(payment_transaction.dict())
        
        return {"message": "Fatura paga com sucesso", "payment_amount": payment_amount}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar pagamento: {str(e)}")

# ============================================================================
# 🏷️ TRANSACTION TAGS MANAGEMENT
# ============================================================================

@api_router.post("/tags", response_model=TransactionTag)
async def create_tag(
    tag_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new transaction tag"""
    tag = TransactionTag(
        user_id=current_user.id,
        name=tag_data['name'],
        color=tag_data.get('color', '#6B7280'),
        description=tag_data.get('description')
    )
    
    await db.transaction_tags.insert_one(tag.dict())
    return tag

@api_router.get("/tags")
async def get_tags(current_user: User = Depends(get_current_user)):
    """Get user's transaction tags"""
    try:
        tags = await db.transaction_tags.find({"user_id": current_user.id}).to_list(100)
        # Convert to serializable format
        serialized_tags = []
        for tag in tags:
            if '_id' in tag:
                del tag['_id']  # Remove MongoDB ObjectId
            serialized_tags.append(tag)
        return {"tags": serialized_tags}
    except Exception as e:
        print(f"Error getting tags: {e}")
        # Return empty list if collection doesn't exist yet
        return {"tags": []}

@api_router.patch("/transactions/{transaction_id}/tags")
async def update_transaction_tags(
    transaction_id: str,
    tags_data: dict,  # {"tag_ids": List[str]}
    current_user: User = Depends(get_current_user)
):
    """Update transaction tags"""
    tag_ids = tags_data.get('tag_ids', [])
    
    transaction = await db.transactions.find_one({
        "id": transaction_id,
        "user_id": current_user.id
    })
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    await db.transactions.update_one(
        {"id": transaction_id},
        {"$set": {"tags": tag_ids}}
    )
    
    return {"message": "Tags atualizadas com sucesso", "tag_ids": tag_ids}

@api_router.get("/reports/by-tags")
async def get_report_by_tags(
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user)
):
    """Get transactions grouped by tags"""
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Get transactions with tags
    transactions = await db.transactions.find({
        "user_id": current_user.id,
        "transaction_date": {"$gte": start, "$lte": end},
        "tags": {"$exists": True, "$ne": []}
    }).to_list(10000)
    
    # Get all tags
    tags = await db.transaction_tags.find({"user_id": current_user.id}).to_list(100)
    tag_lookup = {tag['id']: tag for tag in tags}
    
    # Group by tags
    tag_data = {}
    
    for transaction in transactions:
        for tag_id in transaction.get('tags', []):
            if tag_id in tag_lookup:
                tag = tag_lookup[tag_id]
                tag_name = tag['name']
                
                if tag_name not in tag_data:
                    tag_data[tag_name] = {
                        'total_income': 0,
                        'total_expenses': 0,
                        'count': 0,
                        'color': tag['color'],
                        'transactions': []
                    }
                
                tag_data[tag_name]['count'] += 1
                tag_data[tag_name]['transactions'].append({
                    'id': transaction['id'],
                    'description': transaction['description'],
                    'value': transaction['value'],
                    'type': transaction['type'],
                    'date': transaction['transaction_date']
                })
                
                if transaction['type'] == 'Receita':
                    tag_data[tag_name]['total_income'] += transaction['value']
                else:
                    tag_data[tag_name]['total_expenses'] += transaction['value']
    
    return {"tag_data": tag_data, "date_range": {"start": start_date, "end": end_date}}

# Helper function to create comprehensive default categories
async def create_default_categories(user_id: str):
    print(f"[DEBUG] Starting COMPLETE Brazilian categories creation for user: {user_id}")
    
    # COMPLETE BRAZILIAN CATEGORIES AS REQUESTED BY USER
    default_categories = [
        # RECEITAS COMPLETAS
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
        
        # CATEGORIAS PRINCIPAIS BRASILEIRAS CONFORME SOLICITADO
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
        
        {"name": "Pets", "type": "Despesa"},
        {"name": "Ração", "type": "Despesa", "parent": "Pets"},
        {"name": "Veterinário", "type": "Despesa", "parent": "Pets"},
        {"name": "Acessórios para Pets", "type": "Despesa", "parent": "Pets"},
        {"name": "Banho e Tosa", "type": "Despesa", "parent": "Pets"},
        {"name": "Medicamentos Pet", "type": "Despesa", "parent": "Pets"},
        
        {"name": "Vestuário", "type": "Despesa"},
        {"name": "Roupas", "type": "Despesa", "parent": "Vestuário"},
        {"name": "Calçados", "type": "Despesa", "parent": "Vestuário"},
        {"name": "Acessórios", "type": "Despesa", "parent": "Vestuário"},
        {"name": "Roupas Íntimas", "type": "Despesa", "parent": "Vestuário"},
        {"name": "Roupas de Trabalho", "type": "Despesa", "parent": "Vestuário"},
        
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
        {"name": "Plano Odontológico", "type": "Despesa", "parent": "Saúde"},
        
        {"name": "Transporte", "type": "Despesa"},
        {"name": "Combustível", "type": "Despesa", "parent": "Transporte"},
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
        
        {"name": "Educação", "type": "Despesa"},
        {"name": "Mensalidade Escolar", "type": "Despesa", "parent": "Educação"},
        {"name": "Mensalidade Universitária", "type": "Despesa", "parent": "Educação"},
        {"name": "Faculdade", "type": "Despesa", "parent": "Educação"},
        {"name": "Cursos Livres/Idiomas", "type": "Despesa", "parent": "Educação"},
        {"name": "Cursos", "type": "Despesa", "parent": "Educação"},
        {"name": "Material Escolar", "type": "Despesa", "parent": "Educação"},
        {"name": "Livros", "type": "Despesa", "parent": "Educação"},
        {"name": "Pós-graduação", "type": "Despesa", "parent": "Educação"},
        {"name": "Seminário", "type": "Despesa", "parent": "Educação"},
        {"name": "ETAAD", "type": "Despesa", "parent": "Educação"},
        
        {"name": "Trabalho", "type": "Despesa"},
        {"name": "Material de Escritório", "type": "Despesa", "parent": "Trabalho"},
        {"name": "Software/Licenças", "type": "Despesa", "parent": "Trabalho"},
        {"name": "Equipamentos de Trabalho", "type": "Despesa", "parent": "Trabalho"},
        {"name": "Cursos Profissionais", "type": "Despesa", "parent": "Trabalho"},
        {"name": "Hospedagem Trabalho", "type": "Despesa", "parent": "Trabalho"},
        
        {"name": "Lazer", "type": "Despesa"},
        {"name": "Cinema", "type": "Despesa", "parent": "Lazer"},
        {"name": "Teatro", "type": "Despesa", "parent": "Lazer"},
        {"name": "Shows", "type": "Despesa", "parent": "Lazer"},
        {"name": "Eventos Esportivos", "type": "Despesa", "parent": "Lazer"},
        {"name": "Viagens (Passagens)", "type": "Despesa", "parent": "Lazer"},
        {"name": "Viagens (Hospedagem)", "type": "Despesa", "parent": "Lazer"},
        {"name": "Viagens (Passeios)", "type": "Despesa", "parent": "Lazer"},
        {"name": "Jogos", "type": "Despesa", "parent": "Lazer"},
        {"name": "Hobbies", "type": "Despesa", "parent": "Lazer"},
        {"name": "Festas/Eventos Sociais", "type": "Despesa", "parent": "Lazer"},
        
        {"name": "Doações", "type": "Despesa"},
        {"name": "Caridade", "type": "Despesa", "parent": "Doações"},
        {"name": "Dízimo", "type": "Despesa", "parent": "Doações"},
        {"name": "Contribuições", "type": "Despesa", "parent": "Doações"},
        
        {"name": "Eletrodomésticos", "type": "Despesa"},
        {"name": "Geladeira", "type": "Despesa", "parent": "Eletrodomésticos"},
        {"name": "Fogão", "type": "Despesa", "parent": "Eletrodomésticos"},
        {"name": "Micro-ondas", "type": "Despesa", "parent": "Eletrodomésticos"},
        {"name": "Máquina de Lavar", "type": "Despesa", "parent": "Eletrodomésticos"},
        {"name": "Ar Condicionado", "type": "Despesa", "parent": "Eletrodomésticos"},
        {"name": "Ventilador", "type": "Despesa", "parent": "Eletrodomésticos"},
        {"name": "TV", "type": "Despesa", "parent": "Eletrodomésticos"},
        {"name": "Eletrônicos", "type": "Despesa", "parent": "Eletrodomésticos"},
        
        {"name": "Assinaturas", "type": "Despesa"},
        {"name": "Netflix", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "Spotify", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "Prime Video", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "Globoplay", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "Microsoft", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "CapCut", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "Google One", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "Adobe", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "YouTube Premium", "type": "Despesa", "parent": "Assinaturas"},
        {"name": "iCloud", "type": "Despesa", "parent": "Assinaturas"},
        
        {"name": "Investimentos", "type": "Despesa"},
        {"name": "Aplicações Financeiras", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Compra de Ações", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Fundos de Investimento", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Poupança Programada", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Custos de Corretagem", "type": "Despesa", "parent": "Investimentos"},
        {"name": "CDB/LCI/LCA", "type": "Despesa", "parent": "Investimentos"},
        {"name": "Tesouro Direto", "type": "Despesa", "parent": "Investimentos"},
        
        {"name": "Cartão", "type": "Despesa"},
        {"name": "Fatura do Cartão de Crédito", "type": "Despesa", "parent": "Cartão"},
        {"name": "Anuidade Cartão", "type": "Despesa", "parent": "Cartão"},
        {"name": "Juros do Cartão", "type": "Despesa", "parent": "Cartão"},
        {"name": "IOF Cartão", "type": "Despesa", "parent": "Cartão"},
        
        {"name": "Dívidas", "type": "Despesa"},
        {"name": "Empréstimos Pessoais", "type": "Despesa", "parent": "Dívidas"},
        {"name": "Financiamento de Veículo", "type": "Despesa", "parent": "Dívidas"},
        {"name": "Financiamento Imobiliário", "type": "Despesa", "parent": "Dívidas"},
        {"name": "Juros de Dívidas", "type": "Despesa", "parent": "Dívidas"},
        {"name": "Cheque Especial", "type": "Despesa", "parent": "Dívidas"},
        {"name": "Crediário", "type": "Despesa", "parent": "Dívidas"},
        
        {"name": "Energia", "type": "Despesa"},
        {"name": "Luz", "type": "Despesa", "parent": "Energia"},
        {"name": "Taxa de Iluminação Pública", "type": "Despesa", "parent": "Energia"},
        {"name": "Bandeira Tarifária", "type": "Despesa", "parent": "Energia"},
        
        {"name": "Água", "type": "Despesa"},
        {"name": "Conta de Água", "type": "Despesa", "parent": "Água"},
        {"name": "Taxa de Esgoto", "type": "Despesa", "parent": "Água"},
        
        {"name": "Internet", "type": "Despesa"},
        {"name": "Internet Residencial", "type": "Despesa", "parent": "Internet"},
        {"name": "Internet Móvel", "type": "Despesa", "parent": "Internet"},
        {"name": "Wi-Fi", "type": "Despesa", "parent": "Internet"},
        
        {"name": "Celular", "type": "Despesa"},
        {"name": "Conta do Celular", "type": "Despesa", "parent": "Celular"},
        {"name": "Recarga", "type": "Despesa", "parent": "Celular"},
        {"name": "Aparelho Celular", "type": "Despesa", "parent": "Celular"},
        {"name": "Capas e Acessórios", "type": "Despesa", "parent": "Celular"},
        
        {"name": "Seguro", "type": "Despesa"},
        {"name": "Seguro Residencial", "type": "Despesa", "parent": "Seguro"},
        {"name": "Seguro de Vida", "type": "Despesa", "parent": "Seguro"},
        {"name": "Seguro Celular", "type": "Despesa", "parent": "Seguro"},
        {"name": "Seguro Viagem", "type": "Despesa", "parent": "Seguro"},
        
        {"name": "Agropecuária", "type": "Despesa"},
        {"name": "Sementes", "type": "Despesa", "parent": "Agropecuária"},
        {"name": "Fertilizantes", "type": "Despesa", "parent": "Agropecuária"},
        {"name": "Defensivos", "type": "Despesa", "parent": "Agropecuária"},
        {"name": "Equipamentos Agrícolas", "type": "Despesa", "parent": "Agropecuária"},
        {"name": "Ração Animal", "type": "Despesa", "parent": "Agropecuária"},
        
        # CATEGORIAS GERAIS COMPLEMENTARES
        {"name": "Moradia", "type": "Despesa"},
        {"name": "Aluguel", "type": "Despesa", "parent": "Moradia"},
        {"name": "Condomínio", "type": "Despesa", "parent": "Moradia"},
        {"name": "IPTU", "type": "Despesa", "parent": "Moradia"},
        {"name": "Gás", "type": "Despesa", "parent": "Moradia"},
        {"name": "Telefone Fixo", "type": "Despesa", "parent": "Moradia"},
        {"name": "Manutenção e Reparos", "type": "Despesa", "parent": "Moradia"},
        
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
        
        {"name": "Impostos e Taxas", "type": "Despesa"},
        {"name": "Imposto de Renda", "type": "Despesa", "parent": "Impostos e Taxas"},
        {"name": "Taxas Bancárias", "type": "Despesa", "parent": "Impostos e Taxas"},
        {"name": "Contribuição Sindical", "type": "Despesa", "parent": "Impostos e Taxas"},
        {"name": "Taxas de Condomínio Extras", "type": "Despesa", "parent": "Impostos e Taxas"},
        {"name": "ISS", "type": "Despesa", "parent": "Impostos e Taxas"},
        {"name": "COFINS", "type": "Despesa", "parent": "Impostos e Taxas"},
        
        # CATEGORIA OUTROS PARA FLEXIBILIDADE
        {"name": "Outros", "type": "Despesa"}
    ]
    
    print(f"[DEBUG] Total COMPLETE categories defined: {len(default_categories)}")
    
    try:
        # Create parent categories first
        parent_categories = {}
        categories_to_insert = []
        
        parent_count = 0
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
                parent_count += 1
        
        print(f"[DEBUG] COMPLETE Parent categories to insert: {parent_count}")
        
        # Insert parent categories in batches
        if categories_to_insert:
            try:
                result = await db.categories.insert_many(categories_to_insert)
                print(f"[DEBUG] COMPLETE Parent categories inserted successfully: {len(result.inserted_ids)}")
            except Exception as e:
                print(f"[ERROR] Failed to insert parent categories: {e}")
                return False
        
        # Create subcategories
        subcategories_to_insert = []
        subcategory_count = 0
        
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
                    subcategory_count += 1
                else:
                    print(f"[WARNING] Parent not found for {cat_data['name']} -> {cat_data['parent']}")
        
        print(f"[DEBUG] COMPLETE Subcategories to insert: {subcategory_count}")
        
        # Insert subcategories in batches
        if subcategories_to_insert:
            try:
                result = await db.categories.insert_many(subcategories_to_insert)
                print(f"[DEBUG] COMPLETE Subcategories inserted successfully: {len(result.inserted_ids)}")
            except Exception as e:
                print(f"[ERROR] Failed to insert subcategories: {e}")
                return False
        
        print(f"[DEBUG] COMPLETE Brazilian categories creation completed successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] COMPLETE Category creation failed: {e}")
        return False

# Endpoint to migrate existing users to complete categories
@api_router.post("/admin/migrate-user-categories/{user_id}")
async def migrate_user_categories(user_id: str, current_user: User = Depends(get_current_user)):
    """
    ADMIN ENDPOINT: Migrate existing user to complete 129 categories system
    This fixes the issue where existing users have only 42/129 categories
    """
    # Security check - only allow self-migration for now (or admin check)
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to migrate other users")
    
    print(f"[MIGRATION] Starting category migration for user: {user_id}")
    
    try:
        # Delete existing categories for this user (except custom ones)
        delete_result = await db.categories.delete_many({
            "user_id": user_id,
            "is_custom": {"$ne": True}
        })
        
        print(f"[MIGRATION] Deleted {delete_result.deleted_count} existing system categories")
        
        # Create fresh complete categories
        migration_success = await create_default_categories(user_id)
        
        if migration_success:
            # Count new categories
            new_categories = await db.categories.find({"user_id": user_id}).to_list(200)
            
            print(f"[MIGRATION] Created {len(new_categories)} new categories")
            
            return {
                "message": "Migração de categorias concluída com sucesso!",
                "deleted_old_categories": delete_result.deleted_count,
                "created_new_categories": len(new_categories),
                "migration_successful": True
            }
        else:
            raise Exception("Category creation failed during migration")
            
    except Exception as e:
        print(f"[MIGRATION ERROR] Failed to migrate categories: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

# Helper function to update budget spent amount
async def update_budget_spent(user_id: str, category_id: str, month_year: str, amount: float):
    await db.budgets.update_one(
        {"user_id": user_id, "category_id": category_id, "month_year": month_year},
        {"$inc": {"spent_amount": amount}},
        upsert=False
    )

# ============================================================================
# 🏠 CONTRACT HELPER FUNCTIONS - PHASE 2
# ============================================================================

def calculate_contract_totals(contract: dict) -> dict:
    """
    Calcula valores totais do contrato incluindo juros, taxa administrativa e seguro
    """
    parcelas_restantes = contract["quantidade_parcelas"] - contract["parcela_atual"]
    juros_acumulado = contract["parcela_mensal"] * contract["juros_mensal"] / 100 * contract["parcela_atual"]
    
    valor_total_pago = contract["parcela_mensal"] * contract["parcela_atual"]
    valor_total_final = (contract["parcela_mensal"] * contract["quantidade_parcelas"] + 
                        contract["taxa_administrativa"] + 
                        contract["seguro"])
    valor_restante = valor_total_final - valor_total_pago
    
    return {
        "valor_total_pago": valor_total_pago,
        "valor_total_final": valor_total_final,
        "valor_restante": valor_restante,
        "parcelas_restantes": parcelas_restantes,
        "juros_acumulado": juros_acumulado,
        "progresso_percentual": (contract["parcela_atual"] / contract["quantidade_parcelas"]) * 100
    }

def check_contract_status(contract: dict) -> str:
    """
    Verifica e atualiza automaticamente o status do contrato
    """
    if contract["parcela_atual"] >= contract["quantidade_parcelas"]:
        return "quitado"
    elif contract["status"] == "cancelado":
        return "cancelado"
    else:
        return "ativo"

async def update_contract_status(contract_id: str, user_id: str):
    """
    Atualiza o status do contrato baseado nas regras de negócio
    """
    contract = await db.contracts.find_one({"id": contract_id, "user_id": user_id})
    if contract:
        new_status = check_contract_status(contract)
        if new_status != contract["status"]:
            await db.contracts.update_one(
                {"id": contract_id, "user_id": user_id},
                {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
            )
    return new_status

# ============================================================================
# 🐾 PET SHOP HELPER FUNCTIONS - PHASE 3
# ============================================================================

def generate_receipt_number():
    """
    Gera número único para comprovante de venda
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:4].upper()
    return f"PS{timestamp}{random_suffix}"

async def update_product_stock(product_id: str, user_id: str, quantity_sold: int, reason: str = "venda"):
    """
    Atualiza estoque do produto e registra movimentação
    """
    product = await db.products.find_one({"id": product_id, "user_id": user_id})
    if not product:
        raise ValueError("Produto não encontrado")
    
    previous_stock = product["current_stock"]
    new_stock = previous_stock - quantity_sold
    
    if new_stock < 0:
        raise ValueError(f"Estoque insuficiente. Disponível: {previous_stock}, Solicitado: {quantity_sold}")
    
    # Atualizar estoque do produto
    await db.products.update_one(
        {"id": product_id, "user_id": user_id},
        {"$set": {"current_stock": new_stock, "updated_at": datetime.utcnow()}}
    )
    
    # Registrar movimentação de estoque
    movement = StockMovement(
        user_id=user_id,
        product_id=product_id,
        movement_type="saída",
        quantity=quantity_sold,
        reason=reason,
        previous_stock=previous_stock,
        new_stock=new_stock,
        created_by=user_id
    )
    
    await db.stock_movements.insert_one(movement.dict())
    
    return new_stock

async def check_low_stock_products(user_id: str):
    """
    Verifica produtos com estoque baixo
    """
    products = await db.products.find({
        "user_id": user_id,
        "is_active": True,
        "$expr": {"$lte": ["$current_stock", "$minimum_stock"]}
    }).to_list(100)
    
    # Remove MongoDB ObjectId fields for JSON serialization
    for product in products:
        if "_id" in product:
            del product["_id"]
    
    return products

async def create_financial_transaction_from_sale(sale: dict, user_id: str):
    """
    Cria transação financeira automática a partir de venda do pet shop
    """
    # Buscar conta padrão ou primeira conta ativa
    account = await db.accounts.find_one({
        "user_id": user_id,
        "type": {"$ne": "Cartão de Crédito"}
    })
    
    if not account:
        raise ValueError("Nenhuma conta encontrada para registrar a venda")
    
    # Buscar categoria "Pet Shop" ou criar se não existir
    category = await db.categories.find_one({
        "user_id": user_id,
        "name": "Pet Shop"
    })
    
    if not category:
        # Criar categoria Pet Shop
        pet_shop_category = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "Pet Shop",
            "type": "Receita",
            "parent": None,
            "created_at": datetime.utcnow()
        }
        await db.categories.insert_one(pet_shop_category)
        category = pet_shop_category
    
    # Criar transação financeira
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "account_id": account["id"],
        "category_id": category["id"],
        "type": "Receita",
        "description": f"Venda Pet Shop - {sale['receipt_number']}",
        "value": sale["total"],
        "transaction_date": sale["sale_date"],
        "status": "Pago",
        "payment_method": sale["payment_method"],
        "notes": f"Venda automática do Pet Shop. Items: {len(sale['items'])} produto(s)",
        "created_at": datetime.utcnow(),
        "recurring": False
    }
    
    await db.transactions.insert_one(transaction)
    
    # Atualizar saldo da conta
    await db.accounts.update_one(
        {"id": account["id"]},
        {"$inc": {"current_balance": sale["total"]}}
    )
    
    return transaction["id"]

# Test endpoint for authentication debugging
@api_router.get("/test/auth", response_model=Dict[str, Any])
async def test_auth(current_user: User = Depends(get_current_user)):
    """Test authentication endpoint"""
    return {
        "message": "Authentication working!",
        "user_id": current_user.id,
        "user_email": current_user.email,
        "user_name": current_user.name
    }

# Test endpoint for account deletion
@api_router.delete("/test/delete-account/{account_id}")
async def test_delete_account(account_id: str, current_user: User = Depends(get_current_user)):
    """Test delete account endpoint"""
    return {
        "message": "Delete endpoint working!",
        "account_id": account_id,
        "user_id": current_user.id
    }

# ============================================================================
# 🧠 SISTEMA DE CATEGORIZAÇÃO INTELIGENTE HIERÁRQUICA
# ============================================================================

@api_router.post("/categories/upgrade-hierarchical")
async def upgrade_to_hierarchical_categories(current_user: User = Depends(get_current_user)):
    """Upgrade user's categories to hierarchical Brazilian standard"""
    try:
        # Clear existing categories
        await db.categories.delete_many({"user_id": current_user.id})
        
        # Create new hierarchical categories
        await create_brazilian_hierarchical_categories(current_user.id)
        
        return {"message": "Categorias hierárquicas criadas com sucesso", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar categorias: {str(e)}")

@api_router.get("/categories/hierarchical", response_model=List[Dict[str, Any]])
async def get_hierarchical_categories(current_user: User = Depends(get_current_user)):
    """Get categories organized hierarchically"""
    try:
        # Get all categories
        categories = await db.categories.find({"user_id": current_user.id}).to_list(1000)
        
        # Organize into hierarchy
        main_categories = []
        subcategories_map = defaultdict(list)
        
        for cat in categories:
            if not cat.get("parent_category_id"):
                main_categories.append(cat)
            else:
                subcategories_map[cat["parent_category_id"]].append(cat)
        
        # Build hierarchical structure
        hierarchical = []
        for main_cat in main_categories:
            cat_data = {
                **main_cat,
                "subcategories": subcategories_map.get(main_cat["id"], [])
            }
            hierarchical.append(cat_data)
        
        return hierarchical
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar categorias: {str(e)}")

@api_router.post("/categories/ai-classify")
async def ai_classify_transaction_category(
    transaction_data: Dict[str, str], 
    current_user: User = Depends(get_current_user)
):
    """AI-powered category classification"""
    try:
        description = transaction_data.get("description", "").lower()
        amount = transaction_data.get("amount", 0)
        
        # Get user's categories
        categories = await db.categories.find({"user_id": current_user.id}).to_list(1000)
        
        # Advanced AI classification logic
        best_match = None
        highest_score = 0
        
        for category in categories:
            score = 0
            keywords = category.get("keywords", [])
            
            # Keyword matching
            for keyword in keywords:
                if keyword.lower() in description:
                    score += 10
                    
            # Partial matching
            for keyword in keywords:
                if any(word in keyword.lower() for word in description.split()):
                    score += 5
            
            # Usage frequency bonus
            score += category.get("usage_count", 0) * 0.1
            
            if score > highest_score:
                highest_score = score
                best_match = category
        
        # Confidence calculation
        confidence = min(highest_score / 10, 1.0)  # Cap at 100%
        
        return {
            "suggested_category": best_match,
            "confidence": confidence,
            "explanation": f"Baseado em palavras-chave e histórico de uso"
        }
        
    except Exception as e:
        return {"error": str(e), "suggested_category": None, "confidence": 0.0}

@api_router.post("/categories/custom")
async def create_custom_category(
    category_data: Dict[str, Any], 
    current_user: User = Depends(get_current_user)
):
    """Create custom user category"""
    try:
        category = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "name": category_data["name"],
            "type": category_data["type"],
            "parent_category_id": category_data.get("parent_category_id"),
            "parent_category_name": category_data.get("parent_category_name"),
            "icon": category_data.get("icon", "📁"),
            "color": category_data.get("color", "#6B7280"),
            "keywords": category_data.get("keywords", []),
            "is_custom": True,
            "is_active": True,
            "usage_count": 0,
            "created_at": datetime.utcnow()
        }
        
        await db.categories.insert_one(category)
        
        return {"message": "Categoria personalizada criada", "category": Category(**category)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar categoria: {str(e)}")

async def create_brazilian_hierarchical_categories(user_id: str):
    """Create comprehensive Brazilian hierarchical categories"""
    
    # Check if categories already exist
    existing_count = await db.categories.count_documents({"user_id": user_id})
    if existing_count > 0:
        return False  # Categories already exist
    
    categories_data = [
        # 🏠 1. MORADIA / CASA
        {"name": "Moradia", "type": "Despesa", "icon": "🏠", "color": "#10B981", "keywords": ["casa", "moradia", "lar", "residencia"]},
        {"name": "Aluguel", "type": "Despesa", "parent": "Moradia", "keywords": ["aluguel", "locação", "imobiliaria"]},
        {"name": "Condomínio", "type": "Despesa", "parent": "Moradia", "keywords": ["condominio", "administração", "taxa condominial"]},
        {"name": "Financiamento Imobiliário", "type": "Despesa", "parent": "Moradia", "keywords": ["financiamento", "casa propria", "habitação", "sac", "price"]},
        {"name": "Energia Elétrica", "type": "Despesa", "parent": "Moradia", "keywords": ["energia", "eletrica", "luz", "cepe", "cpfl", "cemig"]},
        {"name": "Água / Esgoto", "type": "Despesa", "parent": "Moradia", "keywords": ["agua", "esgoto", "sabesp", "saneamento"]},
        {"name": "Gás", "type": "Despesa", "parent": "Moradia", "keywords": ["gas", "butano", "comgas", "botijão"]},
        {"name": "IPTU", "type": "Despesa", "parent": "Moradia", "keywords": ["iptu", "imposto territorial", "prefeitura"]},
        {"name": "Reforma / Manutenção", "type": "Despesa", "parent": "Moradia", "keywords": ["reforma", "manutenção", "conserto", "pintura", "eletricista", "encanador"]},
        {"name": "Seguro Residencial", "type": "Despesa", "parent": "Moradia", "keywords": ["seguro residencial", "seguro casa", "proteção residencial"]},
        
        # 🚗 2. TRANSPORTE
        {"name": "Transporte", "type": "Despesa", "icon": "🚗", "color": "#3B82F6", "keywords": ["transporte", "veiculo", "carro", "moto"]},
        {"name": "Combustível", "type": "Despesa", "parent": "Transporte", "keywords": ["combustivel", "gasolina", "alcool", "etanol", "diesel", "posto", "shell", "petrobras"]},
        {"name": "Manutenção do veículo", "type": "Despesa", "parent": "Transporte", "keywords": ["manutenção", "mecanico", "oficina", "revisão", "pneu", "oleo"]},
        {"name": "Financiamento de carro", "type": "Despesa", "parent": "Transporte", "keywords": ["financiamento", "prestação", "carro", "veiculo"]},
        {"name": "IPVA / DPVAT", "type": "Despesa", "parent": "Transporte", "keywords": ["ipva", "dpvat", "imposto veiculo", "licenciamento"]},
        {"name": "Transporte público", "type": "Despesa", "parent": "Transporte", "keywords": ["onibus", "metro", "trem", "passagem", "bilhete unico", "cartão transporte"]},
        {"name": "Pedágios / Estacionamentos", "type": "Despesa", "parent": "Transporte", "keywords": ["pedagio", "estacionamento", "sem parar", "conectcar"]},
        {"name": "Seguro de automóvel", "type": "Despesa", "parent": "Transporte", "keywords": ["seguro auto", "seguro carro", "seguro veiculo"]},
        {"name": "Consórcio de veículo", "type": "Despesa", "parent": "Transporte", "keywords": ["consorcio", "carro", "veiculo", "moto"]},
        
        # 🍕 3. ALIMENTAÇÃO
        {"name": "Alimentação", "type": "Despesa", "icon": "🍕", "color": "#F59E0B", "keywords": ["alimentação", "comida", "refeição"]},
        {"name": "Supermercado", "type": "Despesa", "parent": "Alimentação", "keywords": ["supermercado", "mercado", "compras", "carrefour", "extra", "pao acucar"]},
        {"name": "Feira", "type": "Despesa", "parent": "Alimentação", "keywords": ["feira", "verduras", "frutas", "legumes", "sacolão"]},
        {"name": "Restaurante / Lanchonete", "type": "Despesa", "parent": "Alimentação", "keywords": ["restaurante", "lanchonete", "ifood", "uber eats", "delivery"]},
        {"name": "Marmita", "type": "Despesa", "parent": "Alimentação", "keywords": ["marmita", "quentinha", "almoço", "janta"]},
        
        # 🏥 4. SAÚDE
        {"name": "Saúde", "type": "Despesa", "icon": "🏥", "color": "#EF4444", "keywords": ["saude", "medico", "hospital", "clinica"]},
        {"name": "Plano de Saúde", "type": "Despesa", "parent": "Saúde", "keywords": ["plano saude", "convenio", "unimed", "sulamerica", "bradesco saude"]},
        {"name": "Medicamentos", "type": "Despesa", "parent": "Saúde", "keywords": ["medicamento", "remedio", "farmacia", "drogaria", "droga raia"]},
        {"name": "Consultas / Exames", "type": "Despesa", "parent": "Saúde", "keywords": ["consulta", "exame", "medico", "laboratorio"]},
        {"name": "Terapias / Psicólogo", "type": "Despesa", "parent": "Saúde", "keywords": ["terapia", "psicologo", "fisioterapia", "psicanalise"]},
        {"name": "Odontologia", "type": "Despesa", "parent": "Saúde", "keywords": ["dentista", "odontologia", "ortodontia", "aparelho"]},
        
        # 🎓 5. EDUCAÇÃO
        {"name": "Educação", "type": "Despesa", "icon": "🎓", "color": "#8B5CF6", "keywords": ["educação", "escola", "faculdade", "curso"]},
        {"name": "Mensalidade Escolar / Faculdade", "type": "Despesa", "parent": "Educação", "keywords": ["mensalidade", "escola", "faculdade", "universidade", "colegio"]},
        {"name": "Cursos Livres", "type": "Despesa", "parent": "Educação", "keywords": ["curso", "treinamento", "certificação", "idioma", "ingles"]},
        {"name": "Livros / Material Didático", "type": "Despesa", "parent": "Educação", "keywords": ["livro", "material escolar", "caderno", "apostila"]},
        {"name": "Seminário / ETAAD", "type": "Despesa", "parent": "Educação", "keywords": ["seminario", "etaad", "congresso", "evento"]},
        {"name": "Crianças", "type": "Despesa", "parent": "Educação", "keywords": ["creche", "reforço", "babá", "cuidador"]},
        
        # 🐕 6. PETS
        {"name": "Pets", "type": "Despesa", "icon": "🐕", "color": "#06B6D4", "keywords": ["pet", "animal", "cachorro", "gato"]},
        {"name": "Ração", "type": "Despesa", "parent": "Pets", "keywords": ["ração", "comida pet", "alimento animal"]},
        {"name": "Banho e Tosa", "type": "Despesa", "parent": "Pets", "keywords": ["banho", "tosa", "pet shop", "grooming"]},
        {"name": "Veterinário", "type": "Despesa", "parent": "Pets", "keywords": ["veterinario", "vacina", "consulta pet", "clinica veterinaria"]},
        {"name": "Acessórios", "type": "Despesa", "parent": "Pets", "keywords": ["coleira", "brinquedo", "caminha", "acessorio pet"]},
        
        # 💼 7. TRABALHO / PROFISSIONAL
        {"name": "Trabalho", "type": "Despesa", "icon": "💼", "color": "#374151", "keywords": ["trabalho", "profissional", "carreira"]},
        {"name": "Assinaturas", "type": "Despesa", "parent": "Trabalho", "keywords": ["capcut", "canva", "microsoft", "adobe", "assinatura"]},
        {"name": "Cursos / Certificados", "type": "Despesa", "parent": "Trabalho", "keywords": ["certificação", "curso profissional", "especialização"]},
        {"name": "Equipamentos de trabalho", "type": "Despesa", "parent": "Trabalho", "keywords": ["equipamento", "ferramenta", "notebook", "impressora"]},
        {"name": "Marketing / Publicidade", "type": "Despesa", "parent": "Trabalho", "keywords": ["marketing", "publicidade", "ads", "propaganda"]},
        
        # 🛍️ 8. DESPESAS PESSOAIS
        {"name": "Despesas Pessoais", "type": "Despesa", "icon": "🛍️", "color": "#EC4899", "keywords": ["pessoal", "individual", "proprio"]},
        {"name": "Celular", "type": "Despesa", "parent": "Despesas Pessoais", "keywords": ["celular", "telefone", "vivo", "claro", "tim", "oi"]},
        {"name": "Internet", "type": "Despesa", "parent": "Despesas Pessoais", "keywords": ["internet", "banda larga", "wifi", "net", "claro", "vivo fibra"]},
        {"name": "Streaming", "type": "Despesa", "parent": "Despesas Pessoais", "keywords": ["netflix", "spotify", "amazon prime", "disney", "streaming"]},
        {"name": "Vestuário / Calçados", "type": "Despesa", "parent": "Despesas Pessoais", "keywords": ["roupa", "calçado", "sapato", "vestido", "camisa"]},
        {"name": "Cabelo / Barbeiro / Estética", "type": "Despesa", "parent": "Despesas Pessoais", "keywords": ["cabelo", "barbeiro", "salão", "estetica", "manicure"]},
        {"name": "Presentes", "type": "Despesa", "parent": "Despesas Pessoais", "keywords": ["presente", "gift", "aniversario", "natal"]},
        
        # 🎪 9. LAZER
        {"name": "Lazer", "type": "Despesa", "icon": "🎪", "color": "#F97316", "keywords": ["lazer", "entretenimento", "diversão"]},
        {"name": "Viagens", "type": "Despesa", "parent": "Lazer", "keywords": ["viagem", "hotel", "passagem", "turismo", "ferias"]},
        {"name": "Passeios", "type": "Despesa", "parent": "Lazer", "keywords": ["passeio", "parque", "zoologico", "shopping"]},
        {"name": "Cinema / Teatro / Shows", "type": "Despesa", "parent": "Lazer", "keywords": ["cinema", "teatro", "show", "concerto", "ingresso"]},
        {"name": "Hobbies / Games", "type": "Despesa", "parent": "Lazer", "keywords": ["hobby", "game", "jogo", "playstation", "xbox"]},
        
        # ❤️ 10. DOAÇÕES / AJUDA
        {"name": "Doações", "type": "Despesa", "icon": "❤️", "color": "#DC2626", "keywords": ["doação", "ajuda", "caridade", "solidariedade"]},
        {"name": "Ofertas / Dízimos", "type": "Despesa", "parent": "Doações", "keywords": ["oferta", "dizimo", "igreja", "religioso"]},
        {"name": "Doações a pessoas", "type": "Despesa", "parent": "Doações", "keywords": ["doação", "ajuda", "pessoa", "familia"]},
        {"name": "Ajuda emergencial", "type": "Despesa", "parent": "Doações", "keywords": ["emergencia", "urgente", "socorro", "ajuda"]},
        
        # 📈 11. INVESTIMENTOS / PATRIMÔNIO
        {"name": "Investimentos", "type": "Despesa", "icon": "📈", "color": "#059669", "keywords": ["investimento", "patrimonio", "aplicação"]},
        {"name": "Poupança", "type": "Despesa", "parent": "Investimentos", "keywords": ["poupança", "caderneta", "savings"]},
        {"name": "Tesouro Direto / Renda Fixa", "type": "Despesa", "parent": "Investimentos", "keywords": ["tesouro", "renda fixa", "cdb", "lci"]},
        {"name": "Ações / Fundos", "type": "Despesa", "parent": "Investimentos", "keywords": ["ação", "fundo", "bolsa", "b3", "stock"]},
        {"name": "Compra de imóvel", "type": "Despesa", "parent": "Investimentos", "keywords": ["imovel", "casa", "apartamento", "terreno"]},
        {"name": "Compra de veículo", "type": "Despesa", "parent": "Investimentos", "keywords": ["carro", "veiculo", "moto", "compra"]},
        {"name": "Consórcio Imobiliário", "type": "Despesa", "parent": "Investimentos", "keywords": ["consorcio", "imovel", "casa", "apartamento"]},
        {"name": "Aportes em Consórcios", "type": "Despesa", "parent": "Investimentos", "keywords": ["aporte", "consorcio", "lance"]},
        
        # 💸 12. IMPOSTOS / ENCARGOS
        {"name": "Impostos", "type": "Despesa", "icon": "💸", "color": "#991B1B", "keywords": ["imposto", "taxa", "encargo", "governo"]},
        {"name": "INSS / GPS", "type": "Despesa", "parent": "Impostos", "keywords": ["inss", "gps", "previdencia", "contribuição"]},
        {"name": "IRPF", "type": "Despesa", "parent": "Impostos", "keywords": ["irpf", "imposto renda", "receita federal"]},
        {"name": "Tarifas bancárias", "type": "Despesa", "parent": "Impostos", "keywords": ["tarifa", "banco", "manutenção conta", "anuidade"]},
        {"name": "Multas", "type": "Despesa", "parent": "Impostos", "keywords": ["multa", "infração", "transito"]},
        
        # 💳 13. DÍVIDAS / PARCELAMENTOS
        {"name": "Dívidas", "type": "Despesa", "icon": "💳", "color": "#7C2D12", "keywords": ["divida", "debito", "parcelamento", "pagamento"]},
        {"name": "Cartão de Crédito", "type": "Despesa", "parent": "Dívidas", "keywords": ["cartão", "credito", "fatura", "visa", "master"]},
        {"name": "Renegociação / Acordo", "type": "Despesa", "parent": "Dívidas", "keywords": ["renegociação", "acordo", "quitação", "divida"]},
        {"name": "Empréstimo Pessoal", "type": "Despesa", "parent": "Dívidas", "keywords": ["emprestimo", "financeira", "crediario"]},
        {"name": "Parcelamentos diversos", "type": "Despesa", "parent": "Dívidas", "keywords": ["parcelamento", "prestação", "carnê"]},
        
        # 💰 14. RECEITAS
        {"name": "Receitas", "type": "Receita", "icon": "💰", "color": "#047857", "keywords": ["receita", "renda", "ganho", "entrada"]},
        {"name": "Salário", "type": "Receita", "parent": "Receitas", "keywords": ["salario", "ordenado", "vencimento", "pagamento"]},
        {"name": "Bicos / Freelance", "type": "Receita", "parent": "Receitas", "keywords": ["bico", "freelance", "extra", "trabalho extra"]},
        {"name": "13º salário", "type": "Receita", "parent": "Receitas", "keywords": ["13", "decimo terceiro", "gratificação"]},
        {"name": "Férias", "type": "Receita", "parent": "Receitas", "keywords": ["ferias", "terço constitucional"]},
        {"name": "Recebimentos de clientes", "type": "Receita", "parent": "Receitas", "keywords": ["cliente", "recebimento", "cobrança", "fatura"]},
        {"name": "Reembolsos", "type": "Receita", "parent": "Receitas", "keywords": ["reembolso", "estorno", "devolução"]},
        {"name": "Rendimentos financeiros", "type": "Receita", "parent": "Receitas", "keywords": ["rendimento", "juros", "dividendo", "yield"]},
    ]
    
    # Create categories with hierarchy
    category_map = {}  # Store category IDs by name for parent linking
    
    for cat_data in categories_data:
        # Create main categories first (those without parent)
        if "parent" not in cat_data:
            category = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": cat_data["name"],
                "type": cat_data["type"],
                "parent_category_id": None,
                "parent_category_name": None,
                "icon": cat_data.get("icon", "📁"),
                "color": cat_data.get("color", "#6B7280"),
                "keywords": cat_data.get("keywords", []),
                "is_custom": False,
                "is_active": True,
                "usage_count": 0,
                "created_at": datetime.utcnow()
            }
            
            await db.categories.insert_one(category)
            category_map[cat_data["name"]] = category["id"]
    
    # Now create subcategories
    for cat_data in categories_data:
        if "parent" in cat_data:
            parent_id = category_map.get(cat_data["parent"])
            if parent_id:
                category = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "name": cat_data["name"],
                    "type": cat_data["type"],
                    "parent_category_id": parent_id,
                    "parent_category_name": cat_data["parent"],
                    "icon": cat_data.get("icon", "📁"),
                    "color": cat_data.get("color", "#9CA3AF"),
                    "keywords": cat_data.get("keywords", []),
                    "is_custom": False,
                    "is_active": True,
                    "usage_count": 0,
                    "created_at": datetime.utcnow()
                }
                
                await db.categories.insert_one(category)
    
    return True

@api_router.post("/ai/chat", response_model=Dict[str, Any])
async def ai_chat(message_data: Dict[str, str], current_user: User = Depends(get_current_user)):
    """Chatbot conversacional com IA financeira"""
    try:
        user_message = message_data.get("message", "").lower()
        
        # Sistema de IA básico com respostas inteligentes
        if any(word in user_message for word in ["saldo", "quanto tenho"]):
            # Buscar saldo atual
            accounts = await db.accounts.find({"user_id": current_user.id}).to_list(100)
            total_balance = sum(acc.get("current_balance", 0) for acc in accounts)
            response = f"Seu saldo total consolidado é de R$ {total_balance:,.2f}. "
            
            if total_balance > 0:
                response += "Você está com saldo positivo! 👍"
            else:
                response += "Cuidado! Seu saldo está negativo. 💡 Que tal revisar seus gastos?"
            
        elif any(word in user_message for word in ["gastos", "despesas", "gastei"]):
            # Analisar gastos do mês
            month_start = datetime.now().replace(day=1)
            expenses = await db.transactions.find({
                "user_id": current_user.id,
                "type": "Despesa",
                "transaction_date": {"$gte": month_start.isoformat()}
            }).to_list(1000)
            
            total_expenses = sum(t.get("value", 0) for t in expenses)
            response = f"Seus gastos este mês totalizam R$ {total_expenses:,.2f}. "
            
            if len(expenses) > 0:
                # Categoria que mais gasta
                expense_by_category = defaultdict(float)
                for exp in expenses:
                    category = await db.categories.find_one({"id": exp.get("category_id")})
                    if category:
                        expense_by_category[category["name"]] += exp.get("value", 0)
                
                if expense_by_category:
                    top_category = max(expense_by_category, key=expense_by_category.get)
                    top_value = expense_by_category[top_category]
                    response += f"Sua maior despesa é em '{top_category}' (R$ {top_value:,.2f})."
            
        elif any(word in user_message for word in ["meta", "objetivo", "economia"]):
            # Informações sobre metas
            goals = await db.goals.find({"user_id": current_user.id, "is_active": True}).to_list(100)
            if goals:
                response = f"Você tem {len(goals)} meta(s) ativa(s). "
                for goal in goals[:2]:  # Mostrar até 2 metas
                    progress = (goal.get("current_amount", 0) / goal.get("target_amount", 1)) * 100
                    response += f"Meta '{goal['name']}': {progress:.1f}% concluída. "
            else:
                response = "Você ainda não tem metas definidas. Que tal criar uma meta de economia? 💰"
                
        elif any(word in user_message for word in ["previsão", "futuro", "próximo mês"]):
            # Previsão de saldo futuro
            monthly_income = await get_monthly_average_income(current_user.id)
            monthly_expense = await get_monthly_average_expense(current_user.id)
            
            accounts = await db.accounts.find({"user_id": current_user.id}).to_list(100)
            current_balance = sum(acc.get("current_balance", 0) for acc in accounts)
            
            predicted_balance = current_balance + monthly_income - monthly_expense
            
            response = f"Baseado no seu histórico, sua previsão para o próximo mês é: "
            response += f"Saldo atual: R$ {current_balance:,.2f}, "
            response += f"Entrada média: R$ {monthly_income:,.2f}, "
            response += f"Gasto médio: R$ {monthly_expense:,.2f}. "
            response += f"Saldo previsto: R$ {predicted_balance:,.2f}"
            
        else:
            # Resposta padrão inteligente
            response = "Olá! 🤖 Sou seu assistente financeiro. Posso te ajudar com:\n"
            response += "• Consultar saldo e transações\n"
            response += "• Analisar gastos por categoria\n"  
            response += "• Acompanhar suas metas\n"
            response += "• Fazer previsões financeiras\n"
            response += "• Dar dicas de economia\n\n"
            response += "O que você gostaria de saber?"
        
        # Salvar conversa no banco
        chat_message = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "message": message_data.get("message"),
            "response": response,
            "created_at": datetime.utcnow()
        }
        await db.chat_messages.insert_one(chat_message)
        
        return {"response": response, "success": True}
        
    except Exception as e:
        return {"response": f"Desculpe, ocorreu um erro: {str(e)}", "success": False}

@api_router.get("/ai/insights", response_model=List[Dict[str, Any]])
async def get_ai_insights(current_user: User = Depends(get_current_user)):
    """Gerar insights inteligentes baseados nos dados financeiros"""
    try:
        insights = []
        
        # Insight 1: Análise de gastos anômalos
        last_30_days = datetime.now() - timedelta(days=30)
        recent_transactions = await db.transactions.find({
            "user_id": current_user.id,
            "transaction_date": {"$gte": last_30_days.isoformat()}
        }).to_list(1000)
        
        if recent_transactions:
            amounts = [t.get("value", 0) for t in recent_transactions if t.get("type") == "Despesa"]
            if amounts:
                avg_expense = statistics.mean(amounts)
                max_expense = max(amounts)
                
                if max_expense > avg_expense * 2:  # Gasto 2x maior que a média
                    insights.append({
                        "type": "anomaly",
                        "category": "spending",
                        "title": "Gasto Anômalo Detectado",
                        "description": f"Você teve um gasto de R$ {max_expense:,.2f}, que é {max_expense/avg_expense:.1f}x maior que sua média de R$ {avg_expense:,.2f}",
                        "confidence": 0.85,
                        "actionable": True
                    })
        
        # Insight 2: Previsão de fim de mês
        monthly_income = await get_monthly_average_income(current_user.id)
        monthly_expense = await get_monthly_average_expense(current_user.id)
        
        if monthly_income > 0 and monthly_expense > 0:
            savings_rate = ((monthly_income - monthly_expense) / monthly_income) * 100
            
            if savings_rate < 10:
                insights.append({
                    "type": "suggestion",
                    "category": "savings", 
                    "title": "Taxa de Economia Baixa",
                    "description": f"Você está economizando apenas {savings_rate:.1f}% da sua renda. Tente economizar pelo menos 20%!",
                    "confidence": 0.75,
                    "actionable": True
                })
        
        # Insight 3: Categorias que mais crescem
        last_month = datetime.now() - timedelta(days=30)
        two_months_ago = datetime.now() - timedelta(days=60)
        
        current_month_expenses = await get_expenses_by_category(current_user.id, last_month)
        previous_month_expenses = await get_expenses_by_category(current_user.id, two_months_ago)
        
        for category, current_amount in current_month_expenses.items():
            previous_amount = previous_month_expenses.get(category, 0)
            if previous_amount > 0 and current_amount > previous_amount * 1.5:
                growth = ((current_amount - previous_amount) / previous_amount) * 100
                insights.append({
                    "type": "prediction",
                    "category": "spending",
                    "title": f"Crescimento em {category}",
                    "description": f"Seus gastos com {category} aumentaram {growth:.0f}% este mês (R$ {current_amount:,.2f})",
                    "confidence": 0.70,
                    "actionable": True
                })
        
        return insights[:5]  # Retornar no máximo 5 insights
        
    except Exception as e:
        return []

@api_router.post("/ai/predict-balance")
async def predict_balance(request: PredictionRequest, current_user: User = Depends(get_current_user)):
    """Prever saldo futuro baseado no histórico"""
    try:
        # Buscar histórico de transações
        days_back = min(request.days_ahead * 3, 90)  # Usar 3x o período ou máximo 90 dias
        start_date = datetime.now() - timedelta(days=days_back)
        
        transactions = await db.transactions.find({
            "user_id": current_user.id,
            "transaction_date": {"$gte": start_date.isoformat()}
        }).to_list(1000)
        
        # Calcular médias
        daily_income = []
        daily_expense = []
        
        for t in transactions:
            if t.get("type") == "Receita":
                daily_income.append(t.get("value", 0))
            else:
                daily_expense.append(t.get("value", 0))
        
        avg_daily_income = statistics.mean(daily_income) if daily_income else 0
        avg_daily_expense = statistics.mean(daily_expense) if daily_expense else 0
        
        # Saldo atual
        accounts = await db.accounts.find({"user_id": current_user.id}).to_list(100)
        current_balance = sum(acc.get("current_balance", 0) for acc in accounts)
        
        # Previsão
        predicted_income = avg_daily_income * request.days_ahead
        predicted_expense = avg_daily_expense * request.days_ahead
        predicted_balance = current_balance + predicted_income - predicted_expense
        
        return {
            "current_balance": current_balance,
            "predicted_balance": predicted_balance,
            "predicted_income": predicted_income,
            "predicted_expense": predicted_expense,
            "confidence": 0.75,
            "days_ahead": request.days_ahead
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na previsão: {str(e)}")

@api_router.post("/ai/classify-transaction")
async def classify_transaction(transaction_data: Dict[str, str], current_user: User = Depends(get_current_user)):
    """Classificar automaticamente categoria baseada na descrição"""
    try:
        description = transaction_data.get("description", "").lower()
        
        # Buscar categorias do usuário
        categories = await db.categories.find({"user_id": current_user.id}).to_list(200)
        
        # Regras de classificação inteligente
        classification_rules = {
            "alimentação": ["mercado", "supermercado", "padaria", "açougue", "ifood", "uber eats", "delivery"],
            "transporte": ["uber", "99", "taxi", "combustível", "gasolina", "posto", "estacionamento"],
            "saúde": ["farmácia", "droga", "hospital", "médico", "consulta", "exame"],
            "lazer": ["cinema", "teatro", "bar", "restaurante", "festa", "show"],
            "moradia": ["aluguel", "condomínio", "água", "luz", "energia", "internet", "telefone"],
            "netflix": ["netflix"],
            "spotify": ["spotify", "música"],
            "educação": ["faculdade", "curso", "escola", "livro", "material escolar"]
        }
        
        suggested_category = None
        confidence = 0.0
        
        for category_key, keywords in classification_rules.items():
            for keyword in keywords:
                if keyword in description:
                    # Encontrar categoria correspondente
                    matching_category = next((c for c in categories if category_key.lower() in c["name"].lower()), None)
                    if matching_category:
                        suggested_category = matching_category
                        confidence = 0.8
                        break
            if suggested_category:
                break
        
        return {
            "suggested_category": suggested_category,
            "confidence": confidence,
            "description_analyzed": transaction_data.get("description")
        }
        
    except Exception as e:
        return {"suggested_category": None, "confidence": 0.0, "error": str(e)}

# ============================================================================  
# 🏠 ENDPOINTS DE CONSÓRCIO
# ============================================================================

@api_router.post("/consortiums", response_model=Consortium)
async def create_consortium(consortium_data: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Criar novo consórcio"""
    try:
        # Calcular valores automáticos
        total_value = consortium_data.get("total_value", 0)
        installment_count = consortium_data.get("installment_count", 1)
        monthly_installment = total_value / installment_count if installment_count > 0 else 0
        
        consortium = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "name": consortium_data.get("name"),
            "type": consortium_data.get("type"),
            "total_value": total_value,
            "installment_count": installment_count,
            "paid_installments": consortium_data.get("paid_installments", 0),
            "monthly_installment": monthly_installment,
            "remaining_balance": total_value - (consortium_data.get("paid_installments", 0) * monthly_installment),
            "contemplated": consortium_data.get("contemplated", False),
            "contemplation_date": consortium_data.get("contemplation_date"),
            "bid_value": consortium_data.get("bid_value"),
            "status": consortium_data.get("status", "Ativo"),
            "due_day": consortium_data.get("due_day", 15),
            "start_date": datetime.fromisoformat(consortium_data.get("start_date")),
            "administrator": consortium_data.get("administrator"),
            "group_number": consortium_data.get("group_number"),
            "quota_number": consortium_data.get("quota_number"),
            "notes": consortium_data.get("notes"),
            "created_at": datetime.utcnow()
        }
        
        await db.consortiums.insert_one(consortium)
        return Consortium(**consortium)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar consórcio: {str(e)}")

@api_router.get("/consortiums", response_model=List[Consortium])
async def get_consortiums(current_user: User = Depends(get_current_user)):
    """Listar todos os consórcios do usuário"""
    consortiums = await db.consortiums.find({"user_id": current_user.id}).to_list(100)
    return [Consortium(**consortium) for consortium in consortiums]

@api_router.post("/consortiums/{consortium_id}/payment")
async def add_consortium_payment(consortium_id: str, payment_data: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Adicionar pagamento de parcela do consórcio"""
    try:
        # Verificar se consórcio existe
        consortium = await db.consortiums.find_one({"id": consortium_id, "user_id": current_user.id})
        if not consortium:
            raise HTTPException(status_code=404, detail="Consórcio não encontrado")
        
        # Criar registro de pagamento
        payment = {
            "id": str(uuid.uuid4()),
            "consortium_id": consortium_id,
            "user_id": current_user.id,
            "installment_number": payment_data.get("installment_number"),
            "payment_date": datetime.fromisoformat(payment_data.get("payment_date")),
            "amount_paid": payment_data.get("amount_paid"),
            "payment_type": payment_data.get("payment_type", "Regular"),
            "notes": payment_data.get("notes"),
            "created_at": datetime.utcnow()
        }
        
        await db.consortium_payments.insert_one(payment)
        
        # Atualizar consórcio
        paid_installments = consortium["paid_installments"] + 1
        remaining_balance = consortium["remaining_balance"] - payment_data.get("amount_paid", 0)
        
        await db.consortiums.update_one(
            {"id": consortium_id},
            {"$set": {
                "paid_installments": paid_installments,
                "remaining_balance": max(0, remaining_balance)
            }}
        )
        
        return {"message": "Pagamento registrado com sucesso", "payment_id": payment["id"]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar pagamento: {str(e)}")

@api_router.post("/consortiums/{consortium_id}/contemplation")
async def mark_contemplation(consortium_id: str, contemplation_data: ConsortiumContemplation, current_user: User = Depends(get_current_user)):
    """Marcar consórcio como contemplado"""
    try:
        # Verificar se consórcio existe
        consortium = await db.consortiums.find_one({"id": consortium_id, "user_id": current_user.id})
        if not consortium:
            raise HTTPException(status_code=404, detail="Consórcio não encontrado")
        
        # Atualizar consórcio
        await db.consortiums.update_one(
            {"id": consortium_id},
            {"$set": {
                "contemplated": True,
                "contemplation_date": contemplation_data.contemplation_date,
                "status": "Contemplado"
            }}
        )
        
        return {"message": "Consórcio marcado como contemplado com sucesso"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao marcar contemplação: {str(e)}")

@api_router.get("/consortiums/{consortium_id}/summary")
async def get_consortium_summary(consortium_id: str, current_user: User = Depends(get_current_user)):
    """Obter resumo completo do consórcio"""
    try:
        # Buscar consórcio
        consortium = await db.consortiums.find_one({"id": consortium_id, "user_id": current_user.id})
        if not consortium:
            raise HTTPException(status_code=404, detail="Consórcio não encontrado")
        
        # Buscar pagamentos
        payments = await db.consortium_payments.find({"consortium_id": consortium_id}).to_list(1000)
        
        # Calcular estatísticas
        total_paid = sum(p.get("amount_paid", 0) for p in payments)
        progress_percentage = (consortium["paid_installments"] / consortium["installment_count"]) * 100
        
        return {
            "consortium": Consortium(**consortium),
            "payments": payments,
            "statistics": {
                "total_paid": total_paid,
                "progress_percentage": progress_percentage,
                "remaining_installments": consortium["installment_count"] - consortium["paid_installments"],
                "next_due_date": calculate_next_due_date(consortium)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo: {str(e)}")

# ============================================================================
# 🏠 CONSORTIUM ENHANCEMENTS - PHASE 3 (New Enhanced Endpoints)
# ============================================================================

@api_router.get("/consortiums/dashboard", response_model=Dict[str, Any])
async def get_consortium_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Painel de visualização completo dos consórcios ativos - PHASE 3 ENHANCEMENT"""
    try:
        dashboard = await generate_consortium_dashboard(current_user.id)
        
        # Retornar dados estruturados conforme esperado pelos testes
        return {
            "message": "Painel de consórcios carregado com sucesso",
            "total_consortiums": dashboard.total_consortiums,
            "active_consortiums": dashboard.active_consortiums,
            "contemplated_consortiums": dashboard.contemplated_consortiums,
            "paid_consortiums": dashboard.paid_consortiums,
            "suspended_consortiums": dashboard.suspended_consortiums,
            "total_invested": dashboard.total_invested,
            "total_pending": dashboard.total_pending,
            "next_payments": dashboard.next_payments,
            "contemplation_projections": dashboard.contemplation_projections,
            "performance_summary": dashboard.performance_summary,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar painel: {str(e)}")

@api_router.get("/consortiums/active", response_model=List[Dict[str, Any]])
async def get_active_consortiums(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    type: Optional[str] = None,
    contemplated: Optional[bool] = None
):
    """Listar consórcios com filtros avançados - PHASE 3 ENHANCEMENT"""
    try:
        # Construir query com filtros
        query = {"user_id": current_user.id}
        
        # Filtro por status
        if status:
            if status not in ["Ativo", "Pago", "Contemplado", "Suspenso"]:
                raise HTTPException(status_code=400, detail="Status inválido")
            query["status"] = status
        
        # Filtro por tipo
        if type:
            if type not in ["Imóvel", "Veículo", "Moto"]:
                raise HTTPException(status_code=400, detail="Tipo inválido")
            query["type"] = type
        
        # Filtro por contemplação
        if contemplated is not None:
            query["contemplated"] = contemplated
        
        consortiums = await db.consortiums.find(query).sort("created_at", -1).to_list(100)
        
        # Enriquecer dados com informações adicionais (campos esperados pelos testes)
        enriched_consortiums = []
        for consortium in consortiums:
            # Remove MongoDB ObjectId
            if "_id" in consortium:
                del consortium["_id"]
            
            # Adicionar informações calculadas
            completion_percentage = (consortium["paid_installments"] / consortium["installment_count"]) * 100
            remaining_installments = consortium["installment_count"] - consortium["paid_installments"]
            total_paid = consortium["paid_installments"] * consortium["monthly_installment"]
            months_remaining = remaining_installments  # Assumindo pagamentos mensais
            
            # Adicionar próxima data de vencimento
            next_due_date = calculate_next_due_date(consortium)
            
            # Adicionar projeção de contemplação se ativo e não contemplado
            contemplation_projection = None
            contemplation_probability = 0.0
            
            if consortium["status"] == "Ativo" and not consortium["contemplated"]:
                projection = await calculate_contemplation_projection(consortium)
                contemplation_probability = projection.probability_score
                contemplation_projection = {
                    "estimated_date": projection.estimated_contemplation_date.isoformat(),
                    "probability_score": projection.probability_score,
                    "completion_percentage": projection.completion_percentage,
                    "methods": projection.contemplation_methods
                }
            
            enriched_consortium = {
                **consortium,
                "completion_percentage": round(completion_percentage, 2),
                "remaining_installments": remaining_installments,
                "months_remaining": months_remaining,
                "total_paid": total_paid,
                "next_due_date": next_due_date,
                "contemplation_projection": contemplation_projection,
                "contemplation_probability": round(contemplation_probability, 2)
            }
            
            enriched_consortiums.append(enriched_consortium)
        
        return enriched_consortiums
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar consórcios: {str(e)}")

@api_router.get("/consortiums/contemplation-projections", response_model=List[Dict[str, Any]])
async def get_contemplation_projections(
    current_user: User = Depends(get_current_user),
    min_probability: Optional[float] = None,
    limit: Optional[int] = 10
):
    """Obter projeções de contemplação para consórcios ativos - PHASE 3 ENHANCEMENT"""
    try:
        # Buscar consórcios ativos não contemplados
        active_consortiums = await db.consortiums.find({
            "user_id": current_user.id,
            "status": "Ativo",
            "contemplated": False
        }).to_list(100)
        
        if not active_consortiums:
            return []
        
        # Gerar projeções
        projections = []
        for consortium in active_consortiums:
            projection = await calculate_contemplation_projection(consortium)
            
            # Calcular campos adicionais solicitados pelos testes
            months_remaining = consortium["installment_count"] - consortium["paid_installments"]
            completion_percentage = (consortium["paid_installments"] / consortium["installment_count"]) * 100
            
            # Gerar recomendação baseada na probabilidade
            if projection.probability_score >= 80:
                recommendation = "Alta probabilidade - Considere lance para acelerar contemplação"
            elif projection.probability_score >= 60:
                recommendation = "Boa probabilidade - Continue com pagamentos regulares"
            elif projection.probability_score >= 40:
                recommendation = "Probabilidade moderada - Considere estratégias de lance"
            else:
                recommendation = "Baixa probabilidade - Avalie viabilidade do consórcio"
            
            projection_dict = {
                "consortium_id": projection.consortium_id,
                "consortium_name": projection.consortium_name,
                "consortium_type": consortium["type"],
                "administrator": consortium["administrator"],
                "total_value": consortium["total_value"],
                "group_number": consortium.get("group_number"),
                "quota_number": consortium.get("quota_number"),
                "current_installment": projection.current_installment,
                "total_installments": projection.total_installments,
                "completion_percentage": round(completion_percentage, 2),
                "estimated_contemplation_date": projection.estimated_contemplation_date.isoformat(),
                "contemplation_probability": round(projection.probability_score, 2),
                "monthly_installment": projection.monthly_installment,
                "total_remaining": projection.total_remaining,
                "available_methods": projection.contemplation_methods,
                "months_remaining": months_remaining,
                "recommendation": recommendation
            }
            
            # Aplicar filtro de probabilidade mínima
            if min_probability is None or projection.probability_score >= min_probability:
                projections.append(projection_dict)
        
        # Ordenar por probabilidade (maior primeiro)
        projections.sort(key=lambda x: x["contemplation_probability"], reverse=True)
        
        # Aplicar limite
        if limit:
            projections = projections[:limit]
        
        return projections
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar projeções: {str(e)}")

@api_router.get("/consortiums/statistics", response_model=Dict[str, Any])
async def get_consortium_statistics(
    current_user: User = Depends(get_current_user)
):
    """Estatísticas detalhadas dos consórcios - PHASE 3 ENHANCEMENT"""
    try:
        # Buscar todos os consórcios
        consortiums = await db.consortiums.find({"user_id": current_user.id}).to_list(100)
        
        if not consortiums:
            return {
                "total_consortiums": 0,
                "summary": "Nenhum consórcio encontrado",
                "statistics": {}
            }
        
        # Estatísticas gerais
        total_consortiums = len(consortiums)
        active_count = len([c for c in consortiums if c["status"] == "Ativo"])
        contemplated_count = len([c for c in consortiums if c["contemplated"]])
        paid_count = len([c for c in consortiums if c["status"] == "Pago"])
        suspended_count = len([c for c in consortiums if c["status"] == "Suspenso"])
        
        # Distribuição por status (campo esperado pelos testes)
        distribution_by_status = {
            "Ativo": active_count,
            "Contemplado": contemplated_count,
            "Pago": paid_count,
            "Suspenso": suspended_count
        }
        
        # Distribuição por tipo (campo esperado pelos testes)
        distribution_by_type = {
            "Imóvel": len([c for c in consortiums if c["type"] == "Imóvel"]),
            "Veículo": len([c for c in consortiums if c["type"] == "Veículo"]),
            "Moto": len([c for c in consortiums if c["type"] == "Moto"])
        }
        
        # Estatísticas financeiras
        total_invested = sum(c["paid_installments"] * c["monthly_installment"] for c in consortiums)
        total_portfolio_value = sum(c["total_value"] for c in consortiums)
        total_pending = sum(c["remaining_balance"] for c in consortiums)
        avg_monthly_payment = sum(c["monthly_installment"] for c in consortiums) / len(consortiums)
        
        # Progresso médio (campo esperado pelos testes)
        completion_percentages = [
            (c["paid_installments"] / c["installment_count"]) * 100 
            for c in consortiums
        ]
        average_progress = sum(completion_percentages) / len(completion_percentages)
        
        # Top administradoras
        administrators = [c["administrator"] for c in consortiums]
        admin_counts = {}
        for admin in administrators:
            admin_counts[admin] = admin_counts.get(admin, 0) + 1
        
        top_administrators = sorted(admin_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Próximos vencimentos (campo esperado pelos testes)
        upcoming_due_dates = []
        for consortium in consortiums:
            if consortium["status"] == "Ativo":
                next_due = datetime.utcnow().replace(day=consortium["due_day"])
                if next_due <= datetime.utcnow():
                    if next_due.month == 12:
                        next_due = next_due.replace(year=next_due.year + 1, month=1)
                    else:
                        next_due = next_due.replace(month=next_due.month + 1)
                
                days_until_due = (next_due - datetime.utcnow()).days
                if days_until_due <= 30:
                    upcoming_due_dates.append({
                        "consortium_name": consortium["name"],
                        "due_date": next_due.isoformat(),
                        "amount": consortium["monthly_installment"],
                        "days_until_due": days_until_due
                    })
        
        upcoming_due_dates.sort(key=lambda x: x["days_until_due"])
        
        # Resumo de contemplação (campo esperado pelos testes)
        contemplation_summary = {
            "total_contemplated": contemplated_count,
            "contemplation_rate": round((contemplated_count / total_consortiums) * 100, 2),
            "average_contemplation_time": 0,  # Seria calculado baseado em dados históricos
            "contemplation_methods": {
                "sorteio": len([c for c in consortiums if c.get("contemplated") and c.get("bid_value") is None]),
                "lance": len([c for c in consortiums if c.get("contemplated") and c.get("bid_value") is not None]),
                "natural": len([c for c in consortiums if c["status"] == "Pago"])
            }
        }
        
        return {
            "total_consortiums": total_consortiums,
            "distribution_by_status": distribution_by_status,
            "distribution_by_type": distribution_by_type,
            "financial_summary": {
                "total_invested": round(total_invested, 2),
                "total_portfolio_value": round(total_portfolio_value, 2),
                "total_pending": round(total_pending, 2),
                "average_monthly_payment": round(avg_monthly_payment, 2)
            },
            "average_progress": round(average_progress, 2),
            "contemplation_summary": contemplation_summary,
            "top_administrators": [{"name": admin, "count": count} for admin, count in top_administrators],
            "upcoming_due_dates": upcoming_due_dates[:10],
            "completion_percentages": [round(p, 2) for p in completion_percentages],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar estatísticas: {str(e)}")

@api_router.get("/consortiums/payments-calendar", response_model=Dict[str, Any])
async def get_payments_calendar(
    current_user: User = Depends(get_current_user),
    months_ahead: Optional[int] = 12
):
    """Calendário de pagamentos dos consórcios - PHASE 3 ENHANCEMENT"""
    try:
        # Buscar consórcios ativos
        active_consortiums = await db.consortiums.find({
            "user_id": current_user.id,
            "status": "Ativo"
        }).to_list(100)
        
        if not active_consortiums:
            return {
                "calendar": {},
                "total_months": 0,
                "total_monthly_commitment": 0.0,
                "next_12_months_summary": {},
                "message": "Nenhum consórcio ativo encontrado"
            }
        
        # Calcular compromisso mensal total (campo esperado pelos testes)
        total_monthly_commitment = sum(c["monthly_installment"] for c in active_consortiums)
        
        # Gerar calendário de pagamentos
        calendar = {}
        current_date = datetime.utcnow()
        
        # Resumo dos próximos 12 meses (campo esperado pelos testes)
        next_12_months_summary = {
            "total_amount": total_monthly_commitment * min(months_ahead, 12),
            "total_payments": len(active_consortiums) * min(months_ahead, 12),
            "monthly_average": total_monthly_commitment,
            "active_consortiums": len(active_consortiums)
        }
        
        for month_offset in range(months_ahead):
            # Calcular mês/ano
            target_date = current_date + timedelta(days=30 * month_offset)
            month_key = target_date.strftime("%Y-%m")
            
            monthly_payments = []
            monthly_total = 0
            
            for consortium in active_consortiums:
                # Calcular data de vencimento para este mês
                due_date = target_date.replace(day=consortium["due_day"])
                
                payment_info = {
                    "consortium_id": consortium["id"],
                    "consortium_name": consortium["name"],
                    "consortium_type": consortium["type"],
                    "administrator": consortium["administrator"],
                    "due_date": due_date.isoformat(),
                    "amount": consortium["monthly_installment"],
                    "installment_number": consortium["paid_installments"] + month_offset + 1,
                    "remaining_after_payment": consortium["installment_count"] - (consortium["paid_installments"] + month_offset + 1)
                }
                
                monthly_payments.append(payment_info)
                monthly_total += consortium["monthly_installment"]
            
            calendar[month_key] = {
                "month": target_date.strftime("%B %Y"),
                "payments": monthly_payments,
                "total_amount": round(monthly_total, 2),
                "payment_count": len(monthly_payments)
            }
        
        return {
            "calendar": calendar,
            "total_months": months_ahead,
            "total_monthly_commitment": round(total_monthly_commitment, 2),
            "next_12_months_summary": next_12_months_summary,
            "summary": {
                "total_monthly_commitment": round(total_monthly_commitment, 2),
                "active_consortiums_count": len(active_consortiums)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar calendário: {str(e)}")

# ============================================================================
# 🏠 CONSORTIUM ENHANCEMENTS - PHASE 3 (Additional Models and Functions)
# ============================================================================

class ConsortiumDashboard(BaseModel):
    """Modelo para painel de visualização de consórcios"""
    total_consortiums: int
    active_consortiums: int
    contemplated_consortiums: int
    paid_consortiums: int
    suspended_consortiums: int
    total_invested: float
    total_pending: float
    next_payments: List[Dict[str, Any]]
    contemplation_projections: List[Dict[str, Any]]
    performance_summary: Dict[str, float]

class ConsortiumContemplationProjection(BaseModel):
    """Modelo para projeção de contemplação"""
    consortium_id: str
    consortium_name: str
    current_installment: int
    total_installments: int
    completion_percentage: float
    estimated_contemplation_date: datetime
    probability_score: float  # 0-100%
    monthly_installment: float
    total_remaining: float
    contemplation_methods: List[str]  # "sorteio", "lance", "natural"

async def calculate_contemplation_projection(consortium: Dict[str, Any]) -> ConsortiumContemplationProjection:
    """Calcular projeção de contemplação baseada em dados históricos e padrões"""
    try:
        # Calcular percentual de conclusão
        completion_percentage = (consortium["paid_installments"] / consortium["installment_count"]) * 100
        
        # Calcular data estimada de contemplação (baseada no progresso atual)
        remaining_installments = consortium["installment_count"] - consortium["paid_installments"]
        
        # Estimar data baseada na frequência de pagamentos (assumindo mensal)
        estimated_date = datetime.utcnow() + timedelta(days=30 * remaining_installments)
        
        # Calcular probabilidade baseada no progresso e histórico
        if completion_percentage >= 80:
            probability_score = 85.0
        elif completion_percentage >= 60:
            probability_score = 70.0
        elif completion_percentage >= 40:
            probability_score = 55.0
        elif completion_percentage >= 20:
            probability_score = 40.0
        else:
            probability_score = 25.0
        
        # Ajustar probabilidade baseada no tipo de consórcio
        if consortium["type"] == "Imóvel":
            probability_score += 5  # Consórcios de imóveis têm maior taxa de conclusão
        elif consortium["type"] == "Veículo":
            probability_score += 3
        
        # Métodos de contemplação disponíveis
        contemplation_methods = ["sorteio", "natural"]
        if consortium["remaining_balance"] > 50000:  # Para valores altos, lance é mais comum
            contemplation_methods.append("lance")
        
        return ConsortiumContemplationProjection(
            consortium_id=consortium["id"],
            consortium_name=consortium["name"],
            current_installment=consortium["paid_installments"],
            total_installments=consortium["installment_count"],
            completion_percentage=completion_percentage,
            estimated_contemplation_date=estimated_date,
            probability_score=min(100.0, probability_score),
            monthly_installment=consortium["monthly_installment"],
            total_remaining=consortium["remaining_balance"],
            contemplation_methods=contemplation_methods
        )
        
    except Exception as e:
        print(f"[CONSORTIUM PROJECTION ERROR] {str(e)}")
        # Fallback com dados básicos
        return ConsortiumContemplationProjection(
            consortium_id=consortium.get("id", ""),
            consortium_name=consortium.get("name", "Consórcio"),
            current_installment=consortium.get("paid_installments", 0),
            total_installments=consortium.get("installment_count", 1),
            completion_percentage=0.0,
            estimated_contemplation_date=datetime.utcnow() + timedelta(days=365),
            probability_score=30.0,
            monthly_installment=consortium.get("monthly_installment", 0),
            total_remaining=consortium.get("remaining_balance", 0),
            contemplation_methods=["sorteio", "natural"]
        )

async def generate_consortium_dashboard(user_id: str) -> ConsortiumDashboard:
    """Gerar painel completo de consórcios para o usuário"""
    try:
        # Buscar todos os consórcios do usuário
        consortiums = await db.consortiums.find({"user_id": user_id}).to_list(100)
        
        if not consortiums:
            return ConsortiumDashboard(
                total_consortiums=0,
                active_consortiums=0,
                contemplated_consortiums=0,
                paid_consortiums=0,
                suspended_consortiums=0,
                total_invested=0.0,
                total_pending=0.0,
                next_payments=[],
                contemplation_projections=[],
                performance_summary={}
            )
        
        # Calcular estatísticas básicas
        total_consortiums = len(consortiums)
        active_consortiums = len([c for c in consortiums if c["status"] == "Ativo"])
        contemplated_consortiums = len([c for c in consortiums if c["contemplated"]])
        paid_consortiums = len([c for c in consortiums if c["status"] == "Pago"])
        suspended_consortiums = len([c for c in consortiums if c["status"] == "Suspenso"])
        
        # Calcular valores totais
        total_invested = sum(c["paid_installments"] * c["monthly_installment"] for c in consortiums)
        total_pending = sum(c["remaining_balance"] for c in consortiums)
        
        # Próximos pagamentos (próximos 30 dias)
        next_payments = []
        for consortium in consortiums:
            if consortium["status"] == "Ativo":
                # Calcular próxima data de vencimento
                next_due = datetime.utcnow().replace(day=consortium["due_day"])
                if next_due <= datetime.utcnow():
                    if next_due.month == 12:
                        next_due = next_due.replace(year=next_due.year + 1, month=1)
                    else:
                        next_due = next_due.replace(month=next_due.month + 1)
                
                next_payments.append({
                    "consortium_id": consortium["id"],
                    "consortium_name": consortium["name"],
                    "due_date": next_due.isoformat(),
                    "amount": consortium["monthly_installment"],
                    "installment_number": consortium["paid_installments"] + 1,
                    "days_until_due": (next_due - datetime.utcnow()).days,
                    "type": consortium["type"],
                    "administrator": consortium["administrator"]
                })
        
        # Ordenar por data de vencimento
        next_payments.sort(key=lambda x: x["days_until_due"])
        
        # Projeções de contemplação
        contemplation_projections = []
        for consortium in consortiums:
            if consortium["status"] == "Ativo" and not consortium["contemplated"]:
                projection = await calculate_contemplation_projection(consortium)
                contemplation_projections.append({
                    "consortium_id": projection.consortium_id,
                    "consortium_name": projection.consortium_name,
                    "completion_percentage": projection.completion_percentage,
                    "estimated_contemplation_date": projection.estimated_contemplation_date.isoformat(),
                    "probability_score": projection.probability_score,
                    "contemplation_methods": projection.contemplation_methods,
                    "monthly_installment": projection.monthly_installment,
                    "total_remaining": projection.total_remaining
                })
        
        # Ordenar por probabilidade (maior primeiro)
        contemplation_projections.sort(key=lambda x: x["probability_score"], reverse=True)
        
        # Resumo de performance
        avg_completion = sum(c["paid_installments"] / c["installment_count"] for c in consortiums) / len(consortiums) * 100
        avg_monthly_payment = sum(c["monthly_installment"] for c in consortiums) / len(consortiums)
        
        performance_summary = {
            "average_completion_percentage": round(avg_completion, 2),
            "average_monthly_payment": round(avg_monthly_payment, 2),
            "total_portfolio_value": sum(c["total_value"] for c in consortiums),
            "contemplation_rate": (contemplated_consortiums / total_consortiums * 100) if total_consortiums > 0 else 0,
            "average_installment_count": sum(c["installment_count"] for c in consortiums) / len(consortiums),
            "total_monthly_commitment": sum(c["monthly_installment"] for c in consortiums if c["status"] == "Ativo")
        }
        
        return ConsortiumDashboard(
            total_consortiums=total_consortiums,
            active_consortiums=active_consortiums,
            contemplated_consortiums=contemplated_consortiums,
            paid_consortiums=paid_consortiums,
            suspended_consortiums=suspended_consortiums,
            total_invested=total_invested,
            total_pending=total_pending,
            next_payments=next_payments[:10],  # Próximos 10 pagamentos
            contemplation_projections=contemplation_projections,
            performance_summary=performance_summary
        )
        
    except Exception as e:
        print(f"[CONSORTIUM DASHBOARD ERROR] {str(e)}")
        raise e

# Helper functions for AI
async def get_monthly_average_income(user_id: str) -> float:
    """Calcular média mensal de receitas"""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    income_transactions = await db.transactions.find({
        "user_id": user_id,
        "type": "Receita",
        "transaction_date": {"$gte": thirty_days_ago.isoformat()}
    }).to_list(1000)
    
    total_income = sum(t.get("value", 0) for t in income_transactions)
    return total_income

async def get_monthly_average_expense(user_id: str) -> float:
    """Calcular média mensal de despesas"""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    expense_transactions = await db.transactions.find({
        "user_id": user_id,
        "type": "Despesa", 
        "transaction_date": {"$gte": thirty_days_ago.isoformat()}
    }).to_list(1000)
    
    total_expense = sum(t.get("value", 0) for t in expense_transactions)
    return total_expense

async def get_expenses_by_category(user_id: str, since_date: datetime) -> Dict[str, float]:
    """Agrupar despesas por categoria"""
    expenses = await db.transactions.find({
        "user_id": user_id,
        "type": "Despesa",
        "transaction_date": {"$gte": since_date.isoformat()}
    }).to_list(1000)
    
    expense_by_category = defaultdict(float)
    
    for exp in expenses:
        category = await db.categories.find_one({"id": exp.get("category_id")})
        if category:
            expense_by_category[category["name"]] += exp.get("value", 0)
    
    return dict(expense_by_category)

def calculate_next_due_date(consortium: Dict[str, Any]) -> str:
    """Calcular próxima data de vencimento"""
    try:
        next_month = datetime.now().replace(day=consortium.get("due_day", 15))
        if next_month <= datetime.now():
            if next_month.month == 12:
                next_month = next_month.replace(year=next_month.year + 1, month=1)
            else:
                next_month = next_month.replace(month=next_month.month + 1)
        return next_month.strftime("%Y-%m-%d")
    except:
        return "N/A"

# ============================================================================
# 🔄 AUTOMATIC RECURRENCE SYSTEM HELPER FUNCTIONS
# ============================================================================

def calculate_next_execution_date(start_date: datetime, pattern: str, interval: int, last_execution: Optional[datetime] = None) -> datetime:
    """Calcular próxima data de execução baseada no padrão de recorrência"""
    base_date = last_execution if last_execution else start_date
    
    if pattern == "diario":
        return base_date + timedelta(days=interval)
    elif pattern == "semanal":
        return base_date + timedelta(weeks=interval)
    elif pattern == "mensal":
        # Adicionar meses mantendo o dia do mês (ou último dia se inválido)
        try:
            if base_date.month + interval <= 12:
                new_month = base_date.month + interval
                new_year = base_date.year
            else:
                months_to_add = interval
                new_year = base_date.year
                new_month = base_date.month
                
                while months_to_add > 0:
                    if new_month + months_to_add <= 12:
                        new_month += months_to_add
                        months_to_add = 0
                    else:
                        months_to_add -= (12 - new_month + 1)
                        new_year += 1
                        new_month = 1
            
            # Tentar criar data com o mesmo dia
            try:
                return base_date.replace(year=new_year, month=new_month)
            except ValueError:
                # Se o dia não existe no novo mês (ex: 31 em fevereiro), usar último dia do mês
                import calendar
                last_day = calendar.monthrange(new_year, new_month)[1]
                return base_date.replace(year=new_year, month=new_month, day=last_day)
        except:
            return base_date + timedelta(days=30 * interval)  # Fallback
            
    elif pattern == "anual":
        try:
            return base_date.replace(year=base_date.year + interval)
        except ValueError:
            # Para anos bissextos (29 de fevereiro)
            return base_date.replace(year=base_date.year + interval, day=28)
    else:
        raise ValueError(f"Padrão de recorrência inválido: {pattern}")

def generate_recurrence_preview(rule: RecurrenceRule, months_ahead: int = 12) -> List[Dict[str, Any]]:
    """Gerar preview das próximas transações baseadas na regra de recorrência"""
    preview_transactions = []
    current_date = rule.next_execution_date
    end_preview_date = datetime.utcnow() + timedelta(days=30 * months_ahead)
    
    execution_count = 0
    max_preview_transactions = 50  # Limite de segurança
    
    while (current_date <= end_preview_date and 
           execution_count < max_preview_transactions and
           (rule.end_date is None or current_date <= rule.end_date) and
           (rule.max_executions is None or rule.total_executions + execution_count < rule.max_executions)):
        
        transaction_preview = {
            "execution_date": current_date.isoformat(),
            "description": rule.transaction_description,
            "value": rule.transaction_value,
            "type": rule.transaction_type,
            "account_id": rule.account_id,
            "category_id": rule.category_id,
            "execution_number": rule.total_executions + execution_count + 1,
            "observation": f"Transação recorrente: {rule.name}"
        }
        
        preview_transactions.append(transaction_preview)
        
        # Calcular próxima data
        current_date = calculate_next_execution_date(
            current_date, rule.recurrence_pattern, rule.interval, current_date
        )
        execution_count += 1
    
    return preview_transactions

async def create_transaction_from_recurrence(rule: RecurrenceRule, execution_date: datetime, user_id: str) -> str:
    """Criar transação baseada em regra de recorrência"""
    try:
        # Criar transação
        transaction = Transaction(
            user_id=user_id,
            description=rule.transaction_description,
            value=rule.transaction_value,
            type=rule.transaction_type,
            transaction_date=execution_date,
            account_id=rule.account_id,
            category_id=rule.category_id,
            observation=f"Transação recorrente automática: {rule.name}",
            status="Pago",  # Transações automáticas são criadas como pagas
            tags=rule.tags,
            is_recurring=True,
            recurrence_interval=rule.recurrence_pattern,
            related_transaction_id=rule.id  # Relacionar com a regra de recorrência
        )
        
        await db.transactions.insert_one(transaction.dict())
        
        # Atualizar saldo da conta
        if rule.transaction_type == "Receita":
            balance_change = rule.transaction_value
        else:  # Despesa
            balance_change = -rule.transaction_value
            
        await db.accounts.update_one(
            {"id": rule.account_id, "user_id": user_id},
            {"$inc": {"current_balance": balance_change}}
        )
        
        return transaction.id
        
    except Exception as e:
        print(f"[RECURRENCE ERROR] Erro ao criar transação: {e}")
        raise e

async def process_pending_recurrences(user_id: str) -> Dict[str, Any]:
    """Processar recorrências pendentes para um usuário"""
    try:
        results = {
            "processed_rules": 0,
            "created_transactions": 0,
            "created_suggestions": 0,
            "errors": []
        }
        
        # Buscar regras ativas que precisam ser executadas
        active_rules = await db.recurrence_rules.find({
            "user_id": user_id,
            "is_active": True,
            "next_execution_date": {"$lte": datetime.utcnow()}
        }).to_list(100)
        
        for rule_data in active_rules:
            try:
                rule = RecurrenceRule(**rule_data)
                results["processed_rules"] += 1
                
                if rule.auto_create and not rule.require_confirmation:
                    # Criar transação automaticamente
                    transaction_id = await create_transaction_from_recurrence(
                        rule, rule.next_execution_date, user_id
                    )
                    results["created_transactions"] += 1
                    
                    # Atualizar regra
                    next_date = calculate_next_execution_date(
                        rule.next_execution_date, rule.recurrence_pattern, 
                        rule.interval, rule.next_execution_date
                    )
                    
                    await db.recurrence_rules.update_one(
                        {"id": rule.id},
                        {"$set": {
                            "last_execution_date": rule.next_execution_date,
                            "next_execution_date": next_date,
                            "total_executions": rule.total_executions + 1,
                            "updated_at": datetime.utcnow()
                        }}
                    )
                    
                else:
                    # Criar sugestão para confirmação
                    suggestion = PendingRecurrence(
                        user_id=user_id,
                        recurrence_rule_id=rule.id,
                        suggested_date=rule.next_execution_date,
                        transaction_data={
                            "description": rule.transaction_description,
                            "value": rule.transaction_value,
                            "type": rule.transaction_type,
                            "account_id": rule.account_id,
                            "category_id": rule.category_id,
                            "observation": f"Transação recorrente: {rule.name}"
                        },
                        expires_at=datetime.utcnow() + timedelta(days=7)  # Expira em 7 dias
                    )
                    
                    await db.pending_recurrences.insert_one(suggestion.dict())
                    results["created_suggestions"] += 1
                    
                    # Atualizar próxima data de execução da regra
                    next_date = calculate_next_execution_date(
                        rule.next_execution_date, rule.recurrence_pattern, 
                        rule.interval, rule.next_execution_date
                    )
                    
                    await db.recurrence_rules.update_one(
                        {"id": rule.id},
                        {"$set": {
                            "next_execution_date": next_date,
                            "updated_at": datetime.utcnow()
                        }}
                    )
                    
            except Exception as e:
                error_msg = f"Erro ao processar regra {rule_data.get('name', 'desconhecida')}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"[RECURRENCE ERROR] {error_msg}")
        
        return results
        
    except Exception as e:
        print(f"[RECURRENCE ERROR] Erro geral no processamento: {e}")
        raise e

# ============================================================================
# 📁 SISTEMA DE IMPORTAÇÃO DE ARQUIVOS COM OCR
# ============================================================================

async def extract_text_from_image(image_content: bytes) -> str:
    """Extract text from image using Tesseract OCR"""
    try:
        image = Image.open(io.BytesIO(image_content))
        text = pytesseract.image_to_string(image, lang='por')
        return text
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

async def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF using pdf2image and Tesseract"""
    try:
        images = convert_from_bytes(pdf_content)
        full_text = ""
        for image in images:
            text = pytesseract.image_to_string(image, lang='por')
            full_text += text + "\n"
        return full_text
    except Exception as e:
        print(f"PDF OCR Error: {e}")
        return ""

async def parse_excel_file(file_content: bytes) -> List[Dict]:
    """Parse Excel file and extract transaction data"""
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        
        # Try to identify columns (flexible parsing)
        transactions = []
        for index, row in df.iterrows():
            # Look for date, description, value patterns
            transaction = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['data', 'date']):
                    transaction['data'] = str(row[col])
                elif any(word in col_lower for word in ['descricao', 'description', 'desc']):
                    transaction['descricao'] = str(row[col])
                elif any(word in col_lower for word in ['valor', 'value', 'amount']):
                    try:
                        transaction['valor'] = float(row[col])
                    except:
                        transaction['valor'] = 0.0
                elif any(word in col_lower for word in ['categoria', 'category']):
                    transaction['categoria'] = str(row[col])
                elif any(word in col_lower for word in ['tipo', 'type']):
                    transaction['tipo'] = str(row[col])
            
            if 'data' in transaction and 'descricao' in transaction and 'valor' in transaction:
                transactions.append(transaction)
        
        return transactions
    except Exception as e:
        print(f"Excel parsing error: {e}")
        return []

async def parse_csv_file(file_content: bytes) -> List[Dict]:
    """Parse CSV file and extract transaction data"""
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        
        transactions = []
        for index, row in df.iterrows():
            transaction = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['data', 'date']):
                    transaction['data'] = str(row[col])
                elif any(word in col_lower for word in ['descricao', 'description', 'desc']):
                    transaction['descricao'] = str(row[col])
                elif any(word in col_lower for word in ['valor', 'value', 'amount']):
                    try:
                        transaction['valor'] = float(row[col])
                    except:
                        transaction['valor'] = 0.0
                elif any(word in col_lower for word in ['categoria', 'category']):
                    transaction['categoria'] = str(row[col])
                elif any(word in col_lower for word in ['tipo', 'type']):
                    transaction['tipo'] = str(row[col])
            
            if 'data' in transaction and 'descricao' in transaction and 'valor' in transaction:
                transactions.append(transaction)
        
        return transactions
    except Exception as e:
        print(f"CSV parsing error: {e}")
        return []

async def extract_transactions_from_text(text: str) -> List[Dict]:
    """Extract transaction data from OCR text using pattern matching"""
    transactions = []
    
    # Brazilian date patterns (dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy)
    date_patterns = [
        r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',
        r'\d{1,2} de \w+ de \d{4}'
    ]
    
    # Value patterns (R$ 123,45 or 123.45)
    value_patterns = [
        r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}',
        r'\d{1,3}(?:\.\d{3})*,\d{2}',
        r'\d+\.\d{2}'
    ]
    
    lines = text.split('\n')
    current_transaction = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for dates
        for pattern in date_patterns:
            dates = re.findall(pattern, line)
            if dates:
                current_transaction['data'] = dates[0]
        
        # Look for values
        for pattern in value_patterns:
            values = re.findall(pattern, line)
            if values:
                value_str = values[0].replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                try:
                    current_transaction['valor'] = float(value_str)
                except:
                    pass
        
        # Description (lines with common transaction words)
        transaction_keywords = ['compra', 'pagamento', 'transferencia', 'pix', 'deposito', 'saque']
        if any(keyword in line.lower() for keyword in transaction_keywords):
            current_transaction['descricao'] = line
        
        # If we have enough data, save transaction
        if len(current_transaction) >= 3 and 'data' in current_transaction:
            transactions.append(current_transaction.copy())
            current_transaction = {}
    
    return transactions

async def check_duplicate_transaction(user_id: str, transaction: Dict) -> bool:
    """Check if transaction is duplicate based on date + description + value"""
    existing = await db.transactions.find_one({
        "user_id": user_id,
        "transaction_date": transaction.get('data'),
        "description": transaction.get('descricao'),
        "value": transaction.get('valor')
    })
    return bool(existing)

@api_router.post("/import/upload")
async def upload_files_for_import(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple files for import processing"""
    try:
        session_id = str(uuid.uuid4())
        processed_data = []
        total_transactions = []
        
        for file in files:
            if not file.filename:
                continue
                
            content = await file.read()
            file_extension = Path(file.filename).suffix.lower()
            
            print(f"Processing file: {file.filename} ({file_extension})")
            
            transactions = []
            
            # Process based on file type
            if file_extension in ['.png', '.jpg', '.jpeg']:
                text = await extract_text_from_image(content)
                transactions = await extract_transactions_from_text(text)
                
            elif file_extension == '.pdf':
                text = await extract_text_from_pdf(content)
                transactions = await extract_transactions_from_text(text)
                
            elif file_extension == '.xlsx':
                transactions = await parse_excel_file(content)
                
            elif file_extension == '.csv':
                transactions = await parse_csv_file(content)
            
            # Check for duplicates
            for transaction in transactions:
                is_duplicate = await check_duplicate_transaction(current_user.id, transaction)
                transaction['is_duplicate'] = is_duplicate
                transaction['confidence_score'] = 0.8 if file_extension in ['.xlsx', '.csv'] else 0.6
                
                # Set default values
                if 'tipo' not in transaction:
                    transaction['tipo'] = 'Despesa'
                if 'categoria' not in transaction:
                    transaction['categoria'] = None
                if 'conta' not in transaction:
                    transaction['conta'] = None
            
            file_data = {
                "filename": file.filename,
                "extension": file_extension,
                "transactions_found": len(transactions),
                "transactions": transactions
            }
            
            processed_data.append(file_data)
            total_transactions.extend(transactions)
        
        # Save import session
        import_session = FileImportSession(
            session_id=session_id,
            user_id=current_user.id,
            files_processed=len(files),
            preview_data=total_transactions,
            status="completed"
        )
        
        await db.import_sessions.insert_one(import_session.dict())
        
        return {
            "session_id": session_id,
            "files_processed": len(files),
            "total_transactions": len(total_transactions),
            "preview_data": total_transactions,
            "files_detail": processed_data
        }
        
    except Exception as e:
        print(f"Import upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@api_router.get("/import/sessions/{session_id}")
async def get_import_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get import session data for preview"""
    try:
        session = await db.import_sessions.find_one({
            "session_id": session_id,
            "user_id": current_user.id
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão de importação não encontrada")
        
        # Remove MongoDB ObjectId to avoid JSON serialization issues
        if "_id" in session:
            del session["_id"]
        
        return session
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar sessão: {str(e)}")

@api_router.post("/import/confirm")
async def confirm_import(
    import_request: ImportConfirmRequest,
    current_user: User = Depends(get_current_user)
):
    """Confirm and import selected transactions"""
    try:
        # Verify session exists
        session = await db.import_sessions.find_one({
            "session_id": import_request.session_id,
            "user_id": current_user.id
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão de importação não encontrada")
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        # Get user's default account
        default_account = await db.accounts.find_one({"user_id": current_user.id})
        
        for transaction_data in import_request.selected_transactions:
            try:
                # Skip duplicates if requested
                if transaction_data.is_duplicate:
                    skipped_count += 1
                    continue
                
                # Parse Brazilian date format (dd/mm/yyyy) to datetime
                transaction_date = datetime.utcnow()  # default fallback
                if transaction_data.data:
                    try:
                        # Try parsing Brazilian date format first (dd/mm/yyyy)
                        if '/' in transaction_data.data:
                            day, month, year = transaction_data.data.split('/')
                            transaction_date = datetime(int(year), int(month), int(day))
                        else:
                            # Try ISO format as fallback
                            transaction_date = datetime.fromisoformat(transaction_data.data)
                    except Exception as date_error:
                        print(f"[IMPORT DEBUG] Date parsing failed for '{transaction_data.data}': {date_error}")
                        # Keep default datetime.utcnow()
                
                # Create transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    description=transaction_data.descricao,
                    value=transaction_data.valor,
                    type=transaction_data.tipo or "Despesa",
                    account_id=default_account["id"] if default_account else "",
                    category_id=transaction_data.categoria or None,
                    transaction_date=transaction_date,
                    status="Pago",
                    tags=[],
                    observation=f"Importado via arquivo - Confiança: {transaction_data.confidence_score}"
                )
                
                print(f"[IMPORT DEBUG] Creating transaction: {transaction_data.descricao} - R${transaction_data.valor}")
                await db.transactions.insert_one(transaction.dict())
                
                # Update account balance if account exists
                if default_account:
                    balance_change = transaction_data.valor if transaction_data.tipo == "Receita" else -transaction_data.valor
                    await db.accounts.update_one(
                        {"id": default_account["id"]},
                        {"$inc": {"current_balance": balance_change}}
                    )
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Erro ao importar transação '{transaction_data.descricao}': {str(e)}")
        
        # Update session status
        await db.import_sessions.update_one(
            {"session_id": import_request.session_id},
            {"$set": {"status": "imported"}}
        )
        
        return {
            "message": "Importação concluída com sucesso!",
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "errors": errors,
            "session_id": import_request.session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na importação: {str(e)}")

@api_router.delete("/import/sessions/{session_id}")
async def delete_import_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete import session (cancel import)"""
    try:
        result = await db.import_sessions.delete_one({
            "session_id": session_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        return {"message": "Sessão de importação cancelada"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar importação: {str(e)}")

# ============================================================================
# 🏠 CONTRACT ENDPOINTS - PHASE 2 (CONSORTIUM AND CONSIGNED LOAN)
# ============================================================================

@api_router.post("/contratos", response_model=Dict[str, Any])
async def create_contract(
    contract_data: ContractCreate,
    current_user: User = Depends(get_current_user)
):
    """Criar novo contrato (consórcio ou empréstimo consignado)"""
    try:
        # Validate contract type
        if contract_data.tipo not in ["consórcio", "consignado"]:
            raise HTTPException(status_code=400, detail="Tipo deve ser 'consórcio' ou 'consignado'")
        
        # Validate status
        if contract_data.status not in ["ativo", "quitado", "cancelado"]:
            raise HTTPException(status_code=400, detail="Status deve ser 'ativo', 'quitado' ou 'cancelado'")
        
        # Create contract document
        contract = ContractBase(
            user_id=current_user.id,
            **contract_data.dict()
        ).dict()
        
        # Auto-update status if needed
        contract["status"] = check_contract_status(contract)
        
        # Insert into database
        await db.contracts.insert_one(contract)
        
        # Remove MongoDB _id field for JSON serialization
        if "_id" in contract:
            del contract["_id"]
        
        # Calculate totals for response
        contract_totals = calculate_contract_totals(contract)
        contract.update(contract_totals)
        
        return {
            "message": f"Contrato {contract_data.tipo} criado com sucesso!",
            "contract": contract
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CONTRACT ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar contrato: {str(e)}")

@api_router.get("/contratos", response_model=List[Dict[str, Any]])
async def list_contracts(
    current_user: User = Depends(get_current_user),
    tipo: Optional[str] = None,
    status: Optional[str] = None
):
    """Listar todos os contratos do usuário com filtros opcionais"""
    try:
        # Build query filter
        query = {"user_id": current_user.id}
        
        if tipo and tipo in ["consórcio", "consignado"]:
            query["tipo"] = tipo
            
        if status and status in ["ativo", "quitado", "cancelado"]:
            query["status"] = status
        
        # Get contracts
        contracts = await db.contracts.find(query).to_list(100)
        
        # Calculate totals for each contract and remove MongoDB _id
        for contract in contracts:
            if "_id" in contract:
                del contract["_id"]
            contract_totals = calculate_contract_totals(contract)
            contract.update(contract_totals)
        
        return contracts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar contratos: {str(e)}")

@api_router.get("/contratos/statistics", response_model=Dict[str, Any])
async def get_contracts_statistics(
    current_user: User = Depends(get_current_user)
):
    """Obter estatísticas dos contratos do usuário"""
    try:
        # Get all contracts
        contracts = await db.contracts.find({"user_id": current_user.id}).to_list(100)
        
        if not contracts:
            return {
                "total_contracts": 0,
                "active_contracts": 0,
                "paid_contracts": 0,
                "cancelled_contracts": 0,
                "consortium_count": 0,
                "consigned_count": 0,
                "total_value_sum": 0,
                "total_paid_sum": 0,
                "total_remaining_sum": 0
            }
        
        # Calculate statistics
        total_contracts = len(contracts)
        active_contracts = len([c for c in contracts if c["status"] == "ativo"])
        paid_contracts = len([c for c in contracts if c["status"] == "quitado"])
        cancelled_contracts = len([c for c in contracts if c["status"] == "cancelado"])
        consortium_count = len([c for c in contracts if c["tipo"] == "consórcio"])
        consigned_count = len([c for c in contracts if c["tipo"] == "consignado"])
        
        total_value_sum = 0
        total_paid_sum = 0
        total_remaining_sum = 0
        
        for contract in contracts:
            totals = calculate_contract_totals(contract)
            total_value_sum += totals["valor_total_final"]
            total_paid_sum += totals["valor_total_pago"]
            total_remaining_sum += totals["valor_restante"]
        
        return {
            "total_contracts": total_contracts,
            "active_contracts": active_contracts,
            "paid_contracts": paid_contracts,
            "cancelled_contracts": cancelled_contracts,
            "consortium_count": consortium_count,
            "consigned_count": consigned_count,
            "total_value_sum": total_value_sum,
            "total_paid_sum": total_paid_sum,
            "total_remaining_sum": total_remaining_sum
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")

@api_router.get("/contratos/{contract_id}", response_model=Dict[str, Any])
async def get_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obter contrato específico por ID"""
    try:
        contract = await db.contracts.find_one({
            "id": contract_id,
            "user_id": current_user.id
        })
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        
        # Remove MongoDB _id field for JSON serialization
        if "_id" in contract:
            del contract["_id"]
        
        # Calculate totals
        contract_totals = calculate_contract_totals(contract)
        contract.update(contract_totals)
        
        return contract
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contrato: {str(e)}")

@api_router.put("/contratos/{contract_id}", response_model=Dict[str, Any])
async def update_contract(
    contract_id: str,
    contract_update: ContractUpdate,
    current_user: User = Depends(get_current_user)
):
    """Atualizar contrato existente"""
    try:
        # Check if contract exists
        existing_contract = await db.contracts.find_one({
            "id": contract_id,
            "user_id": current_user.id
        })
        
        if not existing_contract:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        
        # Prepare update data
        update_data = {}
        for field, value in contract_update.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update contract
        await db.contracts.update_one(
            {"id": contract_id, "user_id": current_user.id},
            {"$set": update_data}
        )
        
        # Get updated contract
        updated_contract = await db.contracts.find_one({
            "id": contract_id,
            "user_id": current_user.id
        })
        
        # Remove MongoDB _id field for JSON serialization
        if "_id" in updated_contract:
            del updated_contract["_id"]
        
        # Check and update status if needed
        new_status = await update_contract_status(contract_id, current_user.id)
        updated_contract["status"] = new_status
        
        # Calculate totals
        contract_totals = calculate_contract_totals(updated_contract)
        updated_contract.update(contract_totals)
        
        return {
            "message": "Contrato atualizado com sucesso!",
            "contract": updated_contract
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar contrato: {str(e)}")

@api_router.delete("/contratos/{contract_id}", response_model=Dict[str, str])
async def delete_contract(
    contract_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deletar contrato"""
    try:
        result = await db.contracts.delete_one({
            "id": contract_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        
        return {"message": "Contrato deletado com sucesso!"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar contrato: {str(e)}")

# ============================================================================
# 🐾 PET SHOP ENDPOINTS - PHASE 3
# ============================================================================

@api_router.post("/petshop/products", response_model=Dict[str, Any])
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    """Criar novo produto para o pet shop"""
    try:
        # Verificar se SKU já existe
        existing_product = await db.products.find_one({
            "user_id": current_user.id,
            "sku": product_data.sku
        })
        
        if existing_product:
            raise HTTPException(status_code=400, detail="SKU já existe para este usuário")
        
        # Criar produto
        product = Product(
            user_id=current_user.id,
            **product_data.dict()
        ).dict()
        
        await db.products.insert_one(product)
        
        # Remove MongoDB ObjectId for JSON serialization
        if "_id" in product:
            del product["_id"]
        
        return {
            "message": "Produto criado com sucesso!",
            "product": product
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {str(e)}")

@api_router.get("/petshop/products", response_model=List[Dict[str, Any]])
async def list_products(
    current_user: User = Depends(get_current_user),
    category: Optional[str] = None,
    low_stock: bool = False,
    active_only: bool = True
):
    """Listar produtos do pet shop com filtros"""
    try:
        query = {"user_id": current_user.id}
        
        if category:
            query["category"] = category
            
        if active_only:
            query["is_active"] = True
            
        if low_stock:
            # Produtos com estoque baixo
            products = await check_low_stock_products(current_user.id)
        else:
            products = await db.products.find(query).sort("name", 1).to_list(100)
        
        # Remove MongoDB ObjectId fields for JSON serialization
        for product in products:
            if "_id" in product:
                del product["_id"]
        
        return products
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar produtos: {str(e)}")

@api_router.get("/petshop/products/{product_id}", response_model=Dict[str, Any])
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obter produto específico"""
    try:
        product = await db.products.find_one({
            "id": product_id,
            "user_id": current_user.id
        })
        
        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        # Remove MongoDB ObjectId for JSON serialization
        if "_id" in product:
            del product["_id"]
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar produto: {str(e)}")

@api_router.put("/petshop/products/{product_id}", response_model=Dict[str, Any])
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_user)
):
    """Atualizar produto"""
    try:
        existing_product = await db.products.find_one({
            "id": product_id,
            "user_id": current_user.id
        })
        
        if not existing_product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        # Preparar dados para atualização
        update_data = {}
        for field, value in product_update.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.products.update_one(
            {"id": product_id, "user_id": current_user.id},
            {"$set": update_data}
        )
        
        # Buscar produto atualizado
        updated_product = await db.products.find_one({
            "id": product_id,
            "user_id": current_user.id
        })
        
        # Remove MongoDB ObjectId for JSON serialization
        if updated_product and "_id" in updated_product:
            del updated_product["_id"]
        
        return {
            "message": "Produto atualizado com sucesso!",
            "product": updated_product
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar produto: {str(e)}")

@api_router.delete("/petshop/products/{product_id}", response_model=Dict[str, str])
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deletar produto (soft delete)"""
    try:
        result = await db.products.update_one(
            {"id": product_id, "user_id": current_user.id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        return {"message": "Produto removido com sucesso!"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover produto: {str(e)}")

@api_router.post("/petshop/sales", response_model=Dict[str, Any])
async def create_sale(
    sale_data: SaleCreate,
    current_user: User = Depends(get_current_user)
):
    """Criar nova venda"""
    try:
        # Verificar estoque dos produtos
        for item in sale_data.items:
            product = await db.products.find_one({
                "id": item["product_id"],
                "user_id": current_user.id
            })
            
            if not product:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Produto {item.get('product_name', 'desconhecido')} não encontrado"
                )
            
            if product["current_stock"] < item["quantity"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Estoque insuficiente para {product['name']}. Disponível: {product['current_stock']}"
                )
        
        # Criar venda
        sale = Sale(
            user_id=current_user.id,
            receipt_number=generate_receipt_number(),
            **sale_data.dict()
        ).dict()
        
        await db.sales.insert_one(sale)
        
        # Remove MongoDB ObjectId for JSON serialization
        if "_id" in sale:
            del sale["_id"]
        
        # Atualizar estoque dos produtos
        for item in sale_data.items:
            await update_product_stock(
                item["product_id"], 
                current_user.id, 
                item["quantity"],
                f"Venda {sale['receipt_number']}"
            )
        
        # Criar transação financeira automática
        try:
            transaction_id = await create_financial_transaction_from_sale(sale, current_user.id)
            sale["financial_transaction_id"] = transaction_id
        except Exception as e:
            print(f"Erro ao criar transação financeira: {e}")
            # Venda continua mesmo se transação financeira falhar
        
        return {
            "message": "Venda realizada com sucesso!",
            "sale": sale,
            "receipt_number": sale["receipt_number"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar venda: {str(e)}")

@api_router.get("/petshop/sales", response_model=List[Dict[str, Any]])
async def list_sales(
    current_user: User = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    payment_method: Optional[str] = None
):
    """Listar vendas com filtros"""
    try:
        query = {"user_id": current_user.id}
        
        # Filtro por data
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date)
            query["sale_date"] = date_filter
        
        if payment_method:
            query["payment_method"] = payment_method
        
        sales = await db.sales.find(query).sort("sale_date", -1).to_list(100)
        
        # Remove MongoDB ObjectId fields for JSON serialization
        for sale in sales:
            if "_id" in sale:
                del sale["_id"]
        
        return sales
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar vendas: {str(e)}")

@api_router.get("/petshop/dashboard", response_model=Dict[str, Any])
async def get_petshop_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Dashboard do pet shop com estatísticas"""
    try:
        # Estatísticas de produtos
        total_products = await db.products.count_documents({
            "user_id": current_user.id,
            "is_active": True
        })
        
        low_stock_products = await check_low_stock_products(current_user.id)
        
        # Estatísticas de vendas (últimos 30 dias)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_sales = await db.sales.find({
            "user_id": current_user.id,
            "sale_date": {"$gte": thirty_days_ago}
        }).to_list(1000)
        
        total_sales_count = len(recent_sales)
        total_revenue = sum(sale["total"] for sale in recent_sales)
        
        # Top produtos vendidos
        product_sales = {}
        for sale in recent_sales:
            for item in sale["items"]:
                product_name = item["product_name"]
                if product_name not in product_sales:
                    product_sales[product_name] = {"quantity": 0, "revenue": 0}
                product_sales[product_name]["quantity"] += item["quantity"]
                product_sales[product_name]["revenue"] += item["total"]
        
        top_products = sorted(
            product_sales.items(), 
            key=lambda x: x[1]["quantity"], 
            reverse=True
        )[:5]
        
        # Remove MongoDB ObjectId fields from recent sales
        for sale in recent_sales:
            if "_id" in sale:
                del sale["_id"]
        
        # Remove MongoDB ObjectId fields from low stock products
        for product in low_stock_products:
            if "_id" in product:
                del product["_id"]
        
        return {
            "total_products": total_products,
            "low_stock_count": len(low_stock_products),
            "low_stock_products": low_stock_products,
            "total_sales_30_days": total_sales_count,
            "total_revenue_30_days": total_revenue,
            "top_products": top_products,
            "recent_sales": recent_sales[:10]  # Últimas 10 vendas
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar dashboard: {str(e)}")

@api_router.get("/petshop/receipt/{receipt_number}", response_model=Dict[str, Any])
async def get_receipt(
    receipt_number: str,
    current_user: User = Depends(get_current_user)
):
    """Obter comprovante de venda"""
    try:
        sale = await db.sales.find_one({
            "receipt_number": receipt_number,
            "user_id": current_user.id
        })
        
        if not sale:
            raise HTTPException(status_code=404, detail="Comprovante não encontrado")
        
        # Remove MongoDB ObjectId for JSON serialization
        if "_id" in sale:
            del sale["_id"]
        
        return {
            "sale": sale,
            "business_info": {
                "name": "Pet Shop",
                "owner": current_user.name,
                "date": sale["sale_date"].isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar comprovante: {str(e)}")

@api_router.get("/petshop/stock-movement", response_model=List[Dict[str, Any]])
async def get_stock_movements(
    current_user: User = Depends(get_current_user),
    product_id: Optional[str] = None,
    movement_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
):
    """Listar movimentações de estoque com filtros"""
    try:
        query = {"user_id": current_user.id}
        
        if product_id:
            query["product_id"] = product_id
            
        if movement_type:
            query["movement_type"] = movement_type
            
        # Filtro por data
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date)
            query["created_at"] = date_filter
        
        movements = await db.stock_movements.find(query).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Remove MongoDB ObjectId fields and enrich with product info
        for movement in movements:
            if "_id" in movement:
                del movement["_id"]
                
            # Get product info
            product = await db.products.find_one({"id": movement["product_id"]})
            if product:
                movement["product_name"] = product.get("name", "Produto não encontrado")
                movement["product_sku"] = product.get("sku", "N/A")
        
        return movements
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar movimentações: {str(e)}")

@api_router.post("/petshop/stock-movement", response_model=Dict[str, Any])
async def create_stock_movement(
    movement_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Criar movimentação manual de estoque"""
    try:
        product_id = movement_data.get("product_id")
        movement_type = movement_data.get("movement_type")
        quantity = movement_data.get("quantity")
        reason = movement_data.get("reason")
        
        if not all([product_id, movement_type, quantity, reason]):
            raise HTTPException(status_code=400, detail="Todos os campos são obrigatórios: product_id, movement_type, quantity, reason")
        
        # Verificar se produto existe
        product = await db.products.find_one({
            "id": product_id,
            "user_id": current_user.id
        })
        
        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        previous_stock = product["current_stock"]
        
        # Calcular novo estoque baseado no tipo de movimentação
        if movement_type == "entrada":
            new_stock = previous_stock + int(quantity)
        elif movement_type == "saída":
            new_stock = previous_stock - int(quantity)
            if new_stock < 0:
                raise HTTPException(status_code=400, detail="Estoque não pode ficar negativo")
        elif movement_type == "ajuste":
            new_stock = int(quantity)  # Ajuste absoluto
        else:
            raise HTTPException(status_code=400, detail="Tipo de movimentação inválido. Use: entrada, saída, ajuste")
        
        # Atualizar estoque do produto
        await db.products.update_one(
            {"id": product_id, "user_id": current_user.id},
            {"$set": {"current_stock": new_stock, "updated_at": datetime.utcnow()}}
        )
        
        # Registrar movimentação
        movement = StockMovement(
            user_id=current_user.id,
            product_id=product_id,
            movement_type=movement_type,
            quantity=abs(int(quantity)),
            reason=reason,
            previous_stock=previous_stock,
            new_stock=new_stock,
            created_by=current_user.id
        )
        
        await db.stock_movements.insert_one(movement.dict())
        
        # Remove MongoDB ObjectId for JSON serialization
        movement_dict = movement.dict()
        if "_id" in movement_dict:
            del movement_dict["_id"]
        
        return {
            "message": "Movimentação de estoque registrada com sucesso!",
            "movement": movement_dict,
            "product_name": product["name"],
            "previous_stock": previous_stock,
            "new_stock": new_stock
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar movimentação: {str(e)}")

@api_router.get("/petshop/stock-alert", response_model=Dict[str, Any])
async def get_stock_alerts(
    current_user: User = Depends(get_current_user)
):
    """Obter alertas de estoque baixo"""
    try:
        # Produtos com estoque baixo
        low_stock_products = await check_low_stock_products(current_user.id)
        
        # Produtos com estoque zerado
        zero_stock_products = await db.products.find({
            "user_id": current_user.id,
            "is_active": True,
            "current_stock": 0
        }).to_list(100)
        
        # Produtos próximos ao vencimento (30 dias)
        thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
        expiring_products = await db.products.find({
            "user_id": current_user.id,
            "is_active": True,
            "expiry_date": {
                "$lte": thirty_days_from_now,
                "$gte": datetime.utcnow()
            }
        }).to_list(100)
        
        # Remove MongoDB ObjectId fields
        for product_list in [low_stock_products, zero_stock_products, expiring_products]:
            for product in product_list:
                if "_id" in product:
                    del product["_id"]
        
        # Calcular estatísticas de alerta
        total_products = await db.products.count_documents({
            "user_id": current_user.id,
            "is_active": True
        })
        
        alert_summary = {
            "total_products": total_products,
            "low_stock_count": len(low_stock_products),
            "zero_stock_count": len(zero_stock_products),
            "expiring_count": len(expiring_products),
            "alert_level": "high" if len(zero_stock_products) > 0 else "medium" if len(low_stock_products) > 0 else "low"
        }
        
        return {
            "alert_summary": alert_summary,
            "low_stock_products": low_stock_products,
            "zero_stock_products": zero_stock_products,
            "expiring_products": expiring_products,
            "recommendations": [
                "Reabasteça produtos com estoque baixo",
                "Verifique fornecedores para produtos em falta",
                "Monitore produtos próximos ao vencimento",
                "Configure alertas automáticos para estoque mínimo"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter alertas de estoque: {str(e)}")

@api_router.get("/petshop/statistics", response_model=Dict[str, Any])
async def get_petshop_statistics(
    current_user: User = Depends(get_current_user),
    period: str = "30"  # days
):
    """Obter estatísticas detalhadas do pet shop"""
    try:
        period_days = int(period)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Estatísticas de produtos
        total_products = await db.products.count_documents({
            "user_id": current_user.id,
            "is_active": True
        })
        
        products_by_category = await db.products.aggregate([
            {"$match": {"user_id": current_user.id, "is_active": True}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}, "total_stock": {"$sum": "$current_stock"}}},
            {"$sort": {"count": -1}}
        ]).to_list(100)
        
        # Estatísticas de vendas
        sales_pipeline = [
            {"$match": {"user_id": current_user.id, "sale_date": {"$gte": start_date}}},
            {"$group": {
                "_id": None,
                "total_sales": {"$sum": 1},
                "total_revenue": {"$sum": "$total"},
                "avg_sale_value": {"$avg": "$total"}
            }}
        ]
        
        sales_stats = await db.sales.aggregate(sales_pipeline).to_list(1)
        sales_summary = sales_stats[0] if sales_stats else {
            "total_sales": 0,
            "total_revenue": 0,
            "avg_sale_value": 0
        }
        
        # Vendas por método de pagamento
        payment_method_stats = await db.sales.aggregate([
            {"$match": {"user_id": current_user.id, "sale_date": {"$gte": start_date}}},
            {"$group": {"_id": "$payment_method", "count": {"$sum": 1}, "revenue": {"$sum": "$total"}}},
            {"$sort": {"count": -1}}
        ]).to_list(100)
        
        # Produtos mais vendidos
        top_products_pipeline = [
            {"$match": {"user_id": current_user.id, "sale_date": {"$gte": start_date}}},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_name",
                "quantity_sold": {"$sum": "$items.quantity"},
                "revenue": {"$sum": "$items.total"}
            }},
            {"$sort": {"quantity_sold": -1}},
            {"$limit": 10}
        ]
        
        top_products = await db.sales.aggregate(top_products_pipeline).to_list(10)
        
        # Vendas por dia (últimos 7 dias para gráfico)
        daily_sales_pipeline = [
            {"$match": {"user_id": current_user.id, "sale_date": {"$gte": datetime.utcnow() - timedelta(days=7)}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$sale_date"}},
                "sales_count": {"$sum": 1},
                "revenue": {"$sum": "$total"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_sales = await db.sales.aggregate(daily_sales_pipeline).to_list(7)
        
        # Alertas de estoque
        low_stock_count = len(await check_low_stock_products(current_user.id))
        
        # Movimentações de estoque recentes
        recent_movements = await db.stock_movements.find({
            "user_id": current_user.id
        }).sort("created_at", -1).limit(10).to_list(10)
        
        # Remove MongoDB ObjectId fields
        for movement in recent_movements:
            if "_id" in movement:
                del movement["_id"]
        
        return {
            "period_days": period_days,
            "products": {
                "total_products": total_products,
                "products_by_category": products_by_category,
                "low_stock_alerts": low_stock_count
            },
            "sales": {
                "summary": sales_summary,
                "payment_methods": payment_method_stats,
                "top_products": top_products,
                "daily_sales": daily_sales
            },
            "inventory": {
                "recent_movements": recent_movements,
                "total_stock_value": 0  # Could be calculated if needed
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

# ============================================================================
# 📧 EMAIL TEST ENDPOINT
# ============================================================================

class EmailTestRequest(BaseModel):
    to: EmailStr
    subject: Optional[str] = "Teste de E-mail - OrçaZenFinanceiro"

@api_router.post("/test-email")
async def test_email_sending(
    email_request: EmailTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Test email sending functionality"""
    try:
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                <h2>🎉 Teste de E-mail Bem-sucedido!</h2>
            </div>
            <div style="padding: 20px;">
                <p>Olá!</p>
                <p>Este é um e-mail de teste do sistema <strong>OrçaZenFinanceiro</strong>.</p>
                <p>Se você recebeu este e-mail, significa que o sistema de envio está funcionando corretamente!</p>
                
                <div style="background: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0;">
                    <h3>✅ Status do Sistema:</h3>
                    <ul>
                        <li><strong>SMTP:</strong> Configurado e funcional</li>
                        <li><strong>Usuário Teste:</strong> {current_user.email}</li>
                        <li><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</li>
                        <li><strong>Servidor:</strong> {SMTP_SERVER}:{SMTP_PORT}</li>
                    </ul>
                </div>
                
                <p>Atenciosamente,<br>
                <strong>Equipe OrçaZenFinanceiro</strong></p>
            </div>
            <div style="background: #6c757d; color: white; text-align: center; padding: 10px; font-size: 12px;">
                Este é um e-mail automatizado de teste. Não é necessário responder.
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        TESTE DE E-MAIL - ORÇAZENFINANCEIRO
        
        Olá!
        
        Este é um e-mail de teste do sistema OrçaZenFinanceiro.
        Se você recebeu este e-mail, o sistema de envio está funcionando corretamente!
        
        Status do Sistema:
        - SMTP: Configurado e funcional  
        - Usuário Teste: {current_user.email}
        - Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        - Servidor: {SMTP_SERVER}:{SMTP_PORT}
        
        Atenciosamente,
        Equipe OrçaZenFinanceiro
        """
        
        # Send test email
        success = await send_email(
            to_email=email_request.to,
            subject=email_request.subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            return {
                "success": True,
                "message": f"E-mail de teste enviado com sucesso para {email_request.to}",
                "email_enabled": EMAIL_ENABLED,
                "smtp_server": SMTP_SERVER,
                "smtp_port": SMTP_PORT,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Falha ao enviar e-mail de teste",
                "email_enabled": EMAIL_ENABLED
            }
            
    except Exception as e:
        logger.error(f"Erro no teste de e-mail: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno no envio de e-mail: {str(e)}"
        )

# ============================================================================
# 🔄 AUTOMATIC RECURRENCE SYSTEM ENDPOINTS - PHASE 2
# ============================================================================

@api_router.post("/recurrence/rules", response_model=Dict[str, Any])
async def create_recurrence_rule(
    rule_data: RecurrenceRuleCreate,
    current_user: User = Depends(get_current_user)
):
    """Criar nova regra de recorrência automática"""
    try:
        # Validar padrão de recorrência
        valid_patterns = ["diario", "semanal", "mensal", "anual"]
        if rule_data.recurrence_pattern not in valid_patterns:
            raise HTTPException(
                status_code=400, 
                detail=f"Padrão inválido. Use: {', '.join(valid_patterns)}"
            )
        
        # Validar tipo de transação
        if rule_data.transaction_type not in ["Receita", "Despesa"]:
            raise HTTPException(
                status_code=400, 
                detail="Tipo deve ser 'Receita' ou 'Despesa'"
            )
        
        # Verificar se conta existe
        account = await db.accounts.find_one({
            "id": rule_data.account_id,
            "user_id": current_user.id,
            "is_active": True
        })
        if not account:
            raise HTTPException(status_code=404, detail="Conta não encontrada")
        
        # Calcular primeira data de execução
        next_execution = calculate_next_execution_date(
            rule_data.start_date, rule_data.recurrence_pattern, 
            rule_data.interval
        )
        
        # Criar regra de recorrência
        rule = RecurrenceRule(
            user_id=current_user.id,
            next_execution_date=next_execution,
            **rule_data.dict()
        )
        
        await db.recurrence_rules.insert_one(rule.dict())
        
        # Remove MongoDB ObjectId for JSON serialization
        rule_dict = rule.dict()
        if "_id" in rule_dict:
            del rule_dict["_id"]
        
        return {
            "message": "Regra de recorrência criada com sucesso!",
            "rule": rule_dict,
            "next_execution_date": next_execution.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar regra: {str(e)}")

@api_router.get("/recurrence/rules", response_model=List[Dict[str, Any]])
async def list_recurrence_rules(
    current_user: User = Depends(get_current_user),
    is_active: Optional[bool] = None,
    recurrence_pattern: Optional[str] = None
):
    """Listar regras de recorrência do usuário"""
    try:
        query = {"user_id": current_user.id}
        
        if is_active is not None:
            query["is_active"] = is_active
            
        if recurrence_pattern:
            query["recurrence_pattern"] = recurrence_pattern
        
        rules = await db.recurrence_rules.find(query).sort("created_at", -1).to_list(100)
        
        # Remove MongoDB ObjectId fields and enrich with account info
        for rule in rules:
            if "_id" in rule:
                del rule["_id"]
            
            # Adicionar informações da conta
            account = await db.accounts.find_one({"id": rule["account_id"]})
            if account:
                rule["account_name"] = account.get("name", "Conta não encontrada")
                rule["account_type"] = account.get("type", "N/A")
            
            # Adicionar informações da categoria
            if rule.get("category_id"):
                category = await db.categories.find_one({"id": rule["category_id"]})
                if category:
                    rule["category_name"] = category.get("name", "Categoria não encontrada")
        
        return rules
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar regras: {str(e)}")

@api_router.get("/recurrence/rules/{rule_id}", response_model=Dict[str, Any])
async def get_recurrence_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obter regra de recorrência específica"""
    try:
        rule = await db.recurrence_rules.find_one({
            "id": rule_id,
            "user_id": current_user.id
        })
        
        if not rule:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
        
        # Remove MongoDB ObjectId
        if "_id" in rule:
            del rule["_id"]
        
        # Adicionar informações adicionais
        account = await db.accounts.find_one({"id": rule["account_id"]})
        if account:
            rule["account_name"] = account.get("name", "Conta não encontrada")
            rule["account_type"] = account.get("type", "N/A")
        
        if rule.get("category_id"):
            category = await db.categories.find_one({"id": rule["category_id"]})
            if category:
                rule["category_name"] = category.get("name", "Categoria não encontrada")
        
        return rule
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar regra: {str(e)}")

@api_router.put("/recurrence/rules/{rule_id}", response_model=Dict[str, Any])
async def update_recurrence_rule(
    rule_id: str,
    rule_update: RecurrenceRuleUpdate,
    current_user: User = Depends(get_current_user)
):
    """Atualizar regra de recorrência"""
    try:
        # Verificar se regra existe
        existing_rule = await db.recurrence_rules.find_one({
            "id": rule_id,
            "user_id": current_user.id
        })
        
        if not existing_rule:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
        
        # Preparar dados para atualização
        update_data = {}
        for field, value in rule_update.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # Se padrão ou intervalo mudaram, recalcular próxima execução
        if "recurrence_pattern" in update_data or "interval" in update_data:
            new_pattern = update_data.get("recurrence_pattern", existing_rule["recurrence_pattern"])
            new_interval = update_data.get("interval", existing_rule["interval"])
            
            next_execution = calculate_next_execution_date(
                existing_rule["next_execution_date"], 
                new_pattern, 
                new_interval,
                existing_rule.get("last_execution_date")
            )
            update_data["next_execution_date"] = next_execution
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.recurrence_rules.update_one(
            {"id": rule_id, "user_id": current_user.id},
            {"$set": update_data}
        )
        
        # Buscar regra atualizada
        updated_rule = await db.recurrence_rules.find_one({
            "id": rule_id,
            "user_id": current_user.id
        })
        
        if "_id" in updated_rule:
            del updated_rule["_id"]
        
        return {
            "message": "Regra de recorrência atualizada com sucesso!",
            "rule": updated_rule
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar regra: {str(e)}")

@api_router.delete("/recurrence/rules/{rule_id}", response_model=Dict[str, str])
async def delete_recurrence_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deletar regra de recorrência"""
    try:
        result = await db.recurrence_rules.delete_one({
            "id": rule_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
        
        # Também deletar sugestões pendentes relacionadas
        await db.pending_recurrences.delete_many({
            "recurrence_rule_id": rule_id,
            "user_id": current_user.id
        })
        
        return {"message": "Regra de recorrência deletada com sucesso!"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar regra: {str(e)}")

@api_router.get("/recurrence/rules/{rule_id}/preview", response_model=Dict[str, Any])
async def preview_recurrence_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    months_ahead: int = 12
):
    """Gerar preview das próximas transações de uma regra de recorrência"""
    try:
        rule_data = await db.recurrence_rules.find_one({
            "id": rule_id,
            "user_id": current_user.id
        })
        
        if not rule_data:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
        
        rule = RecurrenceRule(**rule_data)
        
        # Gerar preview
        preview_transactions = generate_recurrence_preview(rule, months_ahead)
        
        return {
            "rule_id": rule_id,
            "rule_name": rule.name,
            "preview_period_months": months_ahead,
            "total_transactions": len(preview_transactions),
            "total_value": sum(t["value"] for t in preview_transactions),
            "transactions": preview_transactions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar preview: {str(e)}")

@api_router.get("/recurrence/pending", response_model=List[Dict[str, Any]])
async def list_pending_recurrences(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None
):
    """Listar recorrências pendentes de confirmação"""
    try:
        query = {"user_id": current_user.id}
        
        if status:
            query["status"] = status
        else:
            query["status"] = "pending"  # Apenas pendentes por padrão
        
        pending = await db.pending_recurrences.find(query).sort("created_at", -1).to_list(100)
        
        # Remove MongoDB ObjectId and enrich with rule info
        for item in pending:
            if "_id" in item:
                del item["_id"]
            
            # Adicionar informações da regra
            rule = await db.recurrence_rules.find_one({"id": item["recurrence_rule_id"]})
            if rule:
                item["rule_name"] = rule.get("name", "Regra não encontrada")
                item["rule_pattern"] = rule.get("recurrence_pattern", "N/A")
        
        return pending
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar pendências: {str(e)}")

@api_router.post("/recurrence/confirm", response_model=Dict[str, Any])
async def confirm_pending_recurrences(
    confirmation: RecurrenceConfirmation,
    current_user: User = Depends(get_current_user)
):
    """Confirmar ou rejeitar recorrências pendentes"""
    try:
        results = {
            "processed": 0,
            "approved": 0,
            "rejected": 0,
            "created_transactions": [],
            "errors": []
        }
        
        if confirmation.action in ["approve_all", "reject_all"]:
            # Processar todas as pendências
            pending_list = await db.pending_recurrences.find({
                "user_id": current_user.id,
                "status": "pending"
            }).to_list(100)
            
            pending_ids = [item["id"] for item in pending_list]
        else:
            pending_ids = confirmation.pending_recurrence_ids
        
        for pending_id in pending_ids:
            try:
                pending = await db.pending_recurrences.find_one({
                    "id": pending_id,
                    "user_id": current_user.id,
                    "status": "pending"
                })
                
                if not pending:
                    results["errors"].append(f"Pendência {pending_id} não encontrada")
                    continue
                
                results["processed"] += 1
                
                if confirmation.action in ["approve", "approve_all"]:
                    # Buscar regra para criar transação
                    rule = await db.recurrence_rules.find_one({
                        "id": pending["recurrence_rule_id"]
                    })
                    
                    if rule:
                        rule_obj = RecurrenceRule(**rule)
                        transaction_id = await create_transaction_from_recurrence(
                            rule_obj, pending["suggested_date"], current_user.id
                        )
                        
                        results["created_transactions"].append({
                            "transaction_id": transaction_id,
                            "description": pending["transaction_data"]["description"],
                            "value": pending["transaction_data"]["value"],
                            "date": pending["suggested_date"]
                        })
                        
                        # Atualizar regra
                        await db.recurrence_rules.update_one(
                            {"id": rule["id"]},
                            {"$set": {
                                "last_execution_date": pending["suggested_date"],
                                "total_executions": rule["total_executions"] + 1,
                                "updated_at": datetime.utcnow()
                            }}
                        )
                    
                    # Marcar como aprovada
                    await db.pending_recurrences.update_one(
                        {"id": pending_id},
                        {"$set": {"status": "approved"}}
                    )
                    results["approved"] += 1
                    
                else:  # reject or reject_all
                    # Marcar como rejeitada
                    await db.pending_recurrences.update_one(
                        {"id": pending_id},
                        {"$set": {"status": "rejected"}}
                    )
                    results["rejected"] += 1
                
            except Exception as e:
                error_msg = f"Erro ao processar {pending_id}: {str(e)}"
                results["errors"].append(error_msg)
        
        return {
            "message": f"Processamento concluído: {results['approved']} aprovadas, {results['rejected']} rejeitadas",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@api_router.post("/recurrence/process", response_model=Dict[str, Any])
async def process_user_recurrences(
    current_user: User = Depends(get_current_user)
):
    """Processar todas as recorrências pendentes do usuário (manual trigger)"""
    try:
        results = await process_pending_recurrences(current_user.id)
        
        return {
            "message": "Processamento de recorrências concluído!",
            "results": results,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@api_router.get("/recurrence/statistics", response_model=Dict[str, Any])
async def get_recurrence_statistics(
    current_user: User = Depends(get_current_user)
):
    """Obter estatísticas do sistema de recorrência"""
    try:
        # Estatísticas de regras
        total_rules = await db.recurrence_rules.count_documents({"user_id": current_user.id})
        active_rules = await db.recurrence_rules.count_documents({
            "user_id": current_user.id,
            "is_active": True
        })
        
        # Estatísticas por padrão
        pattern_stats = await db.recurrence_rules.aggregate([
            {"$match": {"user_id": current_user.id, "is_active": True}},
            {"$group": {"_id": "$recurrence_pattern", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(10)
        
        # Estatísticas de pendências
        pending_count = await db.pending_recurrences.count_documents({
            "user_id": current_user.id,
            "status": "pending"
        })
        
        # Próximas execuções (próximos 7 dias)
        next_week = datetime.utcnow() + timedelta(days=7)
        upcoming_executions = await db.recurrence_rules.find({
            "user_id": current_user.id,
            "is_active": True,
            "next_execution_date": {"$lte": next_week}
        }).sort("next_execution_date", 1).to_list(10)
        
        # Remove MongoDB ObjectId fields
        for execution in upcoming_executions:
            if "_id" in execution:
                del execution["_id"]
        
        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "inactive_rules": total_rules - active_rules,
            "pattern_distribution": pattern_stats,
            "pending_confirmations": pending_count,
            "upcoming_executions": upcoming_executions,
            "next_7_days_count": len(upcoming_executions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

# ============================================================================
# 🧹 ADMINISTRATIVE DATA CLEANUP ENDPOINTS (TEMPORARY)
# ============================================================================

@api_router.post("/admin/cleanup-data")
async def cleanup_example_data(current_user: User = Depends(get_current_user)):
    """
    Endpoint administrativo temporário para limpeza de dados de exemplo.
    Mantém apenas o usuário hpdanielvb@gmail.com e remove todos os outros usuários e dados relacionados.
    """
    try:
        # Verificar se o usuário atual é o usuário principal
        if current_user.email != "hpdanielvb@gmail.com":
            raise HTTPException(
                status_code=403, 
                detail="Acesso negado. Apenas o usuário principal pode executar esta operação."
            )
        
        cleanup_summary = {
            "users_removed": 0,
            "transactions_removed": 0,
            "accounts_removed": 0,
            "categories_removed": 0,
            "goals_removed": 0,
            "budgets_removed": 0,
            "sales_removed": 0,
            "products_removed": 0,
            "contracts_removed": 0,
            "import_sessions_removed": 0,
            "stock_movements_removed": 0,
            "main_user_kept": current_user.email
        }
        
        print(f"[CLEANUP] Iniciando limpeza de dados de exemplo...")
        print(f"[CLEANUP] Usuário principal mantido: {current_user.email}")
        
        # Buscar todos os usuários exceto o principal
        other_users = await db.users.find({"email": {"$ne": "hpdanielvb@gmail.com"}}).to_list(1000)
        other_user_ids = [user["id"] for user in other_users]
        
        print(f"[CLEANUP] Encontrados {len(other_users)} usuários para remoção")
        
        if other_user_ids:
            # Remover transações de outros usuários
            transactions_result = await db.transactions.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["transactions_removed"] = transactions_result.deleted_count
            
            # Remover contas de outros usuários
            accounts_result = await db.accounts.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["accounts_removed"] = accounts_result.deleted_count
            
            # Remover categorias de outros usuários (exceto categorias customizadas importantes)
            categories_result = await db.categories.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["categories_removed"] = categories_result.deleted_count
            
            # Remover metas de outros usuários
            goals_result = await db.goals.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["goals_removed"] = goals_result.deleted_count
            
            # Remover orçamentos de outros usuários
            budgets_result = await db.budgets.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["budgets_removed"] = budgets_result.deleted_count
            
            # Remover vendas de outros usuários
            sales_result = await db.sales.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["sales_removed"] = sales_result.deleted_count
            
            # Remover produtos de outros usuários
            products_result = await db.products.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["products_removed"] = products_result.deleted_count
            
            # Remover contratos de outros usuários
            contracts_result = await db.contracts.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["contracts_removed"] = contracts_result.deleted_count
            
            # Remover sessões de importação de outros usuários
            import_sessions_result = await db.import_sessions.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["import_sessions_removed"] = import_sessions_result.deleted_count
            
            # Remover movimentações de estoque de outros usuários
            stock_movements_result = await db.stock_movements.delete_many({"user_id": {"$in": other_user_ids}})
            cleanup_summary["stock_movements_removed"] = stock_movements_result.deleted_count
            
            # Por último, remover os outros usuários
            users_result = await db.users.delete_many({"id": {"$in": other_user_ids}})
            cleanup_summary["users_removed"] = users_result.deleted_count
        
        print(f"[CLEANUP] Limpeza concluída com sucesso!")
        print(f"[CLEANUP] Resumo: {cleanup_summary}")
        
        return {
            "message": "Limpeza de dados de exemplo concluída com sucesso!",
            "summary": cleanup_summary,
            "main_user_preserved": {
                "email": current_user.email,
                "name": current_user.name,
                "id": current_user.id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CLEANUP ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro durante limpeza: {str(e)}")

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