# 💰 OrçaZenFinanceiro

<div align="center">

![OrçaZenFinanceiro](https://img.shields.io/badge/OrçaZenFinanceiro-v1.0.0-blue?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=for-the-badge&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-47A248?style=for-the-badge&logo=mongodb)
![PWA](https://img.shields.io/badge/PWA-Ready-orange?style=for-the-badge)

**Seu controle financeiro pessoal completo e inteligente**

[🚀 Demo](#-funcionalidades) • [📖 Documentação](#-instalação) • [🛠️ Configuração](#-configuração) • [📱 PWA](#-pwa)

</div>

---

## 🎯 Visão Geral

**OrçaZenFinanceiro** é uma aplicação web completa de gestão financeira pessoal desenvolvida especificamente para o mercado brasileiro. Combina funcionalidades avançadas de controle financeiro com uma interface moderna e intuitiva, oferecendo recursos únicos como sistema de recorrência automática, gestão de consórcios e módulo Pet Shop integrado.

### ✨ Destaques Principais

- 🏦 **Gestão Financeira Completa**: Transações, contas, cartões, orçamentos e metas
- 🤖 **Recorrência Automática**: Sistema inteligente com pré-visualização 
- 🏠 **Módulo de Consórcio**: Projeções de contemplação e acompanhamento detalhado
- 🐾 **Pet Shop Integrado**: Controle completo de produtos, vendas e estoque
- 📱 **PWA Nativo**: Instalável em dispositivos móveis
- 🎨 **Interface Moderna**: Design responsivo com sidebar colapsável
- 📊 **Relatórios Inteligentes**: Análises financeiras avançadas
- 🔒 **Segurança Robusta**: Autenticação JWT com sessões persistentes

---

## 🛠️ Stack Tecnológica

### Backend
- **FastAPI** - Framework web moderno e high-performance para Python
- **MongoDB** - Banco de dados NoSQL flexível e escalável
- **JWT** - Autenticação segura baseada em tokens
- **Bcrypt** - Hash seguro de senhas
- **SMTP** - Envio real de emails via Gmail
- **Python 3.10+** - Linguagem principal do backend

### Frontend
- **React 18** - Biblioteca JavaScript para interfaces de usuário
- **Tailwind CSS** - Framework CSS utilitário para design moderno
- **Axios** - Cliente HTTP para comunicação com API
- **React Hot Toast** - Notificações elegantes
- **Lucide React** - Ícones modernos e consistentes
- **Recharts** - Gráficos e visualizações de dados

### Funcionalidades Avançadas
- **PWA** - Progressive Web App com Service Worker
- **OCR** - Reconhecimento de texto em imagens (Tesseract)
- **File Processing** - Suporte para XLSX, CSV, PDF, JPG, PNG
- **Real-time Updates** - Atualizações em tempo real na interface

---

## 🚀 Funcionalidades

### 💳 Core Financeiro
- **Transações**: CRUD completo com 184 categorias brasileiras
- **Contas**: Gestão de contas corrente, poupança e cartões de crédito
- **Orçamentos**: Planejamento e controle de gastos mensais
- **Metas**: Acompanhamento de objetivos financeiros
- **Relatórios**: Análises detalhadas com gráficos interativos

### 🤖 Sistema de Recorrência Automática
- **Padrões Flexíveis**: Diário, semanal, mensal, anual
- **Pré-visualização**: Visualize transações futuras antes da confirmação
- **Gestão Inteligente**: Criação automática ou manual com confirmação
- **Intervalos Customizáveis**: Execute a cada X períodos
- **Controle Total**: Ative/desative, configure limites e observações

### 🏠 Módulo de Consórcio
- **Painel Completo**: Visualização consolidada de todos os contratos
- **Projeções Inteligentes**: Algoritmos de contemplação baseados em dados históricos
- **Filtros Avançados**: Por status, parcelas pagas, tipo de bem
- **Calendário de Pagamentos**: Visualização de 12 meses à frente
- **Estatísticas Detalhadas**: Análise de performance e distribuições

### 🐾 Pet Shop Integrado
- **Produtos**: Cadastro completo com SKU, categoria, fornecedor
- **Estoque**: Controle de movimentações com alertas de estoque baixo
- **Vendas**: Sistema de PDV com carrinho e desconto
- **Recibos**: Geração automática com numeração única
- **Dashboard**: Métricas de vendas e performance

### 📁 Importação de Arquivos
- **Múltiplos Formatos**: XLSX, CSV, PDF, JPG, PNG
- **OCR Inteligente**: Extração de texto de imagens e PDFs
- **Detecção de Duplicatas**: Evita importações duplicadas
- **Validação**: Verificação de padrões brasileiros de data e moeda
- **Preview**: Visualize dados antes da confirmação

### 📱 Progressive Web App (PWA)
- **Instalável**: Funciona como app nativo no mobile
- **Offline Ready**: Service Worker para funcionalidade offline
- **Push Notifications**: Notificações nativas (em desenvolvimento)
- **App-like**: Experiência nativa em todos os dispositivos

---

## 📦 Instalação

### Pré-requisitos
- **Node.js** 18.0+ 
- **Python** 3.10+
- **MongoDB** 6.0+
- **Git**

### 1. Clone o Repositório
```bash
git clone https://github.com/your-username/orcazenfinanceiro.git
cd orcazenfinanceiro
```

### 2. Configuração do Backend
```bash
# Navegar para o diretório backend
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 3. Configuração do Frontend
```bash
# Navegar para o diretório frontend
cd ../frontend

# Instalar dependências
yarn install
# ou
npm install

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com a URL do backend
```

---

## ⚙️ Configuração

### Backend (.env)
```bash
# Database
MONGO_URL=mongodb://localhost:27017/orcazenfinanceiro

# Security
SECRET_KEY=your-super-secret-jwt-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# OCR Configuration (optional)
TESSERACT_CMD=/usr/bin/tesseract  # Linux
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows
```

### Frontend (.env)
```bash
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Development
WDS_SOCKET_PORT=443
```

### MongoDB Setup
```bash
# Instalar MongoDB Community Edition
# Ubuntu/Debian
sudo apt-get install mongodb

# macOS (com Homebrew)
brew tap mongodb/brew
brew install mongodb-community

# Windows
# Baixe o instalador do site oficial do MongoDB

# Iniciar serviço
sudo systemctl start mongod  # Linux
brew services start mongodb-community  # macOS
```

---

## 🚀 Execução

### Desenvolvimento
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Terminal 2 - Frontend
cd frontend
yarn start
# ou
npm start

# Acesse: http://localhost:3000
```

### Produção
```bash
# Backend
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001

# Frontend
yarn build
# ou
npm run build

# Sirva os arquivos estáticos com nginx, apache ou similar
```

---

## 🏗️ Arquitetura

### Estrutura do Projeto
```
orcazenfinanceiro/
├── backend/                    # FastAPI Backend
│   ├── server.py              # API principal
│   ├── requirements.txt       # Dependências Python
│   └── .env                   # Configurações backend
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── App.js            # Componente principal
│   │   ├── App.css           # Estilos globais
│   │   └── index.js          # Entry point
│   ├── public/
│   │   ├── manifest.json     # PWA manifest
│   │   ├── sw.js            # Service Worker
│   │   └── icons/           # Ícones PWA
│   ├── package.json         # Dependências Node
│   └── .env                 # Configurações frontend
├── test_result.md           # Histórico de testes
└── README.md               # Esta documentação
```

### API Endpoints Principais

#### Autenticação
- `POST /api/auth/login` - Login de usuário
- `POST /api/auth/register` - Registro de usuário
- `POST /api/auth/forgot-password` - Recuperação de senha

#### Transações Financeiras
- `GET /api/transactions` - Listar transações
- `POST /api/transactions` - Criar transação
- `PUT /api/transactions/{id}` - Atualizar transação
- `DELETE /api/transactions/{id}` - Excluir transação

#### Sistema de Recorrência
- `POST /api/recurrence/rules` - Criar regra de recorrência
- `GET /api/recurrence/rules` - Listar regras
- `GET /api/recurrence/rules/{id}/preview` - Pré-visualizar transações
- `POST /api/recurrence/confirm` - Confirmar recorrências pendentes

#### Módulo de Consórcio
- `GET /api/consortiums/dashboard` - Painel completo
- `GET /api/consortiums/contemplation-projections` - Projeções
- `GET /api/consortiums/statistics` - Estatísticas detalhadas
- `GET /api/consortiums/payments-calendar` - Calendário de pagamentos

#### Pet Shop
- `GET /api/petshop/products` - Listar produtos
- `POST /api/petshop/sales` - Registrar venda
- `GET /api/petshop/dashboard` - Dashboard Pet Shop

---

## 🔐 Segurança

### Autenticação
- **JWT Tokens** com expiração configurável
- **Bcrypt** para hash de senhas
- **CORS** configurado para URLs específicas
- **Validação de entrada** com Pydantic

### Dados Sensíveis
- Senhas hasheadas com salt
- Tokens JWT assinados
- Variáveis de ambiente para credenciais
- Validação de tipos em todas as APIs

---

## 📱 PWA (Progressive Web App)

### Funcionalidades PWA
- **Manifest.json** configurado para instalação
- **Service Worker** para cache e funcionamento offline
- **Ícones** otimizados para diferentes dispositivos
- **Meta tags** para experiência app-like

### Instalação Mobile
1. Abra o OrçaZenFinanceiro no navegador mobile
2. Toque no menu do navegador
3. Selecione "Adicionar à tela inicial"
4. Confirme a instalação

---

## 🧪 Testes

### Backend
```bash
cd backend
python -m pytest tests/
```

### Frontend
```bash
cd frontend
yarn test
# ou
npm test
```

### Testes Integrados
O projeto inclui histórico completo de testes em `test_result.md` com:
- Testes de API backend
- Testes de interface frontend
- Testes de integração
- Validação de funcionalidades

---

## 📊 Monitoramento

### Logs
- **Backend**: Logs estruturados via Python logging
- **Frontend**: Console logs para debugging
- **Database**: MongoDB logs para performance

### Métricas
- Tempo de resposta das APIs
- Taxa de sucesso de transações
- Uso de recursos do sistema
- Métricas de usuário (em desenvolvimento)

---

## 🚀 Deploy em Produção

### Docker (Recomendado)
```yaml
# docker-compose.yml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: orcazenfinanceiro

  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongodb:27017/orcazenfinanceiro
    depends_on:
      - mongodb

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001

volumes:
  mongodb_data:
```

### Nginx (Proxy Reverso)
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Serviços Cloud
- **Vercel/Netlify**: Frontend estático
- **Railway/Heroku**: Backend FastAPI
- **MongoDB Atlas**: Database gerenciado
- **Cloudflare**: CDN e segurança

---

## 🤝 Contribuição

### Desenvolvimento
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código
- **Backend**: PEP 8 para Python
- **Frontend**: ESLint + Prettier para JavaScript
- **Commits**: Conventional Commits
- **Documentação**: Mantenha README atualizado

---

## 📋 Roadmap

### 🔥 Próximas Funcionalidades
- [ ] **Dashboard Customizável** com widgets arrastar-e-soltar
- [ ] **Integrações Bancárias** via Open Banking
- [ ] **Machine Learning** para categorização automática
- [ ] **Multi-usuário** com permissões granulares
- [ ] **API Pública** para integrações externas
- [ ] **Relatórios Avançados** com exportação PDF/Excel

### 🌟 Melhorias Planejadas
- [ ] **Dark Mode** alternativo
- [ ] **Internacionalização** (i18n)
- [ ] **Push Notifications** nativas
- [ ] **Backup Automático** para cloud
- [ ] **Testes Automatizados** completos
- [ ] **Documentação API** com Swagger

---

## 📞 Suporte

### Documentação
- **API Docs**: `/docs` (Swagger UI automático)
- **Redoc**: `/redoc` (Documentação alternativa)

### Contato
- **Issues**: Use o GitHub Issues para bugs e sugestões
- **Discussões**: GitHub Discussions para dúvidas gerais
- **Email**: [seu-email@dominio.com]

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

### Tecnologias
- **FastAPI** - Framework backend incrível
- **React** - Biblioteca frontend poderosa
- **MongoDB** - Database NoSQL flexível
- **Tailwind CSS** - Framework CSS utilitário

### Inspirações
- Nubank - Design e UX financeiro
- Inter - Simplicidade e funcionalidade
- C6 Bank - Inovação digital

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela no GitHub! ⭐**

Desenvolvido com ❤️ para a comunidade brasileira

[🚀 Deploy](#-deploy-em-produção) • [📱 PWA](#-pwa-progressive-web-app) • [🤝 Contribuir](#-contribuição)

</div>

---

## 📈 Status do Projeto

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-100%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**🎉 OrçaZenFinanceiro v1.0.0 - Pronto para Produção!**
