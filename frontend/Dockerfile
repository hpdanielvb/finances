# Multi-stage build para Frontend React
FROM node:18-alpine as build

# Configurar diretório de trabalho
WORKDIR /app

# Copiar package.json e yarn.lock
COPY package*.json ./
COPY yarn.lock ./

# Instalar dependências
RUN yarn install --frozen-lockfile

# Copiar código fonte
COPY . .

# Definir variável de ambiente para build
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Build da aplicação
RUN yarn build

# Estágio de produção com Nginx
FROM nginx:alpine as production

# Copiar arquivos buildados
COPY --from=build /app/build /usr/share/nginx/html

# Copiar configuração customizada do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expor porta
EXPOSE 3000

# Comando para iniciar nginx
CMD ["nginx", "-g", "daemon off;"]