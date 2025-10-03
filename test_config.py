#!/usr/bin/env python3
"""
Test rapide pour vérifier la configuration et tester l'API Epitech
"""

import os
from dotenv import load_dotenv
from epitech_api import EpitechAPI

def test_configuration():
    """Teste la configuration et la connexion à l'API"""
    
    print("🔍 Test de la configuration MouliCord...\n")
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Vérifier les variables d'environnement
    discord_token = os.getenv('DISCORD_TOKEN')
    epitech_token = os.getenv('EPITECH_API_TOKEN')
    channel_id = os.getenv('CHANNEL_ID')
    
    print("📋 Variables d'environnement:")
    print(f"   DISCORD_TOKEN: {'✅ Défini' if discord_token else '❌ Manquant'}")
    print(f"   EPITECH_API_TOKEN: {'✅ Défini' if epitech_token else '❌ Manquant'}")
    print(f"   CHANNEL_ID: {'✅ Défini' if channel_id else '❌ Manquant'}")
    
    if not all([discord_token, epitech_token, channel_id]):
        print("\n❌ Configuration incomplète!")
        print("📝 Vérifiez votre fichier .env")
        return False
    
    # Tester l'API Epitech
    print(f"\n🔗 Test de l'API Epitech...")
    try:
        api = EpitechAPI(epitech_token)
        results = api.get_moulinette_results(2025)
        
        if results:
            print(f"✅ API fonctionnelle - {len(results)} résultats trouvés")
            
            # Afficher le dernier résultat
            if results:
                latest = max(results, key=lambda x: x.get('date', ''))
                project_name = latest.get('project', {}).get('name', 'Projet inconnu')
                date = latest.get('date', 'Date inconnue')
                print(f"📊 Dernier résultat: {project_name} ({date})")
                
                # Test des détails
                run_id = latest.get('results', {}).get('testRunId')
                if run_id:
                    details = api.get_detailed_results(run_id)
                    if details:
                        print(f"✅ Détails récupérés pour le test {run_id}")
                    else:
                        print(f"⚠️  Impossible de récupérer les détails du test {run_id}")
        else:
            print("⚠️  Aucun résultat trouvé")
            
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return False
    
    print(f"\n🎉 Configuration validée!")
    print(f"🚀 Vous pouvez maintenant lancer le bot avec:")
    print(f"   python bot.py")
    print(f"   ou")
    print(f"   ./start.sh")
    
    return True


if __name__ == "__main__":
    test_configuration()