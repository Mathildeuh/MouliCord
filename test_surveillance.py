#!/usr/bin/env python3
"""
Script de test pour la surveillance automatique de MouliCord
"""

import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from epitech_api import EpitechAPI

def test_surveillance():
    """Test la logique de surveillance des nouveaux résultats"""
    
    print("🔍 Test de la surveillance automatique...\n")
    
    # Charger les variables d'environnement
    load_dotenv()
    
    epitech_token = os.getenv('EPITECH_API_TOKEN')
    if not epitech_token:
        print("❌ EPITECH_API_TOKEN manquant dans le fichier .env")
        return False
    
    # Initialiser l'API
    api = EpitechAPI(epitech_token)
    
    # Simuler la logique de surveillance
    print("📊 Récupération des résultats récents...")
    results = api.get_latest_results(5)
    
    if not results:
        print("❌ Aucun résultat trouvé")
        return False
    
    print(f"✅ {len(results)} résultats récupérés")
    
    # Simuler une dernière vérification (1 heure dans le passé)
    last_check = datetime.now(timezone.utc) - timedelta(hours=1)
    print(f"🕐 Dernière vérification simulée: {last_check}")
    
    # Vérifier les nouveaux résultats
    new_results = []
    for result in results:
        date_str = result.get("date", "")
        if date_str:
            result_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            if result_date > last_check:
                project_name = result.get("project", {}).get("name", "Projet inconnu")
                new_results.append((project_name, result_date))
                print(f"🆕 Nouveau résultat détecté: {project_name} ({result_date})")
    
    if new_results:
        print(f"\n🎉 {len(new_results)} nouveau(x) résultat(s) détecté(s) !")
        for name, date in sorted(new_results, key=lambda x: x[1]):
            print(f"   • {name} - {date.strftime('%d/%m/%Y à %H:%M UTC')}")
    else:
        print("\n📭 Aucun nouveau résultat depuis la dernière vérification")
    
    # Test du formatage
    print("\n📝 Test du formatage d'un résultat:")
    latest = results[0]
    summary = api.format_project_summary(latest)
    print("=" * 50)
    print(summary)
    print("=" * 50)
    
    return True

def test_timezone_handling():
    """Test la gestion des timezones"""
    
    print("\n🌍 Test de la gestion des timezones...")
    
    # Dates de test
    date_str = "2025-10-03T12:49:33Z"
    
    # Parser avec timezone UTC
    utc_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    print(f"Date parsée: {utc_date}")
    print(f"Timezone: {utc_date.tzinfo}")
    
    # Date de comparaison
    now_utc = datetime.now(timezone.utc)
    print(f"Maintenant (UTC): {now_utc}")
    
    # Test de comparaison
    try:
        is_newer = utc_date > now_utc
        print(f"✅ Comparaison réussie: {utc_date} > {now_utc} = {is_newer}")
    except Exception as e:
        print(f"❌ Erreur de comparaison: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Tests MouliCord - Surveillance automatique\n")
    
    success = True
    
    success &= test_timezone_handling()
    success &= test_surveillance()
    
    if success:
        print("\n🎉 Tous les tests sont passés avec succès !")
        print("🚀 La surveillance automatique devrait fonctionner correctement.")
    else:
        print("\n❌ Certains tests ont échoué.")
        print("🔧 Vérifiez votre configuration avant de lancer le bot.")