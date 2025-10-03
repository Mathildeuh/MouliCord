# Guide d'utilisation MouliCord

## Configuration initiale

1. **Copier le fichier de configuration**
```bash
cp .env.example .env
```

2. **Éditer le fichier .env**
```bash
nano .env
```

Remplissez les trois variables :
- `DISCORD_TOKEN` : Token de votre bot Discord
- `EPITECH_API_TOKEN` : Token Bearer de l'API Epitech
- `CHANNEL_ID` : ID du canal Discord pour les notifications

3. **Tester la configuration**
```bash
python test_config.py
python test_surveillance.py  # Test de la surveillance automatique
```

4. **Démarrer le bot**
```bash
python bot.py
# ou
./start.sh
```

## Commandes Discord

### `!mouli [nombre]`
Affiche les derniers résultats de la moulinette.

**Exemples :**
- `!mouli` → Affiche les 5 derniers résultats
- `!mouli 3` → Affiche les 3 derniers résultats
- `!mouli 10` → Affiche les 10 derniers résultats

### `!details <run_id>`
Affiche les détails complets d'un test spécifique.

**Exemple :**
- `!details 7271428` → Détails du test avec l'ID 7271428

**Comment trouver un run_id ?**
- Utilisez `!mouli` pour voir les résultats récents
- Le run_id est affiché dans le résumé de chaque projet
- Ou consultez directement l'API Epitech

### `!watch`
Active ou désactive la surveillance automatique des nouveaux résultats.

**Fonctionnement :**
- Le bot vérifie automatiquement toutes les 5 minutes
- Notification instantanée des nouveaux résultats
- Peut être activée/désactivée à volonté

### `!status`
Affiche le statut de la surveillance automatique.

**Informations affichées :**
- État de la surveillance (activée/désactivée)
- Dernière vérification effectuée
- Prochaine vérification prévue

### `!check_now`
Force une vérification immédiate des nouveaux résultats.

**Usage :**
- Utile pour tester la surveillance
- Vérifie instantanément s'il y a de nouveaux résultats
- N'affecte pas le cycle automatique de 5 minutes

### `!help_mouli`
Affiche l'aide intégrée du bot.

## Exemples d'utilisation

### Consultation rapide
```
Utilisateur: !mouli 3
Bot: [Affiche les 3 derniers résultats avec statistiques]
```

### Analyse détaillée
```
Utilisateur: !details 7271428
Bot: [Affiche tous les détails du test, tâches, traces d'exécution]
```

### Surveillance automatique
```
Utilisateur: !watch
Bot: 🟢 Surveillance automatique activée
     🕒 Dernière vérification: 03/10/2025 à 14:30 UTC
     ⏰ Prochaine vérification dans 5 minutes

Utilisateur: !status
Bot: 📊 Statut de la surveillance
     Surveillance automatique: 🟢 Activée
     Dernière vérification: 03/10/2025 à 14:35 UTC
     Prochaine vérification: 03/10/2025 à 14:40 UTC

[5 minutes plus tard, nouveau résultat disponible]
Bot: 🚨 Nouveau résultat de moulinette !
     Un nouveau résultat est disponible pour C Pool Day 11
     [Résumé du projet avec statistiques]

Utilisateur: !check_now
Bot: 🔍 Vérification manuelle en cours...
     [Vérifie immédiatement s'il y a de nouveaux résultats]
```

## Informations affichées

### Résumé de projet
- Nom du projet et module
- Date et heure du test
- Nombre de tests réussis/total
- Pourcentage de réussite
- Détail des tâches (✅/❌)
- Tests crashed ou mandatory failed

### Détails complets
- Informations du projet (module, campus, année)
- Liste détaillée de toutes les compétences
- Traces d'exécution (logs de compilation et tests)
- Commit Git utilisé
- Style/Lint errors

## Dépannage

### "❌ Aucun résultat trouvé"
- Vérifiez votre token Epitech
- Assurez-vous d'avoir des résultats pour 2025
- Testez avec `python test_config.py`

### "Canal non trouvé"
- Vérifiez l'ID du canal dans .env
- Assurez-vous que le bot a accès au canal
- Le bot doit avoir les permissions de lecture/écriture

### "Erreur lors de la récupération"
- Vérifiez votre connexion Internet
- Le token Epitech peut avoir expiré
- L'API Epitech peut être temporairement indisponible

### Le bot ne répond pas
- Vérifiez que le bot est en ligne sur Discord
- Le token Discord peut être invalide
- Redémarrez le bot avec `python bot.py`