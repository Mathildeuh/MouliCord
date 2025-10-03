# MouliCord 🤖

Bot Discord pour surveiller automatiquement les résultats de la moulinette Epitech.

## ✨ Fonctionnalités

- 🚨 **Surveillance automatique** des nouveaux résultats (toutes les 5 min)
- 💾 **Stockage intelligent** - évite les doublons avec historique JSON
- 📊 Consultation des résultats et statistiques détaillées
- 🔍 Détails complets des tests avec traces d'exécution
- ⚡ Notifications instantanées uniquement des nouveaux résultatst Discord pour Moulinette Epitech

Bot Discord pour consulter et surveiller automatiquement les résultats de la moulinette Epitech.

## Fonctionnalités

- 📊 Consultation des derniers résultats de moulinette
- 🔍 Affichage des détails complets d'un test spécifique
- 🚨 Surveillance automatique des nouveaux résultats (toutes les 5 minutes)
- � **Stockage intelligent en JSON** - évite les doublons et compare avec l'historique
- �📈 Statistiques détaillées (taux de réussite, tâches échouées, etc.)
- 🎨 Interface Discord avec embeds colorés
- 🕒 Gestion correcte des timezones (UTC)
- 🔧 Commandes de debug et de statut
- ⚡ Notifications instantanées des nouveaux résultats uniquement
- 🗄️ Sauvegarde et gestion de l'historique des résultats

## 🚀 Installation

1. **Configuration**
```bash
cp .env.example .env
nano .env  # Remplir vos tokens
```

2. **Démarrage**
```bash
./start.sh
# ou
pip install -r requirements.txt && python bot.py
```

### 🔑 Tokens requis

- **DISCORD_TOKEN** : [Discord Developer Portal](https://discord.com/developers/applications)
- **EPITECH_API_TOKEN** : Token Bearer de [api.epitest.eu](https://api.epitest.eu)
- **CHANNEL_ID** : ID du canal Discord (mode développeur → clic droit → copier ID)

## 🎮 Commandes Discord

| Commande | Description |
|----------|-------------|
| `!mouli [nb]` | Derniers résultats (défaut: 5) |
| `!details <id>` | Détails complets d'un test |
| `!watch` | Active/désactive surveillance |
| `!status` | Statut de la surveillance |
| `!stats` | Statistiques du stockage |
| `!backup` | Sauvegarde du stockage |
| `!help_mouli` | Aide complète |

## 📁 Fichiers

- `bot.py` - Bot Discord principal
- `epitech_api.py` - Client API Epitech avec stockage JSON
- `start.sh` - Script de démarrage
- `results_history.json` - Historique des résultats (auto-généré)
- `.env` - Configuration (tokens)

---
*Projet éducatif pour Epitech*