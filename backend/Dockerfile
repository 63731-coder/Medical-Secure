# Dockerfile pour le backend Django
FROM python:3.11-slim

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer le répertoire pour les logs
RUN mkdir -p logs

# Exposer le port
EXPOSE 8000

# Commande par défaut (peut être surchargée dans docker-compose.yml)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
