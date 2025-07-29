#!/bin/bash

# 🚂 OrçaZenFinanceiro - Railway Production Deploy Script
# Automated deployment to Railway with MongoDB Atlas

set -e  # Exit on any error

echo "🚂 OrçaZenFinanceiro - Deploy para Railway"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}🔍 $1${NC}"
}

# Check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI não está instalado!"
        echo ""
        echo "📥 Instale o Railway CLI:"
        echo "npm install -g @railway/cli"
        echo ""
        echo "🔗 Ou visite: https://docs.railway.app/develop/cli"
        exit 1
    fi
    print_status "Railway CLI encontrado"
}

# Check if user is logged in to Railway
check_railway_auth() {
    if ! railway whoami &> /dev/null; then
        print_error "Não logado no Railway!"
        echo ""
        echo "🔐 Faça login no Railway:"
        echo "railway login"
        exit 1
    fi
    
    local user=$(railway whoami)
    print_status "Logado no Railway como: $user"
}

# Validate environment file
validate_env() {
    if [ ! -f .env.production ]; then
        print_error "Arquivo .env.production não encontrado!"
        echo ""
        echo "📝 Copie e configure o arquivo:"
        echo "cp .env.example .env.production"
        echo "nano .env.production"
        exit 1
    fi
    
    # Check for default values that need to be changed
    if grep -q "change_this" .env.production; then
        print_error "Ainda existem valores padrão no .env.production!"
        echo ""
        print_warning "Configure todas as variáveis:"
        grep -n "change_this\|YOUR_\|your-" .env.production
        echo ""
        echo "📝 Edite: nano .env.production"
        exit 1
    fi
    
    # Check for MongoDB Atlas URL
    if ! grep -q "mongodb+srv://" .env.production; then
        print_error "MongoDB Atlas URL não configurada!"
        echo ""
        print_warning "Configure MONGO_URL no .env.production"
        echo "📖 Veja: MONGODB_ATLAS_SETUP.md"
        exit 1
    fi
    
    print_status "Arquivo .env.production validado"
}

# Create Railway project
create_railway_project() {
    print_info "Verificando projeto Railway..."
    
    if ! railway status &> /dev/null; then
        print_warning "Projeto Railway não encontrado. Criando novo projeto..."
        
        # Create new project
        railway new orcazenfinanceiro --name "OrçaZenFinanceiro"
        
        print_status "Projeto Railway criado: OrçaZenFinanceiro"
    else
        local project=$(railway status | grep "Project:" | cut -d' ' -f2-)
        print_status "Usando projeto Railway: $project"
    fi
}

# Set environment variables in Railway
set_railway_variables() {
    print_info "Configurando variáveis de ambiente no Railway..."
    
    # Read .env.production and set variables
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ $key =~ ^[[:space:]]*# ]] || [[ -z $key ]] || [[ $key =~ ^[[:space:]]*$ ]]; then
            continue
        fi
        
        # Remove quotes and whitespace
        key=$(echo "$key" | tr -d '[:space:]')
        value=$(echo "$value" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | sed 's/^"//' | sed 's/"$//')
        
        if [[ -n $key && -n $value ]]; then
            print_info "Configurando: $key"
            railway variables set "$key=$value"
        fi
    done < .env.production
    
    print_status "Variáveis de ambiente configuradas"
}

# Deploy backend service
deploy_backend() {
    print_info "🔧 Fazendo deploy do backend..."
    
    # Navigate to backend directory
    cd backend
    
    # Create railway service for backend
    railway service create orcazen-backend
    railway service connect orcazen-backend
    
    # Deploy backend
    railway up --detach
    
    # Get backend URL
    local backend_url=$(railway domain)
    if [[ -n $backend_url ]]; then
        print_status "Backend deployed: https://$backend_url"
        
        # Update frontend environment variable
        cd ..
        sed -i.bak "s|REACT_APP_BACKEND_URL=.*|REACT_APP_BACKEND_URL=https://$backend_url|" .env.production
        railway variables set "REACT_APP_BACKEND_URL=https://$backend_url"
    fi
    
    cd ..
}

# Deploy frontend service  
deploy_frontend() {
    print_info "🎨 Fazendo deploy do frontend..."
    
    # Navigate to frontend directory
    cd frontend
    
    # Create railway service for frontend
    railway service create orcazen-frontend
    railway service connect orcazen-frontend
    
    # Set frontend specific variables
    railway variables set "NODE_VERSION=18"
    
    # Deploy frontend
    railway up --detach
    
    # Get frontend URL
    local frontend_url=$(railway domain)
    if [[ -n $frontend_url ]]; then
        print_status "Frontend deployed: https://$frontend_url"
    fi
    
    cd ..
}

# Test deployment
test_deployment() {
    print_info "🧪 Testando deployment..."
    
    # Wait a bit for services to start
    sleep 30
    
    # Get service URLs
    local backend_url=$(cd backend && railway domain)
    local frontend_url=$(cd frontend && railway domain)
    
    if [[ -n $backend_url ]]; then
        print_info "Testando backend: https://$backend_url/health"
        if curl -f -s "https://$backend_url/health" > /dev/null; then
            print_status "Backend health check: OK"
        else
            print_warning "Backend health check falhou - pode estar inicializando"
        fi
    fi
    
    if [[ -n $frontend_url ]]; then
        print_info "Testando frontend: https://$frontend_url"
        if curl -f -s "https://$frontend_url" > /dev/null; then
            print_status "Frontend acessível: OK"
        else
            print_warning "Frontend não acessível - pode estar inicializando"
        fi
    fi
}

# Show deployment info
show_deployment_info() {
    echo ""
    echo "🎉 DEPLOY CONCLUÍDO!"
    echo "==================="
    
    # Get URLs
    local backend_url=$(cd backend && railway domain 2>/dev/null || echo "not-deployed")
    local frontend_url=$(cd frontend && railway domain 2>/dev/null || echo "not-deployed")
    
    echo ""
    echo "🌐 URLs de Produção:"
    if [[ $frontend_url != "not-deployed" ]]; then
        echo "   Frontend: https://$frontend_url"
    fi
    if [[ $backend_url != "not-deployed" ]]; then
        echo "   Backend API: https://$backend_url"
        echo "   API Docs: https://$backend_url/docs"
    fi
    
    echo ""
    echo "📊 Comandos úteis:"
    echo "   Ver logs backend: cd backend && railway logs"
    echo "   Ver logs frontend: cd frontend && railway logs"
    echo "   Status: railway status"
    echo "   Variáveis: railway variables"
    
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   Se backend não funcionar, verifique MongoDB Atlas connection"
    echo "   Se frontend não carregar, aguarde ~2-3 minutos para build"
    echo "   Logs detalhados: railway logs --follow"
}

# Main deployment function
deploy() {
    echo "🚀 Iniciando deploy para Railway..."
    
    check_railway_cli
    check_railway_auth
    validate_env
    create_railway_project
    set_railway_variables
    deploy_backend
    deploy_frontend
    test_deployment
    show_deployment_info
}

# Helper functions
setup() {
    echo "🔧 Setup inicial para Railway deploy..."
    
    # Check if .env.production exists
    if [ ! -f .env.production ]; then
        print_info "Criando .env.production do template..."
        cp .env.example .env.production
        
        echo ""
        print_warning "Configure o arquivo .env.production antes de fazer deploy:"
        echo "1. Configure MongoDB Atlas (veja MONGODB_ATLAS_SETUP.md)"
        echo "2. Configure Gmail SMTP"
        echo "3. Altere SECRET_KEY"
        echo ""
        echo "📝 Edite: nano .env.production"
        return
    fi
    
    print_status "Setup já realizado. Use: $0 deploy"
}

logs() {
    echo "📋 Mostrando logs dos serviços..."
    
    echo "🔧 Backend logs:"
    cd backend && railway logs --tail 50
    
    echo ""
    echo "🎨 Frontend logs:"
    cd ../frontend && railway logs --tail 50
}

# Menu principal
case "${1:-}" in
    "deploy")
        deploy
        ;;
    "setup")
        setup
        ;;
    "logs")
        logs
        ;;
    "test")
        test_deployment
        ;;
    "status")
        railway status
        ;;
    *)
        echo "📖 OrçaZenFinanceiro - Railway Deploy"
        echo ""
        echo "Uso: $0 {setup|deploy|logs|test|status}"
        echo ""
        echo "Comandos:"
        echo "  setup   - Configuração inicial"
        echo "  deploy  - Deploy completo para Railway"
        echo "  logs    - Ver logs dos serviços"
        echo "  test    - Testar deployment"
        echo "  status  - Status do projeto Railway"
        echo ""
        echo "📚 Pré-requisitos:"
        echo "  1. Railway CLI instalado (npm install -g @railway/cli)"
        echo "  2. Login no Railway (railway login)"
        echo "  3. MongoDB Atlas configurado"
        echo "  4. Gmail SMTP configurado"
        echo ""
        echo "🚀 Para começar: $0 setup"
        exit 1
        ;;
esac