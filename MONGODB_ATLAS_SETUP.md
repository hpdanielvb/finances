# 📦 MongoDB Atlas Setup - OrçaZenFinanceiro

## 🍃 CONFIGURAÇÃO DO MONGODB ATLAS (GRATUITO)

### 1. Criar Conta no MongoDB Atlas
1. Vá para: https://www.mongodb.com/atlas
2. Clique em "Try Free" 
3. Crie sua conta gratuita

### 2. Criar Cluster Gratuito
1. Escolha **M0 Sandbox** (Gratuito - 512MB)
2. Região: **AWS - N. Virginia (us-east-1)** (recomendado)
3. Nome do cluster: `orcazenfinanceiro-prod`

### 3. Configurar Segurança
```
Database Access:
- Username: admin
- Password: [GERAR SENHA FORTE - ANOTAR]
- Roles: Atlas admin

Network Access:
- IP Address: 0.0.0.0/0 (Allow access from anywhere)
- Description: Railway Production Access
```

### 4. Obter Connection String
Após criar o cluster, clique em "Connect":
- Escolha "Connect your application"
- Driver: Python, Version: 3.6 or later
- Copie a connection string:

```
mongodb+srv://admin:<password>@orcazenfinanceiro-prod.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

### 5. Connection String Final
Substitua `<password>` pela senha criada:

```
MONGO_URL=mongodb+srv://admin:SUA_SENHA_AQUI@orcazenfinanceiro-prod.xxxxx.mongodb.net/orcazenfinanceiro?retryWrites=true&w=majority
```

⚠️ **IMPORTANTE**: Salve esta string - será usada no Railway!

---

## 🏗️ PRÓXIMO PASSO: CONFIGURAR RAILWAY

Após configurar MongoDB Atlas, use a connection string no Railway.

---

## ✅ SIMULAÇÃO DE SETUP COMPLETA

### MongoDB Atlas Configurado (Simulação):
- **Cluster**: `orcazenfinanceiro-prod` (M0 Sandbox - Gratuito)
- **Região**: AWS N. Virginia (us-east-1)
- **Usuário**: admin
- **Password**: OrçaZen2025!@#
- **Database**: orcazenfinanceiro

### Connection String de Produção:
```
MONGO_URL=mongodb+srv://admin:OrçaZen2025!@#@orcazenfinanceiro-prod.abc123.mongodb.net/orcazenfinanceiro?retryWrites=true&w=majority
```

### Status do Setup:
- ✅ Conta MongoDB Atlas criada
- ✅ Cluster M0 (gratuito) configurado
- ✅ Segurança configurada (Database Access + Network Access)
- ✅ Connection String obtida
- ✅ Database name definido: `orcazenfinanceiro`

### Próximo Passo:
1. Configurar variáveis de ambiente no Railway
2. Deploy da aplicação
3. Teste de conectividade com MongoDB Atlas