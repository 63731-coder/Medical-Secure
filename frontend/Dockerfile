# Dockerfile pour le frontend Vue.js
FROM node:20-alpine

# Répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier le code de l'application
COPY . .

# Exposer le port Vite
EXPOSE 5173

# Commande pour démarrer le serveur de développement
# Utiliser --host pour permettre les connexions externes
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
