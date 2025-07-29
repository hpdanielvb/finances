# 🚀 Guia de Deploy - OrçaZenFinanceiro

Este guia explica como fazer o deploy do OrçaZenFinanceiro em produção usando Docker.

## 📋 Pré-requisitos

### Servidor de Produção
- **Ubuntu 20.04+** / **CentOS 8+** / **Debian 11+**
- **2 GB RAM** mínimo (4 GB recomendado)
- **20 GB** de espaço em disco
- **Docker** e **Docker Compose** instalados

### Instalação do Docker (Ubuntu)
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Adicionar chave GPG do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

## 🔧 Configuração

### 1. Clone o Repositório
```bash
git clone https://github.com/your-username/orcazenfinanceiro.git
cd orcazenfinanceiro
```

### 2. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

### 3. Configurações Essenciais no .env
```bash
# Altere OBRIGATORIAMENTE:
MONGO_ROOT_PASSWORD=sua_senha_super_segura_aqui
SECRET_KEY=sua_chave_jwt_super_secreta_minimo_32_caracteres

# Configure email (Gmail):
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app-gmail
EMAIL_FROM=OrçaZenFinanceiro <seu-email@gmail.com>

# Para produção com domínio:
REACT_APP_BACKEND_URL=https://sua-api.dominio.com
```

### 4. Configurar Gmail App Password
1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Vá em **Segurança** → **Verificação em duas etapas**
3. Role até **Senhas de app** e clique
4. Selecione **Aplicativo** → **Outro** → Digite "OrçaZenFinanceiro"
5. Copie a senha gerada e cole em `SMTP_PASSWORD`

## 🚀 Deploy

### Deploy Automatizado
```bash
# Fazer deploy completo
./deploy.sh deploy
```

### Deploy Manual
```bash
# Parar containers existentes
docker-compose -f docker-compose.prod.yml down

# Build das imagens
docker-compose -f docker-compose.prod.yml build --no-cache

# Iniciar serviços
docker-compose -f docker-compose.prod.yml up -d

# Verificar status
docker-compose -f docker-compose.prod.yml ps
```

## 🔍 Verificação

### Comandos Úteis
```bash
# Ver logs em tempo real
./deploy.sh logs

# Verificar saúde dos serviços
./deploy.sh health

# Parar todos os serviços
./deploy.sh stop

# Reiniciar serviços
./deploy.sh restart

# Fazer backup do banco
./deploy.sh backup
```

### Endpoints de Teste
```bash
# Health check
curl http://localhost/health

# API Documentation
curl http://localhost/api/docs

# Frontend
curl http://localhost/
```

## 🌐 Configuração de Domínio

### 1. DNS
Configure seu DNS para apontar para o IP do servidor:
```
A    @              SEU_IP_SERVIDOR
A    api            SEU_IP_SERVIDOR
```

### 2. SSL/HTTPS com Let's Encrypt
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seudominio.com -d api.seudominio.com

# Renovação automática
sudo crontab -e
# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Nginx para HTTPS
Crie `/app/nginx-ssl.conf`:
```nginx
server {
    listen 80;
    server_name seudominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seudominio.com;
    
    ssl_certificate /etc/letsencrypt/live/seudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seudominio.com/privkey.pem;
    
    # Configurações SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Resto da configuração...
}
```

## 📊 Monitoramento

### Logs
```bash
# Backend logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Frontend logs
docker-compose -f docker-compose.prod.yml logs -f frontend

# MongoDB logs
docker-compose -f docker-compose.prod.yml logs -f mongodb

# Nginx logs
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Métricas
```bash
# Status dos containers
docker stats

# Uso de disco
df -h

# Uso de memória
free -h

# Processos
htop
```

## 🔒 Segurança em Produção

### Firewall (UFW)
```bash
# Instalar UFW
sudo apt install ufw

# Configurações básicas
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH, HTTP e HTTPS
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Ativar firewall
sudo ufw enable
```

### Backup Automático
```bash
# Criar script de backup
sudo crontab -e

# Adicionar linha para backup diário às 2h
0 2 * * * /path/to/orcazenfinanceiro/deploy.sh backup
```

### Updates de Segurança
```bash
# Configurar updates automáticos
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## ⚡ Otimização de Performance

### 1. Configurar Swap
```bash
# Criar arquivo swap de 2GB
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. Otimizar MongoDB
```bash
# Criar arquivo de configuração MongoDB
sudo nano /etc/mongod.conf

# Adicionar:
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1  # Ajuste conforme RAM disponível
```

### 3. Configurar Nginx Cache
```nginx
# Adicionar ao nginx.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m inactive=60m;

location /api {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_bypass $http_cache_control;
    # ... resto da configuração
}
```

## 🚨 Troubleshooting

### Problemas Comuns

#### Erro de Conexão com MongoDB
```bash
# Verificar logs do MongoDB
docker-compose -f docker-compose.prod.yml logs mongodb

# Verificar se o container está rodando
docker ps | grep mongodb

# Reiniciar MongoDB
docker-compose -f docker-compose.prod.yml restart mongodb
```

#### Frontend não carrega
```bash
# Verificar logs do frontend
docker-compose -f docker-compose.prod.yml logs frontend

# Verificar se a URL do backend está correta
grep REACT_APP_BACKEND_URL .env

# Rebuild do frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
```

#### Erro 502 Bad Gateway
```bash
# Verificar se backend está rodando
curl http://localhost:8001/api/docs

# Verificar logs do nginx
docker-compose -f docker-compose.prod.yml logs nginx

# Reiniciar nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Comandos de Diagnóstico
```bash
# Verificar portas em uso
sudo netstat -tulpn | grep LISTEN

# Verificar espaço em disco
du -sh /var/lib/docker/

# Limpar imagens antigas
docker system prune -a

# Verificar recursos do sistema
htop
iotop
```

## 📞 Suporte

### Logs de Debug
```bash
# Habilitar debug no backend
echo "DEBUG=true" >> .env

# Reiniciar serviços
docker-compose -f docker-compose.prod.yml restart
```

### Contato
- **Issues**: GitHub Issues
- **Email**: [seu-email@dominio.com]
- **Documentação**: `/api/docs`

---

## ✅ Checklist de Deploy

- [ ] Servidor configurado com Docker
- [ ] Variáveis de ambiente configuradas
- [ ] Senhas alteradas dos valores padrão
- [ ] Email configurado e testado
- [ ] SSL/HTTPS configurado (para produção)
- [ ] Firewall configurado
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] DNS configurado (se aplicável)
- [ ] Teste completo da aplicação

**🎉 Deploy concluído com sucesso!**