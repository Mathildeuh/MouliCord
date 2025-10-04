import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from epitech_api import EpitechAPI
from token_refresher import auto_refresh_token

# Charger les variables d'environnement
load_dotenv()

def validate_environment():
    """Valide que toutes les variables d'environnement nécessaires sont présentes"""
    required_vars = {
        'DISCORD_BOT_TOKEN': 'Token du bot Discord',
        'EPITECH_API_TOKEN': 'Token Bearer de l\'API Epitech', 
        'CHANNEL_ID': 'ID du canal Discord'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value.strip() == '':
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print("❌ Variables d'environnement manquantes:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\n💡 Créez un fichier .env avec:")
        print("   DISCORD_BOT_TOKEN=your_bot_token")
        print("   EPITECH_API_TOKEN=your_bearer_token")  
        print("   CHANNEL_ID=your_channel_id")
        print("\n📁 Exemple disponible dans .env.example")
        return False
    return True

# Vérifier les variables d'environnement au démarrage
if not validate_environment():
    exit(1)

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Initialisation sécurisée avec les variables validées
epitech_api = EpitechAPI(os.getenv('EPITECH_API_TOKEN', ''), "results_history.json")
channel_id = int(os.getenv('CHANNEL_ID', '0'))


class MouliCordBot:
    """Bot Discord pour les résultats de la moulinette Epitech - Version Slash Commands uniquement"""
    
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
            date = result.get("date", "")
            
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
            
            # Créer l'embed de notification
            embed = discord.Embed(
                title=f"{emoji} Nouvelle Moulinette - {project_name}",
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
            
            # Informations supplémentaires
            if project_slug:
                embed.add_field(
                    name="🔗 Projet",
                    value=f"`{project_slug}`",
                    inline=True
                )
            
            embed.set_footer(text="MouliCord v2.0 • Surveillance automatique")
            
            # Envoyer la notification avec @everyone pour les nouveaux résultats
            message = f"@everyone 🚨 **NOUVEAU RÉSULTAT DE MOULINETTE !**"
            
            await self.send_to_channel(message, embed)
            print(f"📨 Notification envoyée pour: {project_name} ({percentage}%)")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de la notification: {e}")


moulibot = MouliCordBot()


@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    print(f'{bot.user} est connecté à Discord!')
    print(f'Canal configuré: {channel_id}')
    
    # Actualiser le token au démarrage (optionnel si SKIP_TOKEN_REFRESH=true)
    if not os.getenv('SKIP_TOKEN_REFRESH', '').lower() == 'true':
        print("🔄 Actualisation du token au démarrage...")
        try:
            auto_refresh_token(headless=True, update_env=True)
        except Exception as e:
            print(f"⚠️ Erreur lors de l'actualisation du token: {e}")
    else:
        print("⏭️ Actualisation du token ignorée (SKIP_TOKEN_REFRESH=true)")
    
    # Charger les Slash Commands
    try:
        await bot.load_extension('slash_commands')
        print('✅ Slash Commands chargés')
    except Exception as e:
        print(f'❌ Erreur lors du chargement des Slash Commands: {e}')
    
    # Synchroniser les commandes avec Discord
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} Slash Commands synchronisés avec Discord')
    except Exception as e:
        print(f'❌ Erreur lors de la synchronisation: {e}')
    
    # Vérification immédiate au démarrage pour les nouveaux résultats
    try:
        print("🔍 Vérification des nouveaux résultats au démarrage...")
        new_results_at_startup = epitech_api.get_new_results(2025)
        
        if new_results_at_startup:
            print(f"🆕 {len(new_results_at_startup)} nouveaux résultats détectés au démarrage !")
            for result in new_results_at_startup:
                await moulibot.send_moulinette_notification(result)
        else:
            print("✅ Aucun nouveau résultat au démarrage")
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification au démarrage: {e}")
    
    # Démarrer la vérification automatique périodique
    check_new_results.start()


@tasks.loop(minutes=5)
async def check_new_results():
    """Tâche de vérification automatique des nouveaux résultats"""
    try:
        print(f"🔍 Vérification automatique - {datetime.now().strftime('%H:%M:%S')}")
        
        # Vérifier les nouveaux résultats
        new_results = epitech_api.get_new_results(2025)
        
        if new_results:
            print(f"🆕 {len(new_results)} nouveaux résultats détectés !")
            
            # Envoyer une notification pour chaque nouveau résultat
            for result in new_results:
                await moulibot.send_moulinette_notification(result)
                
        else:
            print("📊 Aucun nouveau résultat détecté")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification automatique: {e}")


@check_new_results.before_loop
async def before_check_new_results():
    """Attendre que le bot soit prêt avant de commencer la vérification"""
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
        # Récupérer le premier résultat pour test
        results = epitech_api.get_moulinette_results(2025)
        
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
        
        new_results = epitech_api.get_new_results(2025)
        
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
        print("🚀 Démarrage de MouliCord v2.0...")
        
        # Vérification finale avant démarrage
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        if not discord_token:
            print("❌ DISCORD_BOT_TOKEN manquant dans le fichier .env")
            exit(1)
            
        print(f"✅ Configuration validée")
        print(f"📡 Canal configuré: {channel_id}")
        api_token = os.getenv('EPITECH_API_TOKEN')
        if api_token and len(api_token) > 20:
            print(f"🔑 Token API: {api_token[:20]}...")
        else:
            print(f"🔑 Token API: {api_token}")
        
        bot.run(discord_token)
        
    except discord.LoginFailure:
        print("❌ Token Discord invalide! Vérifiez DISCORD_BOT_TOKEN dans .env")
        print("💡 Le token doit venir de https://discord.com/developers/applications")
    except ValueError as e:
        print(f"❌ Erreur de configuration: {e}")
        print("💡 Vérifiez que CHANNEL_ID est un nombre valide")
    except Exception as e:
        print(f"❌ Erreur critique au démarrage: {e}")
        print("💡 Vérifiez votre fichier .env et les tokens")
        print("\n📋 Variables requises:")
        print("   • DISCORD_BOT_TOKEN (token du bot Discord)")
        print("   • EPITECH_API_TOKEN (token Bearer API Epitech)")  
        print("   • CHANNEL_ID (ID numérique du canal Discord)")