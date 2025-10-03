import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class EpitechAPI:
    """Client pour interagir avec l'API Epitech"""
    
    def __init__(self, bearer_token: str, storage_file: str = "results_history.json"):
        self.bearer_token = bearer_token
        self.base_url = "https://api.epitest.eu"
        self.storage_file = storage_file
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
        # Initialiser le stockage
        self._init_storage()
    
    def get_moulinette_results(self, year: int = 2025) -> List[Dict]:
        """
        Récupère les résultats de la moulinette pour une année donnée
        
        Args:
            year: Année des résultats (défaut: 2025)
            
        Returns:
            Liste des résultats de la moulinette
        """
        try:
            url = f"{self.base_url}/me/{year}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des résultats: {e}")
            return []
    
    def get_detailed_results(self, run_id: int) -> Optional[Dict]:
        """
        Récupère les détails d'un test spécifique
        
        Args:
            run_id: ID du test run
            
        Returns:
            Détails du test ou None en cas d'erreur
        """
        try:
            url = f"{self.base_url}/me/details/{run_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des détails du test {run_id}: {e}")
            return None
    
    def format_project_summary(self, project_data: Dict) -> str:
        """
        Formate un résumé d'un projet pour l'affichage Discord
        
        Args:
            project_data: Données d'un projet
            
        Returns:
            Résumé formaté du projet
        """
        project = project_data.get("project", {})
        results = project_data.get("results", {})
        skills = results.get("skills", {})
        
        # Calcul des statistiques
        total_tests = sum(skill.get("count", 0) for skill in skills.values())
        passed_tests = sum(skill.get("passed", 0) for skill in skills.values())
        crashed_tests = sum(skill.get("crashed", 0) for skill in skills.values())
        mandatory_failed = results.get("mandatoryFailed", 0)
        
        # Calcul du pourcentage de réussite
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Formatage de la date
        date_str = project_data.get("date", "")
        if date_str:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M")
        else:
            formatted_date = "Date inconnue"
        
        # Création du résumé
        summary = f"""
**{project.get('name', 'Projet inconnu')}** ({project.get('module', {}).get('code', 'Module inconnu')})
📅 **Date:** {formatted_date}
📊 **Tests:** {passed_tests}/{total_tests} réussis ({success_rate:.1f}%)
"""
        
        if crashed_tests > 0:
            summary += f"💥 **Crashed:** {crashed_tests}\n"
        
        if mandatory_failed > 0:
            summary += f"❌ **Mandatory Failed:** {mandatory_failed}\n"
        
        # Ajout des détails des tâches
        if skills:
            summary += "\n**Détail des tâches:**\n"
            for task_name, task_data in skills.items():
                passed = task_data.get("passed", 0)
                count = task_data.get("count", 0)
                status = "✅" if passed == count else "❌"
                summary += f"{status} {task_name}: {passed}/{count}\n"
        
        return summary
    
    def get_latest_results(self, limit: int = 5, year: int = 2025) -> List[Dict]:
        """
        Récupère les derniers résultats de la moulinette
        
        Args:
            limit: Nombre de résultats à récupérer
            year: Année des résultats
            
        Returns:
            Liste des derniers résultats
        """
        results = self.get_moulinette_results(year)
        if not results:
            return []
        
        # Trier par date (plus récent en premier)
        sorted_results = sorted(results, key=lambda x: x.get("date", ""), reverse=True)
        return sorted_results[:limit]
    
    def _init_storage(self):
        """Initialise le fichier de stockage JSON s'il n'existe pas"""
        if not os.path.exists(self.storage_file):
            initial_data = {
                "last_update": datetime.now().isoformat(),
                "results": [],
                "metadata": {
                    "version": "1.0",
                    "description": "Historique des résultats de moulinette Epitech"
                }
            }
            self._save_storage(initial_data)
            print(f"📁 Fichier de stockage créé : {self.storage_file}")
    
    def _load_storage(self) -> Dict:
        """Charge les données du fichier de stockage"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️  Erreur lors du chargement du stockage: {e}")
            return {"results": [], "last_update": None}
    
    def _save_storage(self, data: Dict):
        """Sauvegarde les données dans le fichier de stockage"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    def _get_result_key(self, result: Dict) -> str:
        """Génère une clé unique pour un résultat"""
        # Utilise testRunId + date pour une identification unique
        test_run_id = result.get("results", {}).get("testRunId")
        date = result.get("date", "")
        project_slug = result.get("project", {}).get("slug", "")
        return f"{project_slug}_{test_run_id}_{date}"
    
    def get_new_results(self, year: int = 2025) -> List[Dict]:
        """
        Récupère les nouveaux résultats en comparant avec l'historique
        
        Args:
            year: Année des résultats (défaut: 2025)
            
        Returns:
            Liste des nouveaux résultats uniquement
        """
        try:
            # Récupérer les résultats actuels de l'API
            current_results = self.get_moulinette_results(year)
            if not current_results:
                return []
            
            # Charger l'historique
            storage_data = self._load_storage()
            stored_results = storage_data.get("results", [])
            
            # Créer un set des clés existantes pour une recherche rapide
            existing_keys = set()
            for stored_result in stored_results:
                key = self._get_result_key(stored_result)
                existing_keys.add(key)
            
            # Identifier les nouveaux résultats
            new_results = []
            for result in current_results:
                result_key = self._get_result_key(result)
                if result_key not in existing_keys:
                    new_results.append(result)
                    print(f"🆕 Nouveau résultat détecté: {result.get('project', {}).get('name', 'Inconnu')}")
            
            # Mettre à jour le stockage avec tous les résultats actuels
            if new_results or len(stored_results) != len(current_results):
                storage_data["results"] = current_results
                storage_data["last_update"] = datetime.now().isoformat()
                self._save_storage(storage_data)
                print(f"💾 Stockage mis à jour : {len(current_results)} résultats total")
            
            return new_results
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification des nouveaux résultats: {e}")
            return []
    
    def get_storage_stats(self) -> Dict:
        """Retourne des statistiques sur le stockage"""
        try:
            data = self._load_storage()
            results = data.get("results", [])
            
            if not results:
                return {
                    "total_results": 0,
                    "last_update": "Jamais",
                    "date_range": "N/A",
                    "projects": []
                }
            
            # Calculer les statistiques
            dates = [r.get("date", "") for r in results if r.get("date")]
            dates.sort()
            
            projects = {}
            for result in results:
                project_name = result.get("project", {}).get("name", "Inconnu")
                if project_name not in projects:
                    projects[project_name] = 0
                projects[project_name] += 1
            
            return {
                "total_results": len(results),
                "last_update": data.get("last_update", "Inconnu"),
                "date_range": f"{dates[0]} → {dates[-1]}" if dates else "N/A",
                "projects": dict(sorted(projects.items(), key=lambda x: x[1], reverse=True))
            }
            
        except Exception as e:
            print(f"❌ Erreur lors du calcul des statistiques: {e}")
            return {"error": str(e)}
    
    def clear_storage(self):
        """Vide le stockage (utile pour les tests)"""
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
                print(f"🗑️  Stockage supprimé : {self.storage_file}")
            self._init_storage()
        except Exception as e:
            print(f"❌ Erreur lors de la suppression du stockage: {e}")
    
    def backup_storage(self, backup_file: Optional[str] = None):
        """Crée une sauvegarde du stockage"""
        try:
            if not backup_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"results_backup_{timestamp}.json"
            
            data = self._load_storage()
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Sauvegarde créée : {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return None