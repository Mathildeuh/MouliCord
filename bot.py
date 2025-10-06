import discord
from discord.ext import commands, tasks
import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from epitech_api import EpitechAPI
from token_refresher import auto_refresh_token

# Charger les variables d'environnement
load_dotenv()

# Variables globales pour la gestion des tokens
current_token = None
epitech_api = None

# --- Journalisation unifiée ---
def _log_info(message: str):
    print(f"[INFO] {message}")

def _log_warn(message: str):
    print(f"[WARN] {message}")

def _log_error(message: str):
    print(f"[ERREUR] {message}")

def _log_ok(message: str):
    print(f"[OK] {message}")

def _propagate_api_to_cogs():
    """Propage l'instance EpitechAPI actualisée aux cogs (slash commands)."""
    try:
        from discord.ext import commands as _commands  # local import to avoid type checkers
        if bot:
            slash_commands_cog = bot.get_cog('MouliCordSlashCommands')
            if slash_commands_cog and hasattr(slash_commands_cog, 'update_epitech_api'):
                slash_commands_cog.update_epitech_api(epitech_api)
                _log_info("API propagée aux commandes slash")
    except Exception as e:
        _log_warn(f"Impossible de propager l'API aux cogs: {e}")

# (Gestion du topic supprimée)

def get_fresh_token():
    """Récupère un nouveau token depuis Epitech avec retry logic"""
    global current_token, epitech_api
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            _log_info(f"Récupération d'un nouveau token (tentative {attempt + 1}/{max_retries})…")
            result = auto_refresh_token(headless=True, update_env=False)
            
            if result.get("success") and result.get("token"):
                new_token = result["token"]
                
                # Valider le format du token avant de l'utiliser
                if not new_token or not isinstance(new_token, str):
                    _log_error("Token récupéré invalide (vide ou mauvais type)")
                    if attempt < max_retries - 1:
                        _log_info("Nouvelle tentative dans 5s…")
                        time.sleep(5)
                        continue
                    return False
                
                # Nettoyer le token (retirer "Bearer " si présent)
                clean_token = new_token.strip()
                if clean_token.startswith("Bearer "):
                    clean_token = clean_token[7:].strip()
                
                # Vérifier que c'est un JWT valide (3 parties séparées par des points)
                parts = clean_token.split('.')
                if len(parts) != 3:
                    _log_error(f"Token JWT invalide: {len(parts)} parties au lieu de 3")
                    if attempt < max_retries - 1:
                        _log_info("Nouvelle tentative dans 10s…")
                        time.sleep(10)
                        continue
                    return False
                
                # Tester la création de l'API avec le nouveau token
                try:
                    test_api = EpitechAPI(clean_token, "results_history.json")
                    token_info = test_api.get_token_info()
                    
                    if "error" in token_info:
                        _log_error(f"Token invalide: {token_info['error']}")
                        if attempt < max_retries - 1:
                            _log_info("Nouvelle tentative dans 10s…")
                            time.sleep(10)
                            continue
                        return False
                    
                    if token_info.get("is_expired", True):
                        _log_error("Token récupéré déjà expiré")
                        if attempt < max_retries - 1:
                            _log_info("Nouvelle tentative dans 5s…")
                            time.sleep(5)
                            continue
                        return False
                    
                    # Token valide, l'utiliser
                    current_token = clean_token
                    epitech_api = test_api
                    
                    _log_ok("Nouveau token récupéré et validé (validité ~1h)")
                    # Propager immédiatement aux cogs pour que toutes les commandes utilisent le nouveau token
                    _propagate_api_to_cogs()
                    return True
                    
                except Exception as e:
                    _log_error(f"Erreur lors de la validation du token: {e}")
                    if attempt < max_retries - 1:
                        _log_info("Nouvelle tentative dans 10s…")
                        time.sleep(10)
                        continue
                    return False
                
            else:
                _log_error(f"Échec de récupération du token: {result.get('error', 'Erreur inconnue')}")
                if attempt < max_retries - 1:
                    _log_info("Nouvelle tentative dans 15s…")
                    time.sleep(15)
                    continue
                return False
                
        except Exception as e:
            _log_error(f"Erreur lors de la récupération du token (tentative {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                _log_info("Nouvelle tentative dans 15s…")
                time.sleep(15)
                continue
            return False
    
    _log_error("Échec définitif après 3 tentatives")
    return False

def init_token_from_env():
    """(Désactivé) Toujours générer un token au démarrage; ne jamais lire depuis .env"""
    return False

def ensure_valid_token():
    """S'assure que le token est valide, le renouvelle si nécessaire"""
    global current_token, epitech_api
    
    # Toujours générer un token si aucun n'est disponible
    if not current_token or not epitech_api:
        return get_fresh_token()
    
    try:
        # Vérifier si le token actuel est encore valide
        token_info = epitech_api.get_token_info()
        
        if token_info.get("is_expired", True):
            print("⏰ Token expiré (durée de vie: 1h), renouvellement automatique...")
            return get_fresh_token()
        
        # Token valide
        return True
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification du token: {e}")
        print("🔄 Tentative de récupération d'un nouveau token...")
        return get_fresh_token()

def validate_environment():
    """Valide que toutes les variables d'environnement nécessaires sont présentes"""
    required_vars = {
        'DISCORD_BOT_TOKEN': 'Token du bot Discord',
        'CHANNEL_ID': 'ID du canal Discord'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value.strip() == '':
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        _log_error("Variables d'environnement manquantes:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\nConseil: créez un fichier .env avec:")
        print("   DISCORD_BOT_TOKEN=your_bot_token")
        print("   CHANNEL_ID=your_channel_id")
        print("\nNote: le token Epitech est généré automatiquement (validité ~1h)")
        return False
    return True

# Vérifier les variables d'environnement au démarrage
if not validate_environment():
    exit(1)

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)


# Variables globales - l'API sera initialisée après récupération du token
channel_id = int(os.getenv('CHANNEL_ID', '0'))


class MouliCordBot:
    """Bot Discord pour les résultats de la moulinette Epitech - Tokens auto-renouvelés toutes les heures"""
    
    def __init__(self):
        print("🚀 MouliCord v2.0 - Full Slash Commands Edition")
        print("🕒 Surveillance initialisée avec stockage JSON")
    
    async def send_to_channel(self, message: str, embed: discord.Embed | None = None):
        """Envoie un message dans le canal configuré"""
        channel = bot.get_channel(channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            if embed:
                # Permettre les mentions @everyone
                await channel.send(message, embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
            else:
                await channel.send(message, allowed_mentions=discord.AllowedMentions(everyone=True))
        else:
            print(f"Canal {channel_id} non trouvé ou non compatible")
    
    async def send_moulinette_notification(self, result: dict):
        """Envoie une notification pour un nouveau résultat de moulinette"""
        try:
            # Extraire les informations du résultat
            project_name = result.get("project", {}).get("name", "Projet inconnu")
            project_slug = result.get("project", {}).get("slug", "")
            module_code = result.get("project", {}).get("module", {}).get("code", "G-CPE-100")
            test_run_id = result.get("results", {}).get("testRunId", "")
            date = result.get("date", "")
            
            # Construire l'URL vers le projet sur myresults.epitest.eu
            project_url = None
            if project_slug and test_run_id:
                project_url = f"https://myresults.epitest.eu/index.html#d/2025/{module_code}/{project_slug}/{test_run_id}"
            
            # Calculer les vrais scores depuis la structure skills
            skills = result.get("results", {}).get("skills", {})
            passed = 0
            total = 0
            
            for skill_name, skill_data in skills.items():
                skill_passed = skill_data.get("passed", 0)
                skill_count = skill_data.get("count", 0)
                passed += skill_passed
                total += skill_count
            
            percentage = round((passed / total * 100) if total > 0 else 0, 1)
            
            # Déterminer la couleur et l'emoji selon le score
            if percentage >= 100:
                color = discord.Color.green()
                emoji = "✅"
                status = "PARFAIT"
            elif percentage >= 80:
                color = discord.Color.orange()
                emoji = "🟡"
                status = "BIEN"
            elif percentage >= 50:
                color = discord.Color.orange()
                emoji = "🟠"
                status = "MOYEN"
            else:
                color = discord.Color.red()
                emoji = "❌"
                status = "ÉCHEC"
            
            # Créer l'embed de notification avec URL cliquable
            title = f"{emoji} Nouvelle Moulinette - {project_name}"
            
            embed = discord.Embed(
                title=title,
                url=project_url if project_url else None,  # Rend tout le titre cliquable
                description=f"**{status}** • {passed}/{total} tests ({percentage}%)",
                color=color,
                timestamp=datetime.fromisoformat(date.replace('Z', '+00:00')) if date else datetime.now()
            )
            
            embed.add_field(
                name="📊 Résultats",
                value=f"• Tests passés: **{passed}/{total}** \n• Pourcentage: **{percentage}%**",
                inline=True
            )
            
            if date:
                embed.add_field(
                    name="🕒 Date",
                    value=f"<t:{int(datetime.fromisoformat(date.replace('Z', '+00:00')).timestamp())}:R>",
                    inline=True
                )
            
            # Informations supplémentaires avec lien vers le projet
            if project_url:
                embed.add_field(
                    name="",
                    value=f"🔗 [Voir sur EpiTest]({project_url})",
                    inline=False
                )
            elif project_slug:
                embed.add_field(
                    name="🔗 Projet",
                    value=f"`{project_slug}`",
                    inline=True
                )
            
            embed.set_footer(text="MouliCord v2.0 • Surveillance automatique")
            
            # Envoyer la notification avec @everyone pour les nouveaux résultats
            message = f"<@&1424827053508657252> 🚨 **NOUVEAU RÉSULTAT DE MOULINETTE !**"
            
            await self.send_to_channel(message, embed)
            print(f"📨 Notification envoyée pour: {project_name} ({percentage}%)")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de la notification: {e}")


moulibot = MouliCordBot()


@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    _log_ok(f"Connecté à Discord en tant que {bot.user}")
    _log_info(f"Canal configuré: {channel_id}")
    # (Topic du salon désactivé)
    
    # Récupération automatique du token au démarrage
    # Charger les Slash Commands d'abord
    try:
        await bot.load_extension('slash_commands')
        _log_ok('Commandes slash chargées')
    except Exception as e:
        _log_error(f"Erreur lors du chargement des commandes slash: {e}")
    
    _log_info("Initialisation du token Epitech…")
    if not ensure_valid_token():
        _log_error("Impossible de récupérer le token Epitech")
        _log_warn("Le bot continue sans les fonctionnalités Epitech")
    else:
        _log_ok("Token Epitech configuré")
        
        # Mettre à jour l'API dans le Cog des slash commands
        try:
            slash_commands_cog = bot.get_cog('MouliCordSlashCommands')
            if slash_commands_cog and hasattr(slash_commands_cog, 'update_epitech_api'):
                slash_commands_cog.update_epitech_api(epitech_api)
                _log_info("API mise à jour dans les commandes slash")
        except Exception as e:
            _log_warn(f"Impossible de mettre à jour l'API dans les commandes: {e}")
    
    # Synchroniser les commandes avec Discord
    try:
        synced = await bot.tree.sync()
        _log_ok(f"{len(synced)} commandes slash synchronisées")
    except Exception as e:
        _log_error(f"Erreur lors de la synchronisation des commandes: {e}")
    
    # Vérification immédiate au démarrage pour les nouveaux résultats
    try:
        _log_info("Vérification des nouveaux résultats au démarrage…")
        
        if not ensure_valid_token():
            _log_warn("Token indisponible, vérification au démarrage ignorée")
            return
        
        if epitech_api:
            new_results_at_startup = epitech_api.get_new_results(2025)
        else:
            new_results_at_startup = []
            _log_warn("API non initialisée au démarrage")
        
        if new_results_at_startup:
            _log_ok(f"{len(new_results_at_startup)} nouveau(x) résultat(s) détecté(s) au démarrage")
            for result in new_results_at_startup:
                await moulibot.send_moulinette_notification(result)
        else:
            _log_ok("Aucun nouveau résultat au démarrage")
    except Exception as e:
        _log_warn(f"Erreur lors de la vérification au démarrage: {e}")
    
    # Démarrer les tâches automatiques
    check_new_results.start()
    check_token_expiration.start()


@tasks.loop(minutes=5)
async def check_new_results():
    """Tâche de vérification automatique des nouveaux résultats"""
    try:
        _log_info(f"Vérification automatique - {datetime.now().strftime('%H:%M:%S')}")
        
        # S'assurer que le token est valide avant de vérifier
        if not ensure_valid_token():
            _log_warn("Token indisponible, vérification ignorée")
            return
        
        # Vérifier les nouveaux résultats
        if epitech_api:
            new_results = epitech_api.get_new_results(2025)
        else:
            _log_warn("API non initialisée")
            return
        
        if new_results:
            _log_ok(f"{len(new_results)} nouveau(x) résultat(s) détecté(s)")
            
            # Envoyer une notification pour chaque nouveau résultat
            for result in new_results:
                await moulibot.send_moulinette_notification(result)
                
        else:
            _log_info("Aucun nouveau résultat détecté")
            
    except Exception as e:
        _log_error(f"Erreur lors de la vérification automatique: {e}")


@check_new_results.before_loop
async def before_check_new_results():
    """Attendre que le bot soit prêt avant de commencer la vérification"""
    await bot.wait_until_ready()


@tasks.loop(hours=1)
async def check_token_expiration():
    """Vérification et renouvellement préventif du token (durée de vie: 1h)"""
    try:
        _log_info(f"Vérification de l'expiration du token - {datetime.now().strftime('%H:%M:%S')}")
        
        if epitech_api and current_token:
            token_info = epitech_api.get_token_info()
            
            if token_info.get("is_expired", False):
                _log_info("Token expiré détecté, renouvellement automatique…")
                ensure_valid_token()
            else:
                _log_ok("Token valide")
        else:
            _log_warn("Aucun token configuré, tentative de récupération…")
            ensure_valid_token()
            
    except Exception as e:
        _log_error(f"Erreur lors de la vérification du token: {e}")


@check_token_expiration.before_loop
async def before_check_token_expiration():
    """Attendre que le bot soit prêt avant de commencer la vérification des tokens"""
    await bot.wait_until_ready()


# Commande hybride pour la compatibilité (optionnelle)
@bot.hybrid_command(name="info", description="ℹ️ Informations sur MouliCord v2.0")
async def info_command(ctx):
    """Commande d'information sur le bot"""
    embed = discord.Embed(
        title="🚀 MouliCord v2.0",
        description="**Le bot Discord Epitech le plus avancé !**\n\n✨ **Nouveautés v2.0:**\n• 🎮 Interface 100% Slash Commands\n• 📱 Composants interactifs modernes\n• 📋 Menus déroulants intuitifs\n• 🔄 Boutons d'actualisation\n• 📈 Navigation historique avancée",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="📊 Commandes principales",
        value="• `/mouli` - Derniers résultats\n• `/history` - Historique des projets\n• `/stats` - Statistiques complètes\n• `/status` - État du système",
        inline=True
    )
    
    embed.add_field(
        name="🔧 Gestion",
        value="• `/token` - Vérifier le token\n• `/refresh_token` - Actualiser\n• `/backup` - Sauvegarde\n• `/help` - Guide complet",
        inline=True
    )
    
    embed.add_field(
        name="⚡ Fonctionnalités",
        value="• 🤖 Surveillance 24/7\n• 🔔 Notifications @everyone\n• 💾 Sauvegarde automatique\n• 🛡️ Token auto-refresh",
        inline=False
    )
    
    embed.set_footer(text="Utilisez /help pour le guide complet • MouliCord v2.0")
    
    await ctx.send(embed=embed)


@bot.hybrid_command(name="test_notification", description="🧪 Tester une notification de moulinette")
async def test_notification_command(ctx):
    """Commande pour tester les notifications de moulinette"""
    try:
        # S'assurer que le token est valide
        if not ensure_valid_token():
            await ctx.send("❌ **Erreur:** Token Epitech indisponible")
            return
        
        # Récupérer le premier résultat pour test
        if epitech_api:
            results = epitech_api.get_moulinette_results(2025)
        else:
            await ctx.send("❌ **Erreur:** API non initialisée")
            return
        
        if results:
            # Simuler une nouvelle moulinette avec le premier résultat
            test_result = results[0]
            
            await ctx.send("🧪 **Test de notification en cours...**")
            await moulibot.send_moulinette_notification(test_result)
            
            await ctx.send("✅ **Notification de test envoyée !**\nVérifiez le canal configuré.")
        else:
            await ctx.send("❌ **Aucun résultat disponible pour le test.**")
            
    except Exception as e:
        await ctx.send(f"❌ **Erreur lors du test:** {e}")


@bot.hybrid_command(name="force_check", description="🔍 Forcer une vérification des nouvelles moulinettes")
async def force_check_command(ctx):
    """Commande pour forcer une vérification manuelle"""
    try:
        await ctx.send("🔍 **Vérification manuelle en cours...**")
        
        # S'assurer que le token est valide
        if not ensure_valid_token():
            await ctx.send("❌ **Erreur:** Token Epitech indisponible")
            return

        if epitech_api:
            new_results = epitech_api.get_new_results(2025)
        else:
            await ctx.send("❌ **Erreur:** API non initialisée")
            return
            
        if new_results:
            await ctx.send(f"🆕 **{len(new_results)} nouveaux résultats détectés !**")
            
            for result in new_results:
                await moulibot.send_moulinette_notification(result)
                
            await ctx.send(f"✅ **{len(new_results)} notifications envoyées !**")
        else:
            await ctx.send("📊 **Aucun nouveau résultat détecté.**\nTous les résultats sont déjà connus.")
            
    except Exception as e:
        await ctx.send(f"❌ **Erreur lors de la vérification:** {e}")


if __name__ == "__main__":
    try:
        _log_info("Démarrage de MouliCord v2.0…")
        
        # Vérification finale avant démarrage
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        if not discord_token:
            _log_error("DISCORD_BOT_TOKEN manquant dans le fichier .env")
            exit(1)
            
        _log_ok("Configuration validée")
        _log_info(f"Canal configuré: {channel_id}")
        bot.run(discord_token)
        
    except discord.LoginFailure:
        _log_error("Token Discord invalide ! Vérifiez DISCORD_BOT_TOKEN dans .env")
        print("Astuce: créez le token sur https://discord.com/developers/applications")
    except ValueError as e:
        _log_error(f"Erreur de configuration: {e}")
        print("Astuce: vérifiez que CHANNEL_ID est un nombre valide")
    except Exception as e:
        _log_error(f"Erreur critique au démarrage: {e}")
        print("\nVariables requises:")
        print("   • DISCORD_BOT_TOKEN (token du bot Discord)")
        print("   • CHANNEL_ID (ID numérique du canal Discord)")
