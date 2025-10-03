#!/bin/bash

echo "🚀 MouliCord Bot"

# Vérifier .env
if [ ! -f .env ]; then
    echo "❌ Fichier .env manquant!"
    echo "📝 Créez-le: cp .env.example .env && nano .env"
    exit 1
fi

# Setup environnement
[ ! -d ".venv" ] && python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

# Démarrer
echo "🤖 Démarrage... (Ctrl+C pour arrêter)"
.venv/bin/python bot.py