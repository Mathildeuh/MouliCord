# MouliCord - Bot Discord pour Moulinette Epitech

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

## Installation

1. **Cloner le projet**
```bash
git clone <url-du-repo>
cd MouliCord
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration**
Créez un fichier `.env` basé sur `.env.example` :
```bash
cp .env.example .env
```

Remplissez le fichier `.env` avec vos tokens :
```env
DISCORD_TOKEN=votre_token_discord_bot
EPITECH_API_TOKEN=votre_token_bearer_epitech
CHANNEL_ID=id_du_salon_discord
```

### Comment obtenir les tokens

#### Token Discord Bot
1. Allez sur [Discord Developer Portal](https://discord.com/developers/applications)
2. Créez une nouvelle application
3. Dans "Bot", créez un bot et copiez le token
4. Invitez le bot sur votre serveur avec les permissions nécessaires

#### Token Bearer Epitech
1. Connectez-vous sur [api.epitest.eu](https://api.epitest.eu)
2. Récupérez votre token d'authentification Bearer

#### ID du Canal Discord
1. Activez le mode développeur dans Discord
2. Clic droit sur le canal → "Copier l'ID"

## Utilisation

### Démarrer le bot
```bash
python bot.py
```

### Commandes disponibles

**Consultation :**
- `!mouli [nombre]` - Affiche les derniers résultats (défaut: 5)
- `!details <run_id>` - Affiche les détails d'un test spécifique

**Surveillance :**
- `!watch` - Active/désactive la surveillance automatique
- `!status` - Affiche le statut de la surveillance
- `!check_now` - Force une vérification immédiate

**Gestion du stockage :**
- `!stats` - Statistiques détaillées du stockage JSON
- `!backup` - Crée une sauvegarde du stockage
- `!clear_storage` - Vide le stockage (commande d'administration)

**Aide :**
- `!help_mouli` - Affiche l'aide complète

### Exemples

```
!mouli 3          # Affiche les 3 derniers résultats
!details 7271428  # Détails du test avec l'ID 7271428
!watch            # Active la surveillance automatique
```

## Structure du projet

```
MouliCord/
├── bot.py                 # Bot Discord principal
├── epitech_api.py         # Client API Epitech
├── requirements.txt       # Dépendances Python
├── .env.example          # Exemple de configuration
├── .env                  # Configuration (à créer)
├── start.sh              # Script de démarrage
├── test_config.py        # Test de configuration
├── test_surveillance.py  # Test de surveillance
├── test_storage.py       # Test du système de stockage JSON
├── results_history.json  # Stockage des résultats (généré automatiquement)
├── README.md             # Documentation principale
└── USAGE.md              # Guide d'utilisation détaillé
```

## API Epitech

Le bot utilise deux endpoints de l'API Epitech :

1. **`GET /me/{year}`** - Liste des résultats pour une année
2. **`GET /me/details/{run_id}`** - Détails d'un test spécifique

## Fonctionnalités avancées

### 💾 Système de stockage intelligent
- **Fichier JSON persistant** : `results_history.json` stocke tous les résultats
- **Détection des nouveaux résultats** : Compare avec l'historique à chaque vérification
- **Élimination des doublons** : Identifie les résultats par `testRunId` + `date` + `slug`
- **Statistiques complètes** : Suivi des projets, dates, et évolution
- **Sauvegarde automatique** : Commande `!backup` pour créer des archives

### 🚨 Surveillance automatique
- Vérification toutes les 5 minutes avec comparaison JSON
- Notification automatique **uniquement** des nouveaux résultats
- Peut être activée/désactivée avec `!watch`
- Statut détaillé avec `!status`

### 📊 Formatage intelligent
- Calcul automatique du taux de réussite
- Affichage des tâches réussies/échouées
- Gestion des traces d'exécution
- Statistiques par projet dans `!stats`

### 🛡️ Gestion d'erreurs robuste
- Messages d'erreur informatifs
- Vérification des tokens au démarrage
- Gestion des timeouts API
- Récupération automatique en cas d'erreur JSON

## Licence

Projet éducatif pour Epitech.