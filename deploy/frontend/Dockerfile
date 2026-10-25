# Frontend compilé, servi en fichiers statiques. Contexte de build : racine du dépôt.
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Pas de routeur côté client : un simple serveur statique suffit, Traefik route /api vers le backend.
FROM busybox:1.37
COPY --from=build /app/dist /www
EXPOSE 8080
CMD ["httpd", "-f", "-v", "-p", "8080", "-h", "/www"]
