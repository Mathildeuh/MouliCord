import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from epitech_api import EpitechAPI

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialisation de l'API Epitech avec stockage JSON
epitech_api = EpitechAPI(os.getenv('EPITECH_API_TOKEN'), "results_history.json")
channel_id = int(os.getenv('CHANNEL_ID'))


class MouliCordBot:
    """Bot Discord pour les résultats de la moulinette Epitech"""
    
    def __init__(self):
        print("🕒 Surveillance initialisée avec stockage JSON")
    
    async def send_to_channel(self, message: str, embed: discord.Embed = None):
        """Envoie un message dans le canal configuré"""
        channel = bot.get_channel(channel_id)
        if channel:
            if embed:
                await channel.send(message, embed=embed)
            else:
                await channel.send(message)
        else:
            print(f"Canal {channel_id} non trouvé")


moulibot = MouliCordBot()


@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    print(f'{bot.user} est connecté à Discord!')
    print(f'Canal configuré: {channel_id}')
    
    # Démarrer la vérification automatique
    check_new_results.start()


@bot.command(name='mouli')
async def get_moulinette_results(ctx, limit: int = 5):
    """
    Affiche les derniers résultats de la moulinette
    
    Usage: !mouli [nombre_de_résultats]
    """
    try:
        results = epitech_api.get_latest_results(limit)
        
        if not results:
            await ctx.send("❌ Aucun résultat trouvé ou erreur lors de la récupération.")
            return
        
        embed = discord.Embed(
            title="🏫 Résultats de la Moulinette Epitech",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for i, result in enumerate(results, 1):
            summary = epitech_api.format_project_summary(result)
            embed.add_field(
                name=f"#{i} - {result.get('project', {}).get('name', 'Projet inconnu')}",
                value=summary[:1024],  # Limite Discord pour les fields
                inline=False
            )
        
        embed.set_footer(text="MouliCord Bot")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la récupération des résultats: {str(e)}")


@bot.command(name='details')
async def get_detailed_results(ctx, run_id: int):
    """
    Affiche les détails d'un test spécifique
    
    Usage: !details <run_id>
    """
    try:
        details = epitech_api.get_detailed_results(run_id)
        
        if not details:
            await ctx.send(f"❌ Impossible de récupérer les détails du test {run_id}")
            return
        
        instance = details.get("instance", {})
        skills = details.get("skills", [])
        external_items = details.get("externalItems", [])
        
        embed = discord.Embed(
            title=f"📋 Détails du Test #{run_id}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        # Informations générales
        embed.add_field(
            name="📚 Projet",
            value=f"{instance.get('projectName', 'N/A')} ({instance.get('moduleCode', 'N/A')})",
            inline=True
        )
        
        embed.add_field(
            name="📅 Date",
            value=details.get("date", "N/A"),
            inline=True
        )
        
        embed.add_field(
            name="🏛️ Campus",
            value=f"{instance.get('city', 'N/A')} - {instance.get('year', 'N/A')}",
            inline=True
        )
        
        # Résumé des compétences
        if skills:
            skills_summary = ""
            for skill in skills[:10]:  # Limiter à 10 pour éviter les messages trop longs
                skill_data = skill.get("BreakdownSkillReport", {})
                name = skill_data.get("name", "N/A")
                breakdown = skill_data.get("breakdown", {})
                passed = breakdown.get("passed", 0)
                count = breakdown.get("count", 0)
                status = "✅" if passed == count else "❌"
                skills_summary += f"{status} {name}: {passed}/{count}\n"
            
            if skills_summary:
                embed.add_field(
                    name="🎯 Compétences",
                    value=skills_summary[:1024],
                    inline=False
                )
        
        # Traces/logs si disponibles
        for item in external_items:
            if item.get("type") == "trace-pool" and item.get("comment"):
                trace = item.get("comment", "")[:1000]  # Limiter la longueur
                embed.add_field(
                    name="🔍 Traces d'exécution",
                    value=f"```{trace}...```" if len(trace) >= 1000 else f"```{trace}```",
                    inline=False
                )
                break
        
        embed.set_footer(text="MouliCord Bot")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Erreur lors de la récupération des détails: {str(e)}")


@bot.command(name='watch')
async def toggle_watch_mode(ctx):
    """Active/désactive la surveillance automatique des nouveaux résultats"""
    if check_new_results.is_running():
        check_new_results.stop()
        await ctx.send("🔴 Surveillance automatique désactivée")
    else:
        check_new_results.start()
        stats = epitech_api.get_storage_stats()
        await ctx.send(f"🟢 Surveillance automatique activée\n� Stockage: {stats['total_results']} résultats\n⏰ Prochaine vérification dans 5 minutes")


@bot.command(name='status')
async def watch_status(ctx):
    """Affiche le statut de la surveillance automatique"""
    is_running = check_new_results.is_running()
    status = "🟢 Activée" if is_running else "🔴 Désactivée"
    
    # Récupérer les statistiques du stockage
    stats = epitech_api.get_storage_stats()
    
    embed = discord.Embed(
        title="📊 Statut de la surveillance",
        color=discord.Color.green() if is_running else discord.Color.red()
    )
    
    embed.add_field(name="Surveillance automatique", value=status, inline=True)
    embed.add_field(name="Résultats stockés", value=f"{stats['total_results']}", inline=True)
    embed.add_field(name="Dernière mise à jour", value=stats.get('last_update', 'Jamais')[:16], inline=True)
    
    if is_running:
        next_run = datetime.now(timezone.utc) + timedelta(minutes=5)
        embed.add_field(name="Prochaine vérification", value=next_run.strftime("%d/%m/%Y à %H:%M UTC"), inline=True)
    
    if stats.get('date_range') != 'N/A':
        embed.add_field(name="Période couverte", value=stats['date_range'][:50], inline=False)
    
    embed.set_footer(text="MouliCord Bot - Surveillance avec stockage JSON")
    await ctx.send(embed=embed)


@bot.command(name='check_now')
async def manual_check(ctx):
    """Force une vérification immédiate des nouveaux résultats"""
    await ctx.send("🔍 Vérification manuelle en cours...")
    await check_new_results()


@bot.command(name='stats')
async def storage_stats(ctx):
    """Affiche des statistiques détaillées sur le stockage"""
    stats = epitech_api.get_storage_stats()
    
    embed = discord.Embed(
        title="📈 Statistiques de stockage",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📊 Résultats total",
        value=f"{stats['total_results']} résultats stockés",
        inline=True
    )
    
    embed.add_field(
        name="🕒 Dernière mise à jour",
        value=stats.get('last_update', 'Jamais')[:16],
        inline=True
    )
    
    if stats.get('date_range') != 'N/A':
        embed.add_field(
            name="📅 Période couverte",
            value=stats['date_range'],
            inline=False
        )
    
    # Top 5 des projets
    projects = stats.get('projects', {})
    if projects:
        top_projects = list(projects.items())[:5]
        projects_text = "\n".join([f"{name}: {count} résultats" for name, count in top_projects])
        embed.add_field(
            name="🏆 Top 5 des projets",
            value=projects_text[:1024],
            inline=False
        )
    
    embed.set_footer(text="MouliCord Bot - Stockage JSON")
    await ctx.send(embed=embed)


@bot.command(name='backup')
async def create_backup(ctx):
    """Crée une sauvegarde du stockage"""
    backup_file = epitech_api.backup_storage()
    if backup_file:
        await ctx.send(f"💾 Sauvegarde créée avec succès : `{backup_file}`")
    else:
        await ctx.send("❌ Erreur lors de la création de la sauvegarde")


@bot.command(name='clear_storage')
async def clear_storage_command(ctx):
    """Vide le stockage (commande d'administration)"""
    # Simple protection - peut être améliorée avec des rôles Discord
    await ctx.send("⚠️ Cette commande va supprimer tout l'historique stocké. Tapez `CONFIRMER` pour continuer.")
    
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel
    
    try:
        confirmation = await bot.wait_for('message', check=check, timeout=30)
        if confirmation.content == "CONFIRMER":
            epitech_api.clear_storage()
            await ctx.send("🗑️ Stockage vidé avec succès")
        else:
            await ctx.send("❌ Opération annulée")
    except:
        await ctx.send("⏰ Délai d'attente dépassé - opération annulée")


@tasks.loop(minutes=5)
async def check_new_results():
    """Vérifie périodiquement s'il y a de nouveaux résultats"""
    try:
        print("🔍 Vérification des nouveaux résultats...")
        
        # Utiliser la nouvelle méthode qui compare avec le JSON
        new_results = epitech_api.get_new_results(2025)
        
        if new_results:
            print(f"🎉 {len(new_results)} nouveau(x) résultat(s) détecté(s)")
            
            # Trier les nouveaux résultats par date (du plus ancien au plus récent)
            new_results.sort(key=lambda x: x.get("date", ""))
            
            for result in new_results:
                project_name = result.get("project", {}).get("name", "Projet inconnu")
                
                # Parser la date pour l'embed
                date_str = result.get("date", "")
                result_date = datetime.now(timezone.utc)
                if date_str:
                    result_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                
                embed = discord.Embed(
                    title="🚨 Nouveau résultat de moulinette !",
                    description=f"Un nouveau résultat est disponible pour **{project_name}**",
                    color=discord.Color.orange(),
                    timestamp=result_date
                )
                
                summary = epitech_api.format_project_summary(result)
                embed.add_field(name="Résumé", value=summary[:1024], inline=False)
                
                run_id = result.get("results", {}).get("testRunId")
                if run_id:
                    embed.add_field(
                        name="Plus de détails",
                        value=f"Utilisez `!details {run_id}` pour voir les détails complets",
                        inline=False
                    )
                
                embed.set_footer(text="MouliCord Bot - Surveillance automatique avec stockage JSON")
                
                await moulibot.send_to_channel("", embed)
                print(f"📢 Nouveau résultat notifié: {project_name} ({result_date})")
        else:
            print("📭 Aucun nouveau résultat détecté")
                
    except Exception as e:
        print(f"❌ Erreur lors de la vérification automatique: {e}")
        import traceback
        traceback.print_exc()


@bot.command(name='help_mouli')
async def help_command(ctx):
    """Affiche l'aide pour MouliCord"""
    embed = discord.Embed(
        title="📖 Aide MouliCord",
        description="Bot Discord pour consulter les résultats de la moulinette Epitech",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="!mouli [nombre]",
        value="Affiche les derniers résultats (défaut: 5)",
        inline=False
    )
    
    embed.add_field(
        name="!details <run_id>",
        value="Affiche les détails d'un test spécifique",
        inline=False
    )
    
    embed.add_field(
        name="!watch",
        value="Active/désactive la surveillance automatique",
        inline=False
    )
    
    embed.add_field(
        name="!status",
        value="Affiche le statut de la surveillance",
        inline=False
    )
    
    embed.add_field(
        name="!check_now",
        value="Force une vérification immédiate",
        inline=False
    )
    
    embed.add_field(
        name="!stats",
        value="Affiche les statistiques du stockage",
        inline=False
    )
    
    embed.add_field(
        name="!backup",
        value="Crée une sauvegarde du stockage",
        inline=False
    )
    
    embed.add_field(
        name="!clear_storage",
        value="Vide le stockage (admin)",
        inline=False
    )
    
    embed.add_field(
        name="!help_mouli",
        value="Affiche cette aide",
        inline=False
    )
    
    embed.set_footer(text="MouliCord Bot v1.0")
    await ctx.send(embed=embed)


if __name__ == "__main__":
    # Vérification des variables d'environnement
    discord_token = os.getenv('DISCORD_TOKEN')
    epitech_token = os.getenv('EPITECH_API_TOKEN')
    
    if not discord_token:
        print("❌ DISCORD_TOKEN manquant dans le fichier .env")
        exit(1)
    
    if not epitech_token:
        print("❌ EPITECH_API_TOKEN manquant dans le fichier .env")
        exit(1)
    
    if not channel_id:
        print("❌ CHANNEL_ID manquant dans le fichier .env")
        exit(1)
    
    print("🚀 Démarrage de MouliCord...")
    bot.run(discord_token)