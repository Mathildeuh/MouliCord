import time
import json
import os
from typing import Optional, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException


class TokenRefresher:
    """Automatise la récupération du token Epitech via Selenium avec persistance Office"""
    
    def __init__(self, headless: bool = True, timeout: int = 20, use_persistent_profile: bool = True):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.use_persistent_profile = use_persistent_profile
        self.profile_dir = os.path.join(os.getcwd(), "chrome_profile_epitech")
        
    def _setup_driver(self) -> webdriver.Chrome:
        """Configure et initialise le driver Chrome avec persistance"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--no-headless')
                
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Configuration de persistance pour Office/Azure AD
            if self.use_persistent_profile:
                # Créer le dossier de profil s'il n'existe pas
                os.makedirs(self.profile_dir, exist_ok=True)
                chrome_options.add_argument(f'--user-data-dir={self.profile_dir}')
                chrome_options.add_argument('--profile-directory=Default')
                print(f"📁 Utilisation du profil persistant: {self.profile_dir}")
            
            # Options spécifiques pour améliorer la compatibilité Office/Azure
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Activer les logs réseau pour capturer les requêtes
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            # Essayer d'utiliser le driver système ou télécharger automatiquement
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception:
                # Si pas de driver système, essayer avec webdriver_manager
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Désactiver l'indicateur d'automatisation
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            raise Exception(f"Impossible d'initialiser le driver Chrome: {str(e)}")
    
    def _extract_token_from_logs(self) -> Optional[str]:
        """Extrait le token Bearer des logs réseau avec recherche exhaustive"""
        try:
            print("📡 Analyse des logs réseau pour extraire le token...")
            logs = self.driver.get_log('performance')
            
            # Chercher dans les requêtes réseau récentes d'abord (plus efficace)
            for log in reversed(logs):  # Commencer par les plus récents
                message = json.loads(log['message'])
                
                # Chercher les requêtes réseau
                if message['message']['method'] == 'Network.requestWillBeSent':
                    request = message['message']['params']['request']
                    url = request.get('url', '')
                    
                    # Vérifier si c'est une requête vers l'API Epitech ou myresults
                    if any(domain in url for domain in ['api.epitest.eu', 'myresults.epitest.eu']):
                        headers = request.get('headers', {})
                        auth_header = headers.get('Authorization', '')
                        
                        if auth_header.startswith('Bearer '):
                            token = auth_header.replace('Bearer ', '')
                            print(f"✅ Token Bearer trouvé dans les requêtes vers: {url}")
                            return token
            
            # Si pas trouvé dans les requêtes, essayer d'autres méthodes
            print("🔍 Token non trouvé dans les requêtes, recherche alternative...")
            
            # Essayer de déclencher des requêtes en naviguant sur différentes pages
            current_url = self.driver.current_url
            if 'myresults.epitest.eu' in current_url:
                try:
                    # Essayer de cliquer sur un élément qui pourrait déclencher des requêtes API
                    print("🔄 Tentative de déclenchement de requêtes API...")
                    
                    # Attendre et chercher dans les nouveaux logs
                    time.sleep(2)
                    new_logs = self.driver.get_log('performance')
                    
                    for log in reversed(new_logs):
                        message = json.loads(log['message'])
                        if message['message']['method'] == 'Network.requestWillBeSent':
                            request = message['message']['params']['request']
                            url = request.get('url', '')
                            
                            if any(domain in url for domain in ['api.epitest.eu', 'myresults.epitest.eu']):
                                headers = request.get('headers', {})
                                auth_header = headers.get('Authorization', '')
                                
                                if auth_header.startswith('Bearer '):
                                    token = auth_header.replace('Bearer ', '')
                                    print(f"✅ Token Bearer trouvé après déclenchement: {url}")
                                    return token
                                    
                except Exception as e:
                    print(f"⚠️ Erreur lors du déclenchement: {e}")
            
            # En dernier recours, chercher dans localStorage
            try:
                print("🔍 Recherche dans localStorage...")
                local_storage = self.driver.execute_script("return localStorage;")
                for key, value in local_storage.items():
                    if 'token' in key.lower() and len(str(value)) > 50:
                        if '.' in str(value):  # Ressemble à un JWT
                            print(f"✅ Token trouvé dans localStorage: {key}")
                            return str(value)
            except Exception as e:
                print(f"⚠️ Erreur localStorage: {e}")
                        
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction du token: {e}")
            return None
    
    def _check_authentication_success(self) -> bool:
        """Vérifie si l'authentification a réussi en checkant l'URL"""
        try:
            current_url = self.driver.current_url
            print(f"🔍 URL actuelle: {current_url}")
            
            # Si redirigé vers la page avec l'année, c'est que l'auth a réussi
            return 'myresults.epitest.eu/#y/' in current_url
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification de l'URL: {e}")
            return False
    
    def _check_existing_session(self) -> bool:
        """Vérifie si une session Office valide existe déjà"""
        try:
            if not self.use_persistent_profile or not os.path.exists(self.profile_dir):
                return False
            
            print("🔍 Vérification de la session existante...")
            
            # Aller directement sur la page des résultats pour tester la session
            self.driver.get("https://myresults.epitest.eu/")
            
            # Vérifier si on est déjà authentifié (pas de bouton Login visible)
            try:
                # Si on trouve un bouton Login, la session a expiré
                login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')] | //a[contains(text(), 'Log in')]")
                print("🔓 Session expirée - authentification requise")
                return False
            except:
                # Pas de bouton Login trouvé, vérifier si on est sur la bonne page
                current_url = self.driver.current_url
                if 'myresults.epitest.eu/#y/' in current_url:
                    print("✅ Session Office active détectée !")
                    return True
                else:
                    print(f"❓ URL inattendue: {current_url}")
                    return False
                    
        except Exception as e:
            print(f"❌ Erreur lors de la vérification de session: {e}")
            return False
    
    def refresh_token(self) -> Dict:
        """
        Lance le processus de récupération du token avec persistance Office
        
        Returns:
            Dict avec 'success', 'token', 'message' et optionnellement 'error'
        """
        try:
            print("🚀 Démarrage de la récupération automatique du token...")
            
            # Initialiser le driver
            self.driver = self._setup_driver()
            
            # Vérifier si une session existe déjà
            if self.use_persistent_profile and self._check_existing_session():
                print("🎯 Session Office existante trouvée, extraction du token...")
                
                # Attendre un peu pour que les requêtes réseau se stabilisent
                time.sleep(2)
                
                # Essayer d'extraire le token directement
                token = self._extract_token_from_logs()
                if token:
                    return {
                        "success": True,
                        "token": token,
                        "message": "Token récupéré depuis la session Office persistante",
                        "url": self.driver.current_url,
                        "session_reused": True
                    }
                else:
                    print("⚠️ Aucun token trouvé dans la session existante, nouvelle authentification...")
            
            # Nouvelle authentification nécessaire
            print("📍 Navigation vers https://myresults.epitest.eu/")
            self.driver.get("https://myresults.epitest.eu/")
            
            # Attendre que la page charge et vérifier si on est déjà redirigé
            time.sleep(3)
            current_url = self.driver.current_url
            
            # Vérifier si on est déjà redirigé vers la page avec l'année
            if 'myresults.epitest.eu/index.html#y/' in current_url or 'myresults.epitest.eu/#y/' in current_url:
                print(f"✅ Déjà authentifié ! Redirigé vers: {current_url}")
                print("🎯 Token encore valide, récupération directe depuis le réseau...")
                
                # Attendre un peu pour que les requêtes réseau se stabilisent
                time.sleep(2)
                
                # Extraire le token directement
                token = self._extract_token_from_logs()
                if token:
                    return {
                        "success": True,
                        "token": token,
                        "message": "Token encore valide récupéré directement ! (session Office active)",
                        "url": current_url,
                        "session_reused": True
                    }
                else:
                    print("⚠️ Aucun token trouvé dans les logs réseau, tentative de rafraîchissement...")
                    # Rafraîchir la page pour déclencher de nouvelles requêtes
                    self.driver.refresh()
                    time.sleep(3)
                    token = self._extract_token_from_logs()
                    if token:
                        return {
                            "success": True,
                            "token": token,
                            "message": "Token récupéré après rafraîchissement de la page",
                            "url": current_url,
                            "session_reused": True
                        }
            
            # Si pas encore redirigé, procéder avec l'authentification
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Chercher et cliquer sur le bouton "Log In"
            print("🔍 Recherche du bouton 'Log In'...")
            try:
                login_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in')] | //a[contains(text(), 'Log in')] | //input[@value='Log In']"))
                )
                print("✅ Bouton 'Log In' trouvé, clic en cours...")
                login_button.click()
                
            except TimeoutException:
                # Essayer d'autres sélecteurs possibles
                try:
                    login_button = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Login') or contains(text(), 'Connexion') or contains(text(), 'Sign In')]")
                    login_button.click()
                except Exception:
                    return {
                        "success": False,
                        "error": "Bouton de connexion introuvable",
                        "message": "Le bouton 'Log In' n'a pas pu être localisé sur la page"
                    }
            
            # Attendre la redirection et l'authentification Office
            print("⏳ Attente de l'authentification Office...")
            if not self.headless:
                print("👤 Mode visible: Veuillez vous authentifier avec votre compte Office si nécessaire")
            
            # Attendre plus longtemps pour l'authentification Office (peut prendre du temps)
            time.sleep(8 if self.headless else 15)
            
            # Attendre plusieurs secondes pour que les requêtes réseau se fassent
            print("📡 Monitoring des requêtes réseau...")
            token = None
            for i in range(15):  # Attendre jusqu'à 15 secondes pour Office
                token = self._extract_token_from_logs()
                if token:
                    break
                time.sleep(1)
            
            # Vérifier si l'authentification a réussi
            auth_success = self._check_authentication_success()
            
            if token and auth_success:
                return {
                    "success": True,
                    "token": token,
                    "message": "Token récupéré avec succès ! L'authentification Office est valide et sera persistante.",
                    "url": self.driver.current_url,
                    "session_reused": False
                }
            elif token:
                return {
                    "success": True,
                    "token": token,
                    "message": "Token récupéré mais vérifiez l'authentification manuellement. Session Office créée.",
                    "url": self.driver.current_url,
                    "session_reused": False
                }
            else:
                return {
                    "success": False,
                    "error": "Token introuvable",
                    "message": "Aucun token Bearer n'a été détecté. L'authentification Office peut nécessiter une interaction manuelle en mode visible.",
                    "url": self.driver.current_url if self.driver else None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la récupération du token: {str(e)}"
            }
            
        finally:
            # Nettoyer les ressources
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
    
    def update_env_file(self, new_token: str, env_file: str = ".env") -> bool:
        """Met à jour le token dans le fichier .env"""
        try:
            if not os.path.exists(env_file):
                print(f"❌ Fichier {env_file} introuvable")
                return False
            
            # Lire le fichier actuel
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Chercher et remplacer la ligne EPITECH_API_TOKEN
            token_updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith('EPITECH_API_TOKEN='):
                    lines[i] = f'EPITECH_API_TOKEN={new_token}\n'
                    token_updated = True
                    break
            
            # Si pas trouvé, ajouter à la fin
            if not token_updated:
                lines.append(f'\nEPITECH_API_TOKEN={new_token}\n')
            
            # Réécrire le fichier
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"✅ Token mis à jour dans {env_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour de {env_file}: {e}")
            return False
    



# Fonction utilitaire pour usage direct
def auto_refresh_token(headless: bool = True, update_env: bool = True, use_persistent_profile: bool = True) -> Dict:
    """
    Fonction utilitaire pour récupérer automatiquement un nouveau token
    
    Args:
        headless: Lancer Chrome en mode headless (sans interface)
        update_env: Mettre à jour automatiquement le fichier .env
        use_persistent_profile: Utiliser un profil Chrome persistant pour garder la session Office
    
    Returns:
        Dictionnaire avec le résultat de l'opération
    """
    refresher = TokenRefresher(headless=headless, use_persistent_profile=use_persistent_profile)
    result = refresher.refresh_token()
    
    if result.get("success") and update_env and result.get("token"):
        env_updated = refresher.update_env_file(result["token"])
        result["env_updated"] = env_updated
    
    return result


