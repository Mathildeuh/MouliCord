import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from typing import Optional
from epitech_api import EpitechAPI
from token_refresher import auto_refresh_token

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
    auto_refresh_token(headless=True, update_env=True)
    async def send_to_channel(self, message: str, embed: discord.Embed = None):
        """Envoie un message dans le canal configuré"""
        channel = bot.get_channel(channel_id)
        if channel and hasattr(channel, 'send'):
            if embed:
                # Permettre les mentions @everyone
                await channel.send(message, embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
            else:
                await channel.send(message, allowed_mentions=discord.AllowedMentions(everyone=True))
        else:
            print(f"Canal {channel_id} non trouvé ou non compatible")


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
        
        # Calculer les statistiques globales
        total_projects = len(results)
        total_tests = 0
        total_passed = 0
        
        for result in results:
            skills = result.get("results", {}).get("skills", {})
            total_tests += sum(skill.get("count", 0) for skill in skills.values())
            total_passed += sum(skill.get("passed", 0) for skill in skills.values())
        
        global_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        global_progress = epitech_api._generate_progress_bar(total_passed, total_tests, 15)
        
        embed = discord.Embed(
            title="🏫 Résultats de la Moulinette Epitech",
            description=f"📊 **Global:** {total_passed}/{total_tests} tests ({global_rate:.1f}%)\n📈 {global_progress}",
            color=discord.Color.green() if global_rate >= 70 else discord.Color.orange() if global_rate >= 50 else discord.Color.red(),
            timestamp=datetime.now()
        )
        
        for i, result in enumerate(results, 1):
            summary = epitech_api.format_project_summary(result)
            project_name = result.get('project', {}).get('name', 'Projet inconnu')
            
            # Calculer le taux de réussite pour choisir l'emoji
            skills = result.get("results", {}).get("skills", {})
            project_total = sum(skill.get("count", 0) for skill in skills.values())
            project_passed = sum(skill.get("passed", 0) for skill in skills.values())
            project_rate = (project_passed / project_total * 100) if project_total > 0 else 0
            
            if project_rate >= 90:
                emoji = "🟢"
            elif project_rate >= 70:
                emoji = "🟡"
            elif project_rate >= 50:
                emoji = "🟠"
            else:
                emoji = "🔴"
            
            embed.add_field(
                name=f"{emoji} #{i} - {project_name}",
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


@bot.command(name='token')
async def check_token(ctx):
    """Vérifie les informations du token Epitech et sa date d'expiration"""
    token_info = epitech_api.get_token_info()
    
    if "error" in token_info:
        embed = discord.Embed(
            title="❌ Erreur Token",
            description=token_info["error"],
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Déterminer la couleur selon l'état du token
    if token_info["is_expired"]:
        color = discord.Color.red()
        status_emoji = "🔴"
        status_text = "Expiré"
    elif token_info["days_remaining"] <= 1:
        color = discord.Color.orange()
        status_emoji = "🟠"
        status_text = "Expire bientôt"
    elif token_info["days_remaining"] <= 7:
        color = discord.Color.yellow()
        status_emoji = "🟡"
        status_text = "Expire cette semaine"
    else:
        color = discord.Color.green()
        status_emoji = "🟢"
        status_text = "Valide"
    
    embed = discord.Embed(
        title=f"{status_emoji} Token Epitech - {status_text}",
        color=color
    )
    
    embed.add_field(
        name="📅 Date d'expiration",
        value=token_info["expires_at"],
        inline=True
    )
    
    if not token_info["is_expired"]:
        time_parts = []
        
        if token_info["days_remaining"] > 0:
            time_parts.append(f"{token_info['days_remaining']} jours")
        
        if token_info["hours_remaining"] > 0:
            time_parts.append(f"{token_info['hours_remaining']} heures")
        
        if token_info["minutes_remaining"] > 0:
            time_parts.append(f"{token_info['minutes_remaining']} minutes")
        
        if token_info["seconds_remaining"] > 0 and len(time_parts) < 2:
            time_parts.append(f"{token_info['seconds_remaining']} secondes")
        
        time_display = ", ".join(time_parts) if time_parts else "Moins d'une seconde"
        
        embed.add_field(
            name="⏰ Temps restant",
            value=time_display,
            inline=True
        )
    
    if "issued_at" in token_info:
        embed.add_field(
            name="🔧 Émis le",
            value=token_info["issued_at"],
            inline=True
        )
    
    if "subject" in token_info:
        embed.add_field(
            name="👤 Utilisateur",
            value=token_info["subject"],
            inline=True
        )
    
    # Ajouter des conseils selon l'état
    if token_info["is_expired"]:
        embed.add_field(
            name="⚠️ Action requise",
            value="Le token a expiré. Veuillez le renouveler et mettre à jour la configuration.",
            inline=False
        )
    elif token_info["days_remaining"] <= 7:
        embed.add_field(
            name="💡 Conseil",
            value="Le token expire bientôt. Pensez à le renouveler prochainement.",
            inline=False
        )
    
    await ctx.send(embed=embed)


@bot.command(name='refresh_token')
async def refresh_token_command(ctx, headless: bool = True):
    """Récupère automatiquement un nouveau token via Selenium"""
    
    # Message de début
    start_embed = discord.Embed(
        title="🔄 Récupération du token en cours...",
        description="Lancement de l'automatisation Selenium avec persistance Office\nCela peut prendre 30-60 secondes.",
        color=discord.Color.blue()
    )
    start_embed.add_field(
        name="📋 Étapes",
        value="1️⃣ Vérification session Office existante\n2️⃣ Ouverture du navigateur\n3️⃣ Navigation vers myresults.epitest.eu\n4️⃣ Clic sur 'Log In' (si nécessaire)\n5️⃣ Capture du token\n6️⃣ Sauvegarde de la session",
        inline=False
    )
    
    start_embed.add_field(
        name="🔐 Persistance Office Permanente",
        value="Votre session Office est sauvegardée définitivement - plus besoin de re-authentifier !",
        inline=False
    )
    
    if not headless:
        start_embed.add_field(
            name="👀 Mode visible",
            value="Le navigateur va s'ouvrir - vous devrez peut-être vous authentifier manuellement",
            inline=False
        )
    
    message = await ctx.send(embed=start_embed)
    
    try:
        # Lancer la récupération automatique
        result = auto_refresh_token(headless=headless, update_env=True)
        
        if result["success"]:
            # Succès
            success_embed = discord.Embed(
                title="✅ Token récupéré avec succès !",
                color=discord.Color.green()
            )
            
            success_embed.add_field(
                name="🎯 Status",
                value=result["message"],
                inline=False
            )
            
            if result.get("url"):
                success_embed.add_field(
                    name="🔗 URL finale",
                    value=f"`{result['url'][:50]}...`" if len(result['url']) > 50 else f"`{result['url']}`",
                    inline=False
                )
            
            if result.get("env_updated"):
                success_embed.add_field(
                    name="⚙️ Configuration",
                    value="✅ Fichier .env mis à jour automatiquement",
                    inline=False
                )
                
                # Recharger l'API avec le nouveau token
                global epitech_api
                new_token = result["token"]
                epitech_api = EpitechAPI(new_token, "results_history.json")
                
                success_embed.add_field(
                    name="🔄 Rechargement",
                    value="✅ API rechargée avec le nouveau token",
                    inline=False
                )
            
            # Afficher quelques caractères du token (sécurisé)
            token_preview = f"{result['token'][:10]}...{result['token'][-10:]}"
            success_embed.add_field(
                name="🔑 Token (aperçu)",
                value=f"`{token_preview}`",
                inline=False
            )
            
            success_embed.add_field(
                name="💡 Conseil",
                value="Utilisez `!token` pour vérifier l'expiration du nouveau token",
                inline=False
            )
            
            await message.edit(embed=success_embed)
            
        else:
            # Erreur
            error_embed = discord.Embed(
                title="❌ Échec de la récupération du token",
                color=discord.Color.red()
            )
            
            error_embed.add_field(
                name="🚫 Erreur",
                value=result.get("error", "Erreur inconnue"),
                inline=False
            )
            
            error_embed.add_field(
                name="📝 Message",
                value=result.get("message", "Aucun détail disponible"),
                inline=False
            )
            
            if result.get("url"):
                error_embed.add_field(
                    name="🔗 URL au moment de l'erreur",
                    value=f"`{result['url']}`",
                    inline=False
                )
            
            error_embed.add_field(
                name="🛠️ Solutions possibles",
                value="• Vérifiez votre connexion internet\n• Essayez `!refresh_token False` (mode visible)\n• Vérifiez que Chrome/Chromium est installé\n• L'authentification peut nécessiter une interaction manuelle",
                inline=False
            )
            
            await message.edit(embed=error_embed)
            
    except Exception as e:
        # Erreur critique
        critical_embed = discord.Embed(
            title="💥 Erreur critique",
            description=f"Une erreur inattendue s'est produite:\n```{str(e)}```",
            color=discord.Color.dark_red()
        )
        
        critical_embed.add_field(
            name="🔧 Vérifications",
            value="• Selenium est-il installé ? (`pip install selenium webdriver-manager`)\n• Chrome/Chromium est-il disponible ?\n• Permissions d'écriture sur le fichier .env ?",
            inline=False
        )
        
        await message.edit(embed=critical_embed)


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
                
                # Ajouter mention @everyone pour notifier tout le monde
                mention_message = "@everyone"
                await moulibot.send_to_channel(mention_message, embed)
                print(f"📢 Nouveau résultat notifié avec @everyone: {project_name} ({result_date})")
        else:
            print("📭 Aucun nouveau résultat détecté")
                
    except Exception as e:
        auto_refresh_token(headless=False, update_env=True)
        print(f"🔄 Refresh du token en cours !")
        import traceback
        traceback.print_exc()


@bot.command(name='history')
async def history_command(ctx, *, project_id: Optional[str] = None):
    """
    Affiche l'historique complet d'un projet spécifique
    Usage: !history G-CPE-100/cpoolday09
    """
    if not project_id:
        embed = discord.Embed(
            title="❌ Erreur",
            description="Veuillez spécifier un projet au format `module/projet`\n\n**Exemple:**\n`!history G-CPE-100/cpoolday09`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Message de chargement
    loading_embed = discord.Embed(
        title="🔍 Récupération de l'historique...",
        description=f"Recherche des résultats pour **{project_id}**",
        color=discord.Color.orange()
    )
    message = await ctx.send(embed=loading_embed)
    
    try:
        # Récupérer l'historique du projet
        history = epitech_api.get_project_history(project_id, 2025)
        
        if not history:
            error_embed = discord.Embed(
                title="❌ Aucun résultat",
                description=f"Aucun historique trouvé pour **{project_id}**\n\nVérifiez l'orthographe ou essayez un autre projet.",
                color=discord.Color.red()
            )
            await message.edit(embed=error_embed)
            return
        
        # Informations du projet (du premier résultat)
        project_info = history[0].get("project", {})
        project_name = project_info.get("name", "Projet inconnu")
        module_code = project_info.get("module", {}).get("code", "Module inconnu")
        
        # Embed principal avec résumé
        embed = discord.Embed(
            title=f"📊 Historique - {project_name}",
            description=f"**Module:** {module_code}\n**Total des passages:** {len(history)}",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Analyser l'évolution
        if len(history) >= 2:
            latest = history[0]
            oldest = history[-1]
            
            latest_skills = latest.get("results", {}).get("skills", {})
            oldest_skills = oldest.get("results", {}).get("skills", {})
            
            latest_passed = sum(skill.get("passed", 0) for skill in latest_skills.values())
            latest_total = sum(skill.get("count", 0) for skill in latest_skills.values())
            
            oldest_passed = sum(skill.get("passed", 0) for skill in oldest_skills.values())
            oldest_total = sum(skill.get("count", 0) for skill in oldest_skills.values())
            
            if latest_total > 0 and oldest_total > 0:
                latest_percent = (latest_passed / latest_total) * 100
                oldest_percent = (oldest_passed / oldest_total) * 100
                evolution = latest_percent - oldest_percent
                
                evolution_icon = "📈" if evolution > 0 else "📉" if evolution < 0 else "➡️"
                embed.add_field(
                    name="📊 Évolution",
                    value=f"{evolution_icon} {evolution:+.1f}% ({oldest_percent:.1f}% → {latest_percent:.1f}%)",
                    inline=True
                )
        
        # Détails des passages (limités aux 10 derniers pour éviter la saturation)
        history_display = history[:10]  # Limiter à 10 pour éviter de dépasser la limite Discord
        
        history_text = ""
        for i, entry in enumerate(history_display):
            date_str = entry.get("date", "")
            test_run_id = entry.get("results", {}).get("testRunId", "N/A")
            
            # Parser la date
            try:
                entry_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_formatted = entry_date.strftime("%d/%m/%Y %H:%M")
            except:
                date_formatted = "Date inconnue"
            
            # Calculer le score
            skills = entry.get("results", {}).get("skills", {})
            passed = sum(skill.get("passed", 0) for skill in skills.values())
            total = sum(skill.get("count", 0) for skill in skills.values())
            
            if total > 0:
                score_percent = (passed / total) * 100
                progress_bar = epitech_api._generate_progress_bar(passed, total, 10)
                
                # Icône selon le score
                if score_percent == 100:
                    icon = "🏆"
                elif score_percent >= 80:
                    icon = "✅"
                elif score_percent >= 50:
                    icon = "⚠️"
                else:
                    icon = "❌"
                
                history_text += f"{icon} **{date_formatted}** - {passed}/{total} ({score_percent:.1f}%)\n"
                history_text += f"   {progress_bar} `ID: {test_run_id}`\n\n"
            else:
                history_text += f"⭕ **{date_formatted}** - Aucun test\n   `ID: {test_run_id}`\n\n"
        
        # Ajouter l'historique à l'embed
        embed.add_field(
            name=f"📝 Historique (10 derniers sur {len(history)})",
            value=history_text[:1024] if history_text else "Aucun détail disponible",
            inline=False
        )
        
        # Informations sur le dernier passage
        if history:
            latest_entry = history[0]
            latest_date = latest_entry.get("date", "")
            try:
                latest_dt = datetime.fromisoformat(latest_date.replace('Z', '+00:00'))
                time_ago = datetime.now(timezone.utc) - latest_dt
                
                if time_ago.days > 0:
                    time_str = f"il y a {time_ago.days} jour{'s' if time_ago.days > 1 else ''}"
                else:
                    hours = time_ago.seconds // 3600
                    minutes = (time_ago.seconds % 3600) // 60
                    if hours > 0:
                        time_str = f"il y a {hours}h{minutes:02d}m"
                    else:
                        time_str = f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
                
                embed.add_field(
                    name="⏰ Dernier passage",
                    value=time_str,
                    inline=True
                )
            except:
                pass
        
        # Note pour voir plus de détails
        if len(history) > 10:
            embed.add_field(
                name="ℹ️ Info",
                value=f"Seuls les 10 derniers passages sont affichés.\nUtilisez `!details <ID>` pour voir un passage spécifique.",
                inline=False
            )
        
        embed.set_footer(text="MouliCord Bot - Historique projet")
        await message.edit(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Erreur",
            description=f"Erreur lors de la récupération de l'historique:\n```{str(e)}```",
            color=discord.Color.red()
        )
        await message.edit(embed=error_embed)
        print(f"Erreur dans history_command: {e}")
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
        name="!token",
        value="Vérifie l'expiration du token Epitech",
        inline=False
    )
    
    embed.add_field(
        name="!refresh_token [headless]",
        value="Récupère automatiquement un nouveau token via Selenium (avec persistance Office)",
        inline=False
    )
    
    embed.add_field(
        name="!history <module/projet>",
        value="Affiche l'historique complet d'un projet (ex: G-CPE-100/cpoolday09)",
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
