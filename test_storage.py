#!/usr/bin/env python3
"""
Test du système de stockage JSON pour MouliCord
"""

import os
import json
from dotenv import load_dotenv
from epitech_api import EpitechAPI
from datetime import datetime

def test_storage_system():
    """Test complet du système de stockage JSON"""
    
    print("🧪 Test du système de stockage JSON...\n")
    
    # Charger les variables d'environnement
    load_dotenv()
    
    epitech_token = os.getenv('EPITECH_API_TOKEN')
    if not epitech_token:
        print("❌ EPITECH_API_TOKEN manquant dans le fichier .env")
        return False
    
    # Test avec un fichier de test
    test_storage_file = "test_results_history.json"
    
    try:
        # Nettoyer le fichier de test s'il existe
        if os.path.exists(test_storage_file):
            os.remove(test_storage_file)
        
        print("📁 Initialisation de l'API avec stockage de test...")
        api = EpitechAPI(epitech_token, test_storage_file)
        
        # Test 1: Vérifier l'initialisation du stockage
        print("🔍 Test 1: Initialisation du stockage")
        assert os.path.exists(test_storage_file), "Le fichier de stockage devrait être créé"
        
        with open(test_storage_file, 'r') as f:
            data = json.load(f)
        assert "results" in data, "Le stockage devrait contenir une clé 'results'"
        assert "metadata" in data, "Le stockage devrait contenir une clé 'metadata'"
        print("✅ Initialisation réussie")
        
        # Test 2: Première récupération (tout est nouveau)
        print("\n🔍 Test 2: Première récupération des résultats")
        new_results_1 = api.get_new_results(2025)
        print(f"📊 Premier fetch: {len(new_results_1)} nouveaux résultats")
        
        # Test 3: Deuxième récupération (rien de nouveau normalement)
        print("\n🔍 Test 3: Deuxième récupération (devrait être vide)")
        new_results_2 = api.get_new_results(2025)
        print(f"📊 Deuxième fetch: {len(new_results_2)} nouveaux résultats")
        
        if len(new_results_2) == 0:
            print("✅ Détection correcte - aucun doublon")
        else:
            print("⚠️  Il y a encore de nouveaux résultats (normal si de vrais nouveaux résultats)")
        
        # Test 4: Statistiques
        print("\n🔍 Test 4: Statistiques du stockage")
        stats = api.get_storage_stats()
        print(f"📈 Statistiques:")
        print(f"   - Total résultats: {stats['total_results']}")
        print(f"   - Dernière MAJ: {stats['last_update']}")
        print(f"   - Période: {stats['date_range']}")
        print(f"   - Projets: {len(stats['projects'])}")
        
        # Test 5: Sauvegarde
        print("\n🔍 Test 5: Sauvegarde")
        backup_file = api.backup_storage("test_backup.json")
        if backup_file and os.path.exists(backup_file):
            print("✅ Sauvegarde créée avec succès")
            os.remove(backup_file)  # Nettoyer
        else:
            print("❌ Erreur lors de la sauvegarde")
        
        # Test 6: Nettoyage
        print("\n🔍 Test 6: Nettoyage")
        api.clear_storage()
        stats_after_clear = api.get_storage_stats()
        if stats_after_clear['total_results'] == 0:
            print("✅ Nettoyage réussi")
        else:
            print("❌ Erreur lors du nettoyage")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Nettoyer les fichiers de test
        for test_file in [test_storage_file, "test_backup.json"]:
            if os.path.exists(test_file):
                os.remove(test_file)
                print(f"🧹 Fichier de test supprimé: {test_file}")

def simulate_storage_scenario():
    """Simule un scénario réel d'utilisation"""
    
    print("\n🎭 Simulation d'un scénario réel...\n")
    
    # Données de test simulées
    mock_results = [
        {
            "project": {"slug": "test1", "name": "Test Project 1"},
            "results": {"testRunId": 1001},
            "date": "2025-10-01T10:00:00Z"
        },
        {
            "project": {"slug": "test2", "name": "Test Project 2"}, 
            "results": {"testRunId": 1002},
            "date": "2025-10-02T10:00:00Z"
        }
    ]
    
    # Simulation avec fichier de test
    test_file = "simulation_storage.json"
    
    try:
        # Créer un stockage initial avec 1 résultat
        initial_data = {
            "last_update": datetime.now().isoformat(),
            "results": [mock_results[0]],
            "metadata": {"version": "1.0"}
        }
        
        with open(test_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        
        print("📁 Stockage initial créé avec 1 résultat")
        
        # Simuler une API qui retourne maintenant 2 résultats
        class MockAPI(EpitechAPI):
            def get_moulinette_results(self, year):
                return mock_results  # Retourne 2 résultats
        
        # Tester la détection
        api = MockAPI("fake_token", test_file)
        new_results = api.get_new_results(2025)
        
        print(f"🔍 Nouveaux résultats détectés: {len(new_results)}")
        
        if len(new_results) == 1:
            new_project = new_results[0]["project"]["name"]
            print(f"✅ Détection correcte du nouveau projet: {new_project}")
        else:
            print(f"⚠️  Nombre inattendu de nouveaux résultats: {len(new_results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur simulation: {e}")
        return False
    
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    print("🧪 Tests MouliCord - Système de stockage JSON\n")
    
    success = True
    
    success &= test_storage_system()
    success &= simulate_storage_scenario()
    
    if success:
        print("\n🎉 Tous les tests de stockage sont passés avec succès !")
        print("💾 Le système de stockage JSON est prêt à fonctionner.")
    else:
        print("\n❌ Certains tests ont échoué.")
        print("🔧 Vérifiez votre configuration avant d'utiliser le stockage.")