# MouliCord v2.0 🚀

## **Le Bot Discord Epitech 100% Moderne** 🎮

**Interface entièrement convertie aux Slash Commands avec composants interactifs !**

---

## ✨ **MouliCord v2.0 - Conversion Complète**

🎯 **TOUTES les commandes sont maintenant des Slash Commands !**

- ❌ **Fini les `!commandes`** - Interface dépassée supprimée
- ✅ **100% `/slash_commands`** - Interface Discord moderne
- 📱 **Composants interactifs** - Boutons, menus, navigation
- 🎮 **UX optimale** - Plus intuitive et professionnelle

---

## 🎮 **Commandes Slash Disponibles**

| Commande | Description | Interface |
|----------|-------------|-----------|
| `/mouli` | 📊 Derniers résultats | 🔄 Bouton actualisation |
| `/details <projet>` | 🔍 Détails projet spécifique | 📈 Statistiques détaillées |
| `/history` | 📈 Sélection projet + historique | 📋 Liste projets + 📅 Navigation historique |
| `/stats` | 📊 Statistiques complètes | 🏆 Classements + graphiques |
| `/status` | 🔧 État du système | 📡 API + Token + Stockage |
| `/check_now` | 🔄 Vérification immédiate | ⚡ Force la vérification |
| `/token` | 🔐 Vérification token | ⏰ Temps restant + validité |
| `/refresh_token` | 🔄 Actualisation automatique | 🤖 Selenium + Office |
| `/watch` | 👁️ Statut surveillance | ✅ Toujours active 24/7 |
| `/backup` | 💾 Sauvegarde horodatée | 📄 Fichier timestampé |
| `/clear_storage` | 🗑️ Vider stockage | ⚠️ Confirmation interactive |
| `/help` | ❓ Guide complet | 📖 Navigation par pages |

---

## 🎯 **Exemples d'Utilisation**

### **Navigation Moderne :**
```
/mouli                                # 📊 + 🔄 Bouton actualisation
/history                              # 📋 Sélection projet + 📅 Navigation
/stats                                # 📈 Statistiques + 🏆 Classements
/status                               # 📡 État complet du système
```

### **Gestion Système :**
```
/token                                # 🔐 Vérification rapide
/refresh_token                        # 🤖 Actualisation Selenium
/backup                               # 💾 Sauvegarde automatique
/help                                 # 📖 Guide interactif
```

---

## 📊 **Fonctionnalités Avancées**

### 🔄 **Surveillance Automatique 24/7**
- ✅ **Vérification toutes les 10 minutes**
- 🔔 **Notifications @everyone** pour nouveaux résultats
- 💾 **Sauvegarde automatique** dans `results_history.json`
- 🛡️ **Gestion d'erreurs robuste** avec retry automatique

### 🤖 **Automation Selenium Ultra-Rapide**
- 🚀 **Sessions Office persistantes permanentes**
- ⚡ **Détection intelligente de redirections**
- 🔍 **Récupération automatique de tokens**
- 💾 **Profils Chrome permanents** (jamais supprimés)

### 📱 **Interface Moderne Discord**
- 🎮 **Slash Commands natifs** avec autocomplétion
- 📋 **Menus déroulants interactifs** pour sélections
- 🔄 **Boutons d'actualisation** intégrés
- 📈 **Navigation par pages** dans l'aide et l'historique
- ⚠️ **Confirmations interactives** pour actions sensibles

---

## 🛠️ **Installation & Configuration**

### **1. Prérequis**
```bash
# Python 3.8+
pip install discord.py python-dotenv requests selenium webdriver-manager
```

### **2. Configuration**
```bash
# Créer le fichier .env
DISCORD_BOT_TOKEN=your_discord_bot_token
EPITECH_API_TOKEN=your_epitech_bearer_token
CHANNEL_ID=your_discord_channel_id
```

### **3. Démarrage**
```bash
python bot.py
```

---

## 📈 **Architecture v2.0**

### **Fichiers Principaux :**
- **`bot.py`** - Bot principal avec surveillance automatique + `/info`
- **`slash_commands.py`** - 🎮 **TOUTES les Slash Commands** (12 commandes)
- **`epitech_api.py`** - API Epitech avec fonctions avancées
- **`token_refresher.py`** - Automation Selenium avec sessions persistantes

### **Composants Interactifs :**
- **`MouliResultsView`** - Vue avec boutons d'actualisation
- **`ProjectSelectionView`** - Sélection de projets par menu déroulant
- **`HistoryView`** - Navigation dans l'historique par passages
- **`HelpView`** - Guide d'aide avec navigation par pages
- **`ConfirmClearView`** - Confirmation interactive pour suppressions

### **Stockage :**
- **`results_history.json`** - Historique complet des résultats (auto-généré)
- **`chrome_profile_epitech/`** - Profil Chrome persistant permanent
- **Backups automatiques** avec timestamps

---

## 🔧 **Migration depuis v1.x**

### ❌ **Supprimées (v1.x):**
```bash
!mouli                  # Remplacé par /mouli
!details <projet>       # Remplacé par /details <projet>  
!history <projet>       # Remplacé par /history (avec sélection)
!stats                  # Remplacé par /stats
!status                 # Remplacé par /status
!check_now              # Remplacé par /check_now
!token                  # Remplacé par /token
!refresh_token          # Remplacé par /refresh_token
!watch                  # Remplacé par /watch
!backup                 # Remplacé par /backup
!clear_storage          # Remplacé par /clear_storage
!help_mouli             # Remplacé par /help
```

### ✅ **Nouvelles (v2.0):**
- **Interface 100% Slash Commands** avec autocomplétion Discord
- **Composants interactifs** remplaçant les paramètres manuels
- **Menus déroulants** pour sélections intuitives
- **Boutons d'action** pour actualisation et navigation
- **Confirmations interactives** pour sécurité

---

## 🚀 **Avantages v2.0**

### **🎮 UX Moderne :**
- ✅ **Autocomplétion** Discord native
- ✅ **Paramètres suggérés** automatiquement  
- ✅ **Interface graphique** au lieu de texte
- ✅ **Navigation fluide** avec boutons et menus

### **⚡ Performance :**
- ✅ **Code optimisé** et restructuré
- ✅ **Gestion d'erreurs améliorée**
- ✅ **Moins de requêtes** grâce à la mise en cache
- ✅ **Interface responsive** avec composants asynchrones

### **🔧 Maintenance :**
- ✅ **Architecture modulaire** avec Cogs
- ✅ **Séparation des responsabilités** 
- ✅ **Code plus maintenable** et extensible
- ✅ **Compatibilité future** avec Discord

---

## 📱 **Interface Utilisateur**

### **Avant (v1.x) :**
```
Utilisateur: !history G-CPE-100/cpoolday09
Bot: [Texte brut avec données]
```

### **Après (v2.0) :**
```
Utilisateur: /history
Bot: [Menu déroulant avec tous les projets]
     → Sélection "CPE Piscine - Day 09"
     → [Embed moderne avec navigation boutons ◀️ ▶️]
     → [Menu historique par passage avec dates]
```

---

## 🎯 **Commande de Migration**

Pour tester la nouvelle interface :

```bash
# Au lieu de !mouli
/mouli

# Au lieu de !history G-CPE-100/cpoolday09  
/history → Sélection dans menu → Navigation

# Au lieu de !help_mouli
/help → Navigation par pages interactives
```

---

## 🔥 **MouliCord v2.0 - Le bot Discord Epitech le plus avancé !**

**✨ Interface 100% moderne • 🎮 Slash Commands • 📱 Composants interactifs • ⚡ Ultra-rapide**