# Guide du système de stockage JSON - MouliCord

## 🚀 Vue d'ensemble

MouliCord utilise maintenant un système de stockage JSON intelligent qui :
- **Évite les notifications en doublon**
- **Compare intelligemment** les nouveaux résultats avec l'historique
- **Persiste les données** entre les redémarrages du bot
- **Offre des statistiques** détaillées sur votre progression

## 📁 Fichier de stockage

### `results_history.json`
Ce fichier est créé automatiquement au premier démarrage et contient :

```json
{
  "last_update": "2025-10-03T14:30:00",
  "results": [
    {
      "project": {
        "slug": "cpoolday09",
        "name": "C Pool Day 09"
      },
      "results": {
        "testRunId": 7271428,
        "logins": ["mathilde.angibaud@epitech.eu"]
      },
      "date": "2025-10-03T12:49:33Z"
    }
  ],
  "metadata": {
    "version": "1.0",
    "description": "Historique des résultats de moulinette Epitech"
  }
}
```

## 🔧 Commandes de gestion

### `!stats` - Statistiques détaillées
```
📈 Statistiques de stockage
📊 Résultats total: 15 résultats stockés
🕒 Dernière mise à jour: 2025-10-03T14:30
📅 Période couverte: 2025-09-23 → 2025-10-03
🏆 Top 5 des projets:
   - C Pool Day 09: 1 résultats
   - C Pool Day 08: 1 résultats  
   - count_island: 1 résultats
```

### `!backup` - Sauvegarde
Crée une copie de sauvegarde horodatée :
```
💾 Sauvegarde créée avec succès : results_backup_20251003_143000.json
```

### `!clear_storage` - Remise à zéro
⚠️ **Commande d'administration** - supprime tout l'historique
```
Utilisateur: !clear_storage
Bot: ⚠️ Cette commande va supprimer tout l'historique stocké. Tapez CONFIRMER pour continuer.
Utilisateur: CONFIRMER
Bot: 🗑️ Stockage vidé avec succès
```

## 🤖 Fonctionnement de la surveillance

### Avant (sans stockage)
1. ❌ Vérifiait seulement la date de dernière vérification
2. ❌ Pouvait notifier le même résultat plusieurs fois
3. ❌ Perdait l'historique au redémarrage

### Maintenant (avec stockage JSON)
1. ✅ Compare chaque résultat avec l'historique complet
2. ✅ Identifie uniquement les **vrais nouveaux résultats**
3. ✅ Persiste l'historique entre les redémarrages
4. ✅ Offre des statistiques détaillées

### Algorithme de détection
```python
def est_nouveau_resultat(resultat):
    # Génère une clé unique : projet_testRunId_date
    cle = f"{slug}_{testRunId}_{date}"
    
    # Vérifie si cette clé existe déjà
    return cle not in historique_stocke
```

## 📊 Exemple de workflow

### 1. Premier démarrage
```bash
python bot.py
```
```
📁 Fichier de stockage créé : results_history.json
🤖 Lancement du bot Discord...
🔍 Vérification des nouveaux résultats...
🆕 Nouveau résultat détecté: C Pool Day 09
🆕 Nouveau résultat détecté: C Pool Day 08  
💾 Stockage mis à jour : 15 résultats total
```

### 2. Vérifications suivantes (toutes les 5 min)
```
🔍 Vérification des nouveaux résultats...
📭 Aucun nouveau résultat détecté
```

### 3. Nouveau résultat disponible
```
🔍 Vérification des nouveaux résultats...
🆕 Nouveau résultat détecté: C Pool Day 10
🚨 Nouveau résultat de moulinette !
   Un nouveau résultat est disponible pour C Pool Day 10
💾 Stockage mis à jour : 16 résultats total
```

## 🛠️ Maintenance et dépannage

### Vérifier l'état du stockage
```discord
!status
```
Affiche : nombre de résultats stockés, dernière mise à jour, etc.

### Créer une sauvegarde avant maintenance
```discord
!backup
```

### En cas de problème de stockage
1. Arrêter le bot
2. Supprimer `results_history.json` 
3. Redémarrer le bot (recrée le fichier)
4. Tous les résultats seront considérés comme "nouveaux" au premier run

### Restaurer une sauvegarde
```bash
cp results_backup_YYYYMMDD_HHMMSS.json results_history.json
```

## 🔒 Sécurité

- Le fichier JSON est local au serveur
- Aucune donnée sensible stockée (pas de tokens)
- Sauvegarde recommandée avant maintenance
- Le fichier est exclu du git (dans .gitignore)

## 🚀 Performance

- **Recherche rapide** : Utilise des sets Python pour O(1) lookup
- **Stockage minimal** : Garde seulement les métadonnées nécessaires
- **Mise à jour intelligente** : N'écrit que si il y a des changements
- **Gestion mémoire** : Charge le JSON seulement lors des vérifications