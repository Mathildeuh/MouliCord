# MouliCord 🤖

Bot Discord pour surveiller automatiquement les résultats de la mouli### `!refresh_token` - ### `!refresh_token` - Récupération automatique avec persistance permanente

```bash
!refresh_token          # Mode invisible avec session Office permanente
!refresh_token False    # Mode visible avec session Office permanente
```

**Fonctionnement avec détection intelligente :**
1. 🔍 **Vérification session** → Cherche une session Office existante
2. 🎯 **Réutilisation intelligente** → Utilise la session si valide
3. 🌐 **Ouverture Chrome** → Avec profil persistant permanent
4. 📍 **Navigation** → https://myresults.epitest.eu/
5. ⚡ **Détection automatique** → Si redirigé vers `#y/2025` = token valide !
6. 📡 **Récupération directe** → Extraction immédiate depuis les requêtes réseau
7. 🖱️ **Authentification** → Clic "Log In" uniquement si nécessaire
8. 💾 **Sauvegarde permanente** → Session Office gardée à vie + mise à jour `.env`

**Avantages de la détection intelligente :**
- ⚡ **Ultra-rapidité** : Récupération token en ~2 secondes si déjà connecté
- 🎯 **Détection automatique** : Sait instantanément si le token est encore valide  
- 🔐 **Sécurité** : Session Office stockée localement de façon permanente
- 🚀 **Une seule authentification** : Plus jamais besoin de se re-connecter !
- 🔄 **Fiabilité maximale** : Fonctionne parfaitement avec Office/Azure AD

**Prérequis :**
- Chrome ou Chromium installé sur le système
- `pip install selenium webdriver-manager`
- Connexion Internet stabletique avec persistance

```bash
!refresh_token          # Mode invisible avec persistance Office permanente
!refresh_token False    # Mode visible avec persistance Office permanente
# Plus besoin de nettoyer la session - elle est permanente !
```

**Fonctionnement avec persistance Office :**
1. 🔍 **Vérification session** → Cherche une session Office existante
2. 🎯 **Réutilisation intelligente** → Utilise la session si valide
3. 🌐 **Ouverture Chrome** → Avec profil persistant si nouvelle auth
4. 📍 **Navigation** → https://myresults.epitest.eu/
5. 🖱️ **Authentification** → Clic "Log In" uniquement si nécessaire
6. 📡 **Capture token** → Extraction depuis les requêtes réseau
7. ✅ **Vérification** → Redirection vers `/#y/2025`
8. 💾 **Sauvegarde** → Session Office + mise à jour `.env`

**Avantages de la persistance :**
- 🚀 **Rapidité** : Réutilise les sessions existantes (pas de re-auth)
- 🔐 **Sécurité** : Session Office stockée localement seulement
- 🔄 **Fiabilité** : Fonctionne avec l'authentification Office/Azure AD

**Prérequis :**
- Chrome ou Chromium installé sur le système
- `pip install selenium webdriver-manager`
- Connexion Internet stable✨ Fonctionnalités

- 🚨 **Surveillance automatique** des nouveaux résultats (toutes les 5 min)
- 💾 **Stockage intelligent** - évite les doublons avec historique JSON
- 📊 **Barres de progression visuelles** avec pourcentages automatiques
- 🎨 **Indicateurs colorés** par niveau de réussite (🟩🟨🟧🟥)
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
- **EPITECH_API_TOKEN** : Token Bearer de [api.epitest.eu](https://api.epitest.eu) ou auto-récupéré via `!refresh_token`
- **CHANNEL_ID** : ID du canal Discord (mode développeur → clic droit → copier ID)

### 🤖 Récupération automatique de token

Utilisez `!refresh_token` pour récupérer automatiquement un nouveau token via Selenium :
- ✅ **Persistance Office Permanente** : Sauvegarde définitive de votre session
- ✅ **Plus jamais de re-authentification** : Une seule fois suffit !
- ✅ Ouvre automatiquement https://myresults.epitest.eu/
- ✅ Clique sur "Log In" (uniquement si nécessaire)
- ✅ Capture le token depuis les requêtes réseau
- ✅ Vérifie la validité (redirection vers `/#y/2025`)
- ✅ Met à jour automatiquement le fichier `.env`

## 🎮 Commandes Discord

| Commande | Description |
|----------|-------------|
| `!mouli [nb]` | Derniers résultats avec barres de progression |
| `!details <id>` | Détails complets d'un test |
| `!watch` | Active/désactive surveillance |
| `!status` | Statut de la surveillance |
| `!stats` | Statistiques du stockage |
| `!backup` | Sauvegarde du stockage |
| `!token` | Vérifier l'expiration du token Epitech |
| `!refresh_token [headless]` | 🤖 Récupérer automatiquement un nouveau token (persistance permanente) |
| `!help_mouli` | Aide complète |

### 📊 Barres de progression
- **🟩 Vert** : 90-100% (Excellent)
- **🟨 Jaune** : 70-89% (Bien)  
- **🟧 Orange** : 50-69% (Moyen)
- **🟥 Rouge** : 0-49% (Insuffisant)
- **Projets** : 🟢🟡🟠🔴 + barre de progression globale
- **Tâches** : ✅ réussi / ❌ échoué / 💥 crashé (simple statut)

## 🤖 Automatisation Token

### `!refresh_token` - Récupération automatique

```bash
!refresh_token          # Mode invisible (headless)
!refresh_token False    # Mode visible (pour debug/auth manuelle)
```

**Fonctionnement :**
1. 🌐 Ouvre Chrome/Chromium automatiquement
2. 📍 Navigate vers https://myresults.epitest.eu/
3. 🖱️ Clique sur le bouton "Log In"
4. � Capture les requêtes réseau pour extraire le token Bearer
5. ✅ Vérifie l'authentification (redirection vers `/#y/2025`)
6. 💾 Met à jour automatiquement `.env` et recharge l'API

**Prérequis :**
- Chrome ou Chromium installé sur le système
- `pip install selenium webdriver-manager`
- Connexion Internet stable

## �📁 Fichiers

- `bot.py` - Bot Discord principal
- `epitech_api.py` - Client API Epitech avec stockage JSON  
- `token_refresher.py` - Automatisation Selenium pour token
- `test_token_refresh.py` - Script de test indépendant
- `start.sh` - Script de démarrage
- `results_history.json` - Historique des résultats (auto-généré)
- `.env` - Configuration (tokens)

---
*Projet éducatif pour Epitech*