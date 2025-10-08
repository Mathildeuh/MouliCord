# MouliCord 🚀

## **Le Bot Discord Epitech le plus avancé** 🎮

**Surveillance automatique des résultats de moulinette avec interface moderne et composants interactifs !**

---

## ✨ **Fonctionnalités Principales**

### 🔄 **Surveillance Automatique 24/7**
- ✅ **Vérification toutes les 5 minutes** des nouveaux résultats
- 🔔 **Notifications @everyone** pour les nouveaux résultats
- 💾 **Sauvegarde automatique** dans `results_history.json`
- 🛡️ **Gestion d'erreurs robuste** avec retry automatique

### 🤖 **Automation Selenium Ultra-Rapide**
- 🚀 **Sessions Office persistantes** (jamais supprimées)
- ⚡ **Détection intelligente de redirections**
- 🔍 **Récupération automatique de tokens** (validité 1h)
- 💾 **Profils Chrome permanents** pour performance optimale

### 📱 **Interface Moderne Discord**
- 🎮 **Slash Commands natifs** avec autocomplétion
- 📋 **Menus déroulants interactifs** pour sélections
- 🔄 **Boutons d'actualisation** intégrés
- 📈 **Navigation par pages** dans l'aide et l'historique
- ⚠️ **Confirmations interactives** pour actions sensibles

---

## 🎮 **Commandes Disponibles**

| Commande | Description | Interface |
|----------|-------------|-----------|
| `/mouli` | 📊 Derniers résultats | 🔄 Bouton actualisation + barres colorées |
| `/history` | 📈 Sélection projet + historique | 📋 Liste projets + 📅 Navigation historique |
| `/stats` | 📊 Statistiques complètes | 🏆 Classements + graphiques |
| `/status` | 🔧 État du système | 📡 API + Token + Stockage |
| `/check_now` | 🔄 Vérification immédiate | ⚡ Force la vérification |
| `/token` | 🔐 Vérification + actualisation | ⏰ Temps restant + bouton refresh |
| `/clear_storage` | 🗑️ Vider stockage | ⚠️ Confirmation interactive |
| `/help` | ❓ Guide complet | 📖 Navigation par pages |
| `/info` | ℹ️ Informations + outils | 🏓 Ping + 📊 Status |

---

## 🎯 **Exemples d'Utilisation**

### **Navigation des Résultats :**
```
/mouli                                # 📊 Derniers résultats avec actualisation
/history                              # 📋 Sélection projet + navigation historique
/stats                                # 📈 Statistiques complètes avec classements
```

### **Gestion du Système :**
```
/token                                # 🔐 Vérification + actualisation du token
/status                               # 📡 État complet du système
/check_now                            # ⚡ Vérification immédiate
```

### **Outils et Aide :**
```
/info                                 # ℹ️ Informations + boutons Ping & Status
/help                                 # 📖 Guide interactif complet
/clear_storage                        # 🗑️ Vider le stockage (avec confirmation)
```

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
CHANNEL_ID=your_discord_channel_id

# Optionnel : Canal pour les notifications simples (par défaut: 1425583449150062592)
SIMPLE_NOTIFICATION_CHANNEL_ID=your_simple_notification_channel_id
```

**Note :** Le token Epitech est généré automatiquement au démarrage (validité ~1h)

### **3. Démarrage**
```bash
python bot.py
```

---

## 📊 **Architecture du Projet**

### **Fichiers Principaux :**
- **`bot.py`** - Bot principal avec surveillance automatique + commande `/info`
- **`slash_commands.py`** - Toutes les Slash Commands (9 commandes)
- **`epitech_api.py`** - API Epitech avec fonctions avancées
- **`token_refresher.py`** - Automation Selenium avec sessions persistantes

### **Composants Interactifs :**
- **`RefreshView`** - Boutons d'actualisation des résultats
- **`TokenView`** - Bouton de rafraîchissement du token
- **`InfoView`** - Boutons Ping et Status
- **`ProjectSelectionView`** - Sélection de projets par menu déroulant
- **`HistoryView`** - Navigation dans l'historique par passages
- **`HelpView`** - Guide d'aide avec navigation par pages
- **`ConfirmClearView`** - Confirmation interactive pour suppressions

### **Stockage :**
- **`results_history.json`** - Historique complet des résultats (auto-généré)
- **`chrome_profile_epitech/`** - Profil Chrome persistant permanent
- **Backups automatiques** avec timestamps

---

## 🎨 **Interface Utilisateur**

### **Exemple avec `/mouli` :**
```
📊 Résultats Moulinette (5 derniers)
Source: 🌐 Temps réel

✅ C Pool Day 11
📊 11/11 (100.0%)
📈 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩

✅ Lib Workshop
📊 29/29 (100.0%)
📈 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩

🟡 C Pool Day 10
📊 5/6 (83.3%)
📈 🟨🟨🟨🟨🟨🟨🟨🟨⬜⬜

[🔄 Actualiser]
```

### **Exemple avec `/history` :**
```
📋 Sélection du Projet
Choisissez un projet pour analyser son historique complet.

📊 16 projets disponibles

[Menu déroulant avec tous les projets]
→ Sélection "C Pool Day 11"
→ [Embed avec historique + navigation ◀️ ▶️]
```

---

## 🚀 **Avantages**

### **🎮 UX Moderne :**
- ✅ **Autocomplétion** Discord native
- ✅ **Interface graphique** avec boutons et menus
- ✅ **Navigation fluide** et intuitive
- ✅ **Feedback visuel** avec couleurs et emojis

### **⚡ Performance :**
- ✅ **Code optimisé** et restructuré
- ✅ **Gestion d'erreurs améliorée**
- ✅ **Mise en cache intelligente**
- ✅ **Interface responsive** avec composants asynchrones

### **🔧 Maintenance :**
- ✅ **Architecture modulaire** avec Cogs
- ✅ **Séparation des responsabilités**
- ✅ **Code maintenable** et extensible
- ✅ **Compatibilité future** avec Discord

---

## 🔥 **MouliCord - Le bot Discord Epitech le plus avancé !**

**✨ Interface 100% moderne • 🎮 Slash Commands • 📱 Composants interactifs • ⚡ Ultra-rapide • 🤖 Automation complète**