# 📋 Checklist de Deploy - OrçaZenFinanceiro

## ✅ Pré-Deploy (Concluído)
- [x] Estrutura do projeto validada
- [x] Dockerfiles configurados  
- [x] Variáveis de ambiente preparadas
- [x] Health checks implementados
- [x] Dependencies listadas

## 🚀 Deploy Steps
- [ ] MongoDB Atlas cluster criado
- [ ] Connection string configurada em .env.production
- [ ] Railway CLI instalado (npm install -g @railway/cli)
- [ ] Login no Railway (railway login)
- [ ] Deploy executado (./deploy-railway.sh deploy)

## 🔍 Pós-Deploy
- [ ] Health check funcionando
- [ ] Frontend carregando
- [ ] Backend API acessível
- [ ] Login funcionando
- [ ] Database conectado

## 🌐 URLs Esperadas
- Frontend: https://orcazen-frontend-production.up.railway.app
- Backend: https://orcazen-backend-production.up.railway.app  
- API Docs: https://orcazen-backend-production.up.railway.app/docs

## 📞 Suporte
- Guia completo: DEPLOY_GUIDE.md
- MongoDB Atlas: MONGODB_ATLAS_SETUP.md
- Railway script: ./deploy-railway.sh
