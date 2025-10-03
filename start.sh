#!/bin/bash

# Script de démarrage pour MouliCord

echo "🚀 Démarrage de MouliCord Bot..."

# Vérifier si le fichier .env existe
if [ ! -f .env ]; then
    echo "❌ Fichier .env manquant!"
    echo "📝 Copiez .env.example vers .env et remplissez vos tokens:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Vérifier si l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv .venv
fi

# Activer l'environnement virtuel et installer les dépendances
echo "📦 Installation des dépendances..."
.venv/bin/pip install -r requirements.txt

# Test optionnel de la configuration
echo "🔍 Test de la configuration (optionnel)..."
read -p "Voulez-vous tester la configuration avant de démarrer? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    .venv/bin/python test_config.py
    if [ $? -ne 0 ]; then
        echo "❌ Test de configuration échoué"
        exit 1
    fi
    echo "✅ Configuration validée"
fi

# Démarrer le bot
echo "🤖 Lancement du bot Discord..."
echo "💡 Pour arrêter le bot, utilisez Ctrl+C"
echo "📊 Le bot vérifiera automatiquement les nouveaux résultats toutes les 5 minutes"
echo "� Système de stockage JSON activé - pas de doublons de notifications"
echo "�📖 Utilisez !help_mouli dans Discord pour voir les commandes disponibles"
echo ""

.venv/bin/python bot.py