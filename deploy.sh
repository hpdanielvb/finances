#!/bin/bash

# OrçaZenFinanceiro - Deploy Script
# Script para deploy automático em produção

set -e  # Exit on any error

echo "🚀 OrçaZenFinanceiro - Deploy em Produção"
echo "========================================"

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Instale o Docker primeiro."
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Instale o Docker Compose primeiro."
    exit 1
fi

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado. Copiando do exemplo..."
    cp .env.example .env
    echo "📝 Configure o arquivo .env antes de continuar!"
    echo "📝 Edite: nano .env"
    exit 1
fi

# Função para verificar se todas as variáveis estão configuradas
check_env_vars() {
    echo "🔍 Verificando configurações..."
    
    if grep -q "change_this" .env; then
        echo "❌ Ainda existem valores padrão no .env. Configure todas as variáveis!"
        echo "📝 Edite: nano .env"
        exit 1
    fi
    
    echo "✅ Configurações verificadas"
}

# Função para fazer backup do banco de dados
backup_database() {
    echo "💾 Fazendo backup do banco de dados..."
    
    if docker ps | grep -q orcazen_mongodb; then
        docker exec orcazen_mongodb mongodump --out /data/backup/$(date +%Y%m%d_%H%M%S)
        echo "✅ Backup concluído"
    else
        echo "ℹ️  MongoDB não está rodando, pulando backup"
    fi
}

# Função para fazer deploy
deploy() {
    echo "🏗️  Iniciando deploy..."
    
    # Parar containers existentes
    echo "🛑 Parando containers existentes..."
    docker-compose -f docker-compose.prod.yml down
    
    # Fazer backup se existir dados
    backup_database
    
    # Build das imagens
    echo "🔨 Construindo imagens..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Iniciar serviços
    echo "🚀 Iniciando serviços..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Aguardar serviços ficarem prontos
    echo "⏳ Aguardando serviços ficarem prontos..."
    sleep 30
    
    # Verificar status
    echo "🔍 Verificando status dos serviços..."
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "🎉 Deploy concluído com sucesso!"
    echo ""
    echo "📊 Acesse a aplicação:"
    echo "   Frontend: http://localhost"
    echo "   Backend API: http://localhost/api/docs"
    echo ""
    echo "📝 Comandos úteis:"
    echo "   Logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "   Parar: docker-compose -f docker-compose.prod.yml down"
    echo "   Restart: docker-compose -f docker-compose.prod.yml restart"
}

# Função para verificar saúde dos serviços
health_check() {
    echo "🏥 Verificando saúde dos serviços..."
    
    # Verificar se os containers estão rodando
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        echo "❌ Alguns serviços não estão rodando"
        docker-compose -f docker-compose.prod.yml ps
        exit 1
    fi
    
    # Verificar endpoint de saúde
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Aplicação está saudável"
    else
        echo "⚠️  Endpoint de saúde não está respondendo"
    fi
}

# Função para mostrar logs
show_logs() {
    echo "📋 Mostrando logs dos serviços..."
    docker-compose -f docker-compose.prod.yml logs -f
}

# Menu principal
case "${1:-}" in
    "deploy")
        check_env_vars
        deploy
        ;;
    "health")
        health_check
        ;;
    "logs")
        show_logs
        ;;
    "backup")
        backup_database
        ;;
    "stop")
        echo "🛑 Parando todos os serviços..."
        docker-compose -f docker-compose.prod.yml down
        echo "✅ Serviços parados"
        ;;
    "restart")
        echo "🔄 Reiniciando serviços..."
        docker-compose -f docker-compose.prod.yml restart
        echo "✅ Serviços reiniciados"
        ;;
    *)
        echo "📖 Uso: $0 {deploy|health|logs|backup|stop|restart}"
        echo ""
        echo "Comandos disponíveis:"
        echo "  deploy  - Fazer deploy completo da aplicação"
        echo "  health  - Verificar saúde dos serviços"
        echo "  logs    - Mostrar logs em tempo real"
        echo "  backup  - Fazer backup do banco de dados"
        echo "  stop    - Parar todos os serviços"
        echo "  restart - Reiniciar todos os serviços"
        echo ""
        echo "Exemplo: $0 deploy"
        exit 1
        ;;
esac