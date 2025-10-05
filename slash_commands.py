import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import json
import base64
from epitech_api import EpitechAPI
from token_refresher import auto_refresh_token
import os


class ProjectDetailsView(discord.ui.View):
    """Vue avec menu déroulant pour sélectionner un projet et afficher ses détails"""
    
    def __init__(self, results: List[dict], epitech_api):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.results = results
        self.epitech_api = epitech_api
        
        # Créer les options pour le menu déroulant
        options = []
        for result in results[:25]:  # Discord limite à 25 options
            project = result.get("project", {})
            name = project.get("name", "Projet inconnu")
            slug = project.get("slug", "unknown")
            
            # Calculer le taux de réussite pour l'aperçu
            skills = result.get("results", {}).get("skills", {})
            total_tests = sum(skill.get("count", 0) for skill in skills.values())
            total_passed = sum(skill.get("passed", 0) for skill in skills.values())
            rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
            
            # Émoji selon le taux de réussite
            emoji = "🟢" if rate >= 70 else "🟡" if rate >= 50 else "🔴"
            
            options.append(discord.SelectOption(
                label=f"{name}",
                description=f"{emoji} {rate:.1f}% - {total_passed}/{total_tests} tests",
                value=slug,
                emoji="🎯"
            ))
        
        # Ajouter le menu déroulant
        self.add_item(ProjectSelect(options, self.results, self.epitech_api))


class ProjectSelect(discord.ui.Select):
    """Menu déroulant pour sélectionner un projet"""
    
    def __init__(self, options: List[discord.SelectOption], results: List[dict], epitech_api):
        super().__init__(
            placeholder="🔍 Choisissez un projet à analyser...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.results = results
        self.epitech_api = epitech_api
    
    async def callback(self, interaction: discord.Interaction):
        """Callback appelé quand un projet est sélectionné"""
        selected_slug = self.values[0]
        
        # Trouver le projet sélectionné
        selected_project = None
        for result in self.results:
            if result.get("project", {}).get("slug") == selected_slug:
                selected_project = result
                break
        
        if not selected_project:
            await interaction.response.send_message("❌ Projet non trouvé", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Créer l'embed détaillé
        project = selected_project.get("project", {})
        skills = selected_project.get("results", {}).get("skills", {})
        name = project.get("name", "Projet inconnu")
        
        total_tests = sum(skill.get("count", 0) for skill in skills.values())
        total_passed = sum(skill.get("passed", 0) for skill in skills.values())
        rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Couleur selon le taux de réussite
        if rate >= 70:
            color = discord.Color.green()
        elif rate >= 50:
            color = discord.Color.orange()
        else:
            color = discord.Color.red()
        
        progress = self.epitech_api._generate_progress_bar(total_passed, total_tests, 15)
        
        embed = discord.Embed(
            title=f"🔍 Détails - {name}",
            description=f"📊 **{total_passed}/{total_tests} tests** ({rate:.1f}%)\n📈 {progress}",
            color=color,
            timestamp=datetime.now()
        )
        
        # Ajouter les détails par compétence
        for skill_name, skill_data in skills.items():
            count = skill_data.get("count", 0)
            passed = skill_data.get("passed", 0)
            skill_rate = (passed / count * 100) if count > 0 else 0
            skill_progress = self.epitech_api._generate_progress_bar(passed, count, 8)
            
            embed.add_field(
                name=f"🎯 {skill_name}",
                value=f"{passed}/{count} ({skill_rate:.1f}%)\n{skill_progress}",
                inline=True
            )
        
        # Ajouter des informations supplémentaires
        date_str = selected_project.get("date", "")
        if date_str:
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                embed.add_field(
                    name="📅 Date de passage",
                    value=f"<t:{int(date_obj.timestamp())}:F>",
                    inline=False
                )
            except:
                pass
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class MouliCordSlashCommands(commands.Cog):
    """Slash Commands modernes pour MouliCord avec composants interactifs"""
    
    def __init__(self, bot: commands.Bot, epitech_api: EpitechAPI):
        self.bot = bot
        self.epitech_api = epitech_api
        channel_id_str = os.getenv('CHANNEL_ID')
        self.channel_id = int(channel_id_str) if channel_id_str else 0

    @app_commands.command(name="mouli", description="📊 Affiche les derniers résultats de la moulinette")
    @app_commands.describe(
        nombre="Nombre de résultats à afficher (1-20, défaut: 5)"
    )
    async def mouli_slash(self, interaction: discord.Interaction, nombre: Optional[int] = 5):
        """Slash command pour afficher les résultats de moulinette"""
        
        # Validation
        if nombre is None or nombre < 1 or nombre > 20:
            nombre = 5
        
        await interaction.response.defer(thinking=True)
        
        try:
            results = self.epitech_api.get_moulinette_results(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucun résultat",
                    description="Impossible de récupérer les résultats de la moulinette",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Limiter les résultats
            limited_results = results[:nombre]
            
            # Créer l'embed principal avec les statistiques globales
            # Créer l'embed manuellement pour les listes de résultats
            total_projects = len(limited_results)
            total_tests = sum(
                sum(skill.get("count", 0) for skill in result.get("results", {}).get("skills", {}).values())
                for result in limited_results
            )
            total_passed = sum(
                sum(skill.get("passed", 0) for skill in result.get("results", {}).get("skills", {}).values())
                for result in limited_results
            )
            
            global_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
            global_progress = self.epitech_api._generate_progress_bar(total_passed, total_tests, 15)
            
            embed = discord.Embed(
                title=f"🏫 Résultats Moulinette ({nombre} derniers)",
                description=f"📊 **Global:** {total_passed}/{total_tests} tests ({global_rate:.1f}%)\n📈 {global_progress}",
                color=discord.Color.green() if global_rate >= 70 else discord.Color.orange() if global_rate >= 50 else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            # Ajouter chaque projet individuellement
            for result in limited_results[:10]:  # Limiter à 10 pour éviter la limite Discord
                module = result.get("module", "Projet inconnu")
                skills = result.get("results", {}).get("skills", {})
                tests = sum(skill.get("count", 0) for skill in skills.values())
                passed = sum(skill.get("passed", 0) for skill in skills.values())
                rate = (passed / tests * 100) if tests > 0 else 0
                progress = self.epitech_api._generate_progress_bar(passed, tests, 8)
                
                embed.add_field(
                    name=f"📁 {module}",
                    value=f"📊 {passed}/{tests} ({rate:.1f}%)\n{progress}",
                    inline=True
                )
            
            # Créer une vue avec bouton d'actualisation
            view = MouliResultsView(self.epitech_api, nombre)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur lors de la récupération:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="details", description="🔍 Sélectionne et affiche les détails d'un projet")
    async def details_slash(self, interaction: discord.Interaction):
        """Slash command pour les détails d'un projet avec menu déroulant"""
        await interaction.response.defer(thinking=True)
        
        try:
            results = self.epitech_api.get_moulinette_results(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucun résultat",
                    description="Impossible de récupérer les résultats",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Créer le menu déroulant avec les projets disponibles
            view = ProjectDetailsView(results, self.epitech_api)
            
            embed = discord.Embed(
                title="🔍 Détails de Projet",
                description=f"📊 **{len(results)} projets disponibles**\n\n🎯 Sélectionnez un projet dans le menu déroulant ci-dessous pour voir ses détails complets.",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Instructions",
                value="• Utilisez le menu déroulant pour choisir un projet\n• Les détails s'afficheront automatiquement\n• Seuls les projets avec des résultats sont listés",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur lors de la récupération des détails:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        """Slash command pour les détails d'un projet"""
        await interaction.response.defer(thinking=True)
        
        try:
            results = self.epitech_api.get_moulinette_results(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucun résultat",
                    description="Impossible de récupérer les résultats",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Créer le menu déroulant avec les projets disponibles
            view = ProjectDetailsView(results, self.epitech_api)
            
            # Créer l'embed avec instructions
                embed = discord.Embed(
                    title="❌ Projet non trouvé",
                    description=f"Le projet `{projet}` n'a pas été trouvé dans les résultats récents.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Créer l'embed détaillé manuellement
            skills = project_result.get("results", {}).get("skills", {})
            total_tests = sum(skill.get("count", 0) for skill in skills.values())
            total_passed = sum(skill.get("passed", 0) for skill in skills.values())
            rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
            progress = self.epitech_api._generate_progress_bar(total_passed, total_tests, 15)
            
            embed = discord.Embed(
                title=f"🔍 Détails - {projet}",
                description=f"📊 **{total_passed}/{total_tests} tests** ({rate:.1f}%)\n📈 {progress}",
                color=discord.Color.green() if rate >= 70 else discord.Color.orange() if rate >= 50 else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            # Détails par compétence
            for skill_name, skill_data in skills.items():
                count = skill_data.get("count", 0)
                passed = skill_data.get("passed", 0)
                skill_rate = (passed / count * 100) if count > 0 else 0
                skill_progress = self.epitech_api._generate_progress_bar(passed, count, 8)
                
                embed.add_field(
                    name=f"� {skill_name}",
                    value=f"{passed}/{count} ({skill_rate:.1f}%)\n{skill_progress}",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur lors de la récupération des détails:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="watch", description="🔄 Surveillance automatique des résultats")
    async def watch_slash(self, interaction: discord.Interaction):
        """Slash command pour la surveillance"""
        embed = discord.Embed(
            title="🔄 Surveillance Active",
            description="✅ La surveillance automatique des nouveaux résultats est **toujours active**.\n\n📡 Vérification toutes les 10 minutes\n🔔 Notifications automatiques avec @everyone",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="📊 Affiche le statut du bot et de l'API")
    async def status_slash(self, interaction: discord.Interaction):
        """Slash command pour le statut"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Test de l'API
            results = self.epitech_api.get_moulinette_results(2025)
            api_status = "✅ Connectée" if results else "❌ Erreur"
            
            # Informations sur le token
            token_info = self.epitech_api.check_token_expiration()
            
            embed = discord.Embed(
                title="📊 Statut du Bot MouliCord",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🤖 Bot Discord",
                value="✅ En ligne et fonctionnel",
                inline=True
            )
            
            embed.add_field(
                name="🏫 API Epitech", 
                value=api_status,
                inline=True
            )
            
            embed.add_field(
                name="🔑 Token Status",
                value=token_info,
                inline=False
            )
            
            embed.add_field(
                name="🔄 Surveillance",
                value="✅ Active (5min) - Tokens auto-renouvelés (1h)",
                inline=True
            )
            
            # Statistiques de stockage
            try:
                with open("results_history.json", "r") as f:
                    history = json.load(f)
                    total_entries = len(history)
            except:
                total_entries = 0
                
            embed.add_field(
                name="💾 Stockage JSON",
                value=f"📊 {total_entries} entrées sauvegardées",
                inline=True
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de statut",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="check_now", description="🔄 Force une vérification immédiate des résultats")
    async def check_now_slash(self, interaction: discord.Interaction):
        """Slash command pour vérification immédiate"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Effectuer la vérification
            results = self.epitech_api.get_moulinette_results(2025)
            
            if results:
                embed = discord.Embed(
                    title="✅ Vérification terminée",
                    description=f"🔍 **{len(results)} projets** trouvés dans les résultats actuels",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                # Afficher un aperçu des 3 derniers résultats
                for i, result in enumerate(results[:3]):
                    module = result.get("module", "Inconnu")
                    skills = result.get("results", {}).get("skills", {})
                    total_tests = sum(skill.get("count", 0) for skill in skills.values())
                    total_passed = sum(skill.get("passed", 0) for skill in skills.values())
                    rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
                    
                    embed.add_field(
                        name=f"📁 {module}",
                        value=f"📊 {total_passed}/{total_tests} ({rate:.1f}%)",
                        inline=True
                    )
            else:
                embed = discord.Embed(
                    title="❌ Erreur de vérification",
                    description="Impossible de récupérer les résultats de l'API",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur lors de la vérification",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="📈 Statistiques complètes des résultats")
    async def stats_slash(self, interaction: discord.Interaction):
        """Slash command pour les statistiques"""
        await interaction.response.defer(thinking=True)
        
        try:
            results = self.epitech_api.get_moulinette_results(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucune donnée",
                    description="Impossible de récupérer les statistiques",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Calculs statistiques
            total_projects = len(results)
            total_tests = sum(
                sum(skill.get("count", 0) for skill in result.get("results", {}).get("skills", {}).values())
                for result in results
            )
            total_passed = sum(
                sum(skill.get("passed", 0) for skill in result.get("results", {}).get("skills", {}).values())
                for result in results
            )
            
            global_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
            
            # Répartition par taux de réussite
            def get_project_rate(project):
                skills = project.get("results", {}).get("skills", {})
                tests = sum(skill.get("count", 0) for skill in skills.values())
                passed = sum(skill.get("passed", 0) for skill in skills.values())
                return (passed / tests * 100) if tests > 0 else 0
            
            excellent = sum(1 for result in results if get_project_rate(result) >= 80)
            good = sum(1 for result in results if 60 <= get_project_rate(result) < 80)
            average = sum(1 for result in results if 40 <= get_project_rate(result) < 60)
            poor = sum(1 for result in results if get_project_rate(result) < 40)
            
            # Projets les mieux réussis
            top_projects = sorted(results, key=get_project_rate, reverse=True)[:3]
            
            embed = discord.Embed(
                title="📈 Statistiques Complètes",
                description=f"📊 **Taux de réussite global:** {global_rate:.1f}%",
                color=discord.Color.green() if global_rate >= 70 else discord.Color.orange() if global_rate >= 50 else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎯 Résumé Global",
                value=f"📁 **{total_projects}** projets\n🧪 **{total_tests}** tests\n✅ **{total_passed}** réussis",
                inline=True
            )
            
            embed.add_field(
                name="📊 Répartition",
                value=f"🟢 Excellent (≥80%): **{excellent}**\n🔵 Bon (60-79%): **{good}**\n🟡 Moyen (40-59%): **{average}**\n🔴 Faible (<40%): **{poor}**",
                inline=True
            )
            
            # Top 3 projets
            if top_projects:
                top_text = ""
                for i, project in enumerate(top_projects):
                    module = project.get("module", "Inconnu")
                    rate = get_project_rate(project)
                    medals = ["🥇", "🥈", "🥉"]
                    top_text += f"{medals[i]} `{module}` ({rate:.1f}%)\n"
                
                embed.add_field(
                    name="🏆 Top 3 Projets",
                    value=top_text,
                    inline=False
                )
            
            # Barre de progression globale
            progress_bar = self.epitech_api._generate_progress_bar(total_passed, total_tests, 20)
            embed.add_field(
                name="📈 Progression Globale",
                value=progress_bar,
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur statistiques",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="backup", description="💾 Créer une sauvegarde des résultats")
    async def backup_slash(self, interaction: discord.Interaction):
        """Slash command pour créer un backup"""
        await interaction.response.defer(thinking=True)
        
        try:
            import shutil
            
            # Créer une sauvegarde avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"results_backup_{timestamp}.json"
            
            shutil.copy2("results_history.json", backup_name)
            
            # Statistiques du backup
            try:
                with open("results_history.json", "r") as f:
                    data = json.load(f)
                    entries_count = len(data)
            except:
                entries_count = 0
            
            embed = discord.Embed(
                title="💾 Sauvegarde Créée",
                description=f"✅ Backup créé avec succès !",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📄 Fichier",
                value=f"`{backup_name}`",
                inline=True
            )
            
            embed.add_field(
                name="📊 Contenu",
                value=f"{entries_count} entrées sauvegardées",
                inline=True
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur de sauvegarde",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="clear_storage", description="🗑️ Vider le stockage des résultats")
    async def clear_storage_slash(self, interaction: discord.Interaction):
        """Slash command pour vider le stockage avec confirmation"""
        
        # Message de confirmation initial
        try:
            with open("results_history.json", "r") as f:
                data = json.load(f)
                entries_count = len(data)
        except:
            entries_count = 0
        
        embed = discord.Embed(
            title="⚠️ Confirmation Requise",
            description=f"Êtes-vous sûr de vouloir **supprimer définitivement** toutes les données ?\n\n📊 **{entries_count} entrées** seront perdues !",
            color=discord.Color.orange()
        )
        
        view = ConfirmClearView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="token", description="🔐 Vérifie le token Epitech (durée de vie: 1h)")
    async def token_slash(self, interaction: discord.Interaction):
        """Slash command pour vérifier le token"""
        
        await interaction.response.defer(thinking=True)
        
        try:
            expiration_info = self.epitech_api.check_token_expiration()
            
            embed = discord.Embed(
                title="🔐 Statut du Token",
                description=expiration_info,
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
                
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Impossible de vérifier le token:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="refresh_token", description="🔄 Force le renouvellement du token (1h de validité)")
    async def refresh_token_slash(self, interaction: discord.Interaction):
        """Slash command pour actualiser le token"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Message de début
            embed = discord.Embed(
                title="🔄 Renouvellement du Token",
                description="⏳ Génération d'un nouveau token (valide 1h)...",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Lancer l'actualisation avec Selenium
            success = auto_refresh_token(headless=True, update_env=True)
            
            if success:
                # Vérifier le nouveau token
                new_token_info = self.epitech_api.check_token_expiration()
                
                embed = discord.Embed(
                    title="✅ Token Actualisé",
                    description="🎉 Le token a été actualisé avec succès !",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🔑 Nouveau Token",
                    value=new_token_info,
                    inline=False
                )
                
                embed.add_field(
                    name="🔧 Méthode",
                    value="✅ Selenium + Office persistant",
                    inline=True
                )
                
            else:
                embed = discord.Embed(
                    title="❌ Échec de l'actualisation",
                    description="Impossible d'actualiser le token automatiquement",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="💡 Solution",
                    value="Vérifiez votre connexion Office ou actualisez manuellement",
                    inline=False
                )
            
            # Éditer le message existant
            await interaction.edit_original_response(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur d'actualisation",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="history", description="📈 Analyse l'historique d'un projet avec sélection interactive")
    async def history_slash(self, interaction: discord.Interaction):
        """Slash command pour l'historique avec sélection de projet"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Récupérer tous les résultats pour extraire les projets disponibles
            results = self.epitech_api.get_moulinette_results(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucun résultat",
                    description="Impossible de récupérer les projets disponibles",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Extraire tous les projets uniques avec leurs informations
            projects_map = {}
            for result in results:
                module = result.get("module", "")
                if module and module not in projects_map:
                    project_name = result.get("project_name", module.split("/")[-1] if "/" in module else module)
                    projects_map[module] = {
                        "name": project_name,
                        "module": module
                    }
            
            if not projects_map:
                embed = discord.Embed(
                    title="❌ Aucun projet",
                    description="Aucun projet trouvé dans les résultats",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Créer l'embed de sélection
            embed = discord.Embed(
                title="📋 Sélection du Projet",
                description=f"**Choisissez un projet** pour analyser son historique complet.\n\n📊 **{len(projects_map)} projets** disponibles",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📈 Fonctionnalités",
                value="• Évolution des notes dans le temps\n• Comparaison entre passages\n• Navigation interactive",
                inline=True
            )
            
            embed.add_field(
                name="🔍 Analyse",
                value="• Détection des améliorations\n• Historique des erreurs\n• Progression détaillée",
                inline=True
            )
            
            # Créer la vue de sélection
            project_selection_view = ProjectSelectionView(self.epitech_api, projects_map)
            await interaction.followup.send(embed=embed, view=project_selection_view, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur lors de la récupération de l'historique:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="❓ Guide complet des commandes MouliCord")
    async def help_slash(self, interaction: discord.Interaction):
        """Slash command d'aide avec navigation par pages"""
        
        view = HelpView()
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)


# VIEWS ET COMPOSANTS INTERACTIFS

class MouliResultsView(discord.ui.View):
    """Vue interactive pour les résultats de moulinette avec bouton d'actualisation"""
    
    def __init__(self, epitech_api: EpitechAPI, nombre: int):
        super().__init__(timeout=300)
        self.epitech_api = epitech_api
        self.nombre = nombre
    
    @discord.ui.button(label="🔄 Actualiser", style=discord.ButtonStyle.primary)
    async def refresh_results(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Actualise les résultats"""
        await interaction.response.defer()
        
        try:
            results = self.epitech_api.get_moulinette_results(2025)
            
            if results:
                limited_results = results[:self.nombre]
                embed = self.epitech_api.format_detailed_summary(limited_results)
                embed.title = f"🏫 Résultats Moulinette ({self.nombre} derniers) - Actualisé"
                embed.set_footer(text=f"Dernière actualisation: {datetime.now().strftime('%H:%M:%S')}")
                
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                embed = discord.Embed(
                    title="❌ Erreur d'actualisation",
                    description="Impossible de récupérer les nouveaux résultats",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class ConfirmClearView(discord.ui.View):
    """Vue de confirmation pour la suppression du stockage"""
    
    def __init__(self):
        super().__init__(timeout=30)
    
    @discord.ui.button(label="✅ Confirmer", style=discord.ButtonStyle.danger)
    async def confirm_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Compter les entrées avant suppression
            try:
                with open("results_history.json", "r") as f:
                    data = json.load(f)
                    entries_count = len(data)
            except:
                entries_count = 0
            
            # Vider le fichier
            with open("results_history.json", "w") as f:
                json.dump([], f)
            
            embed = discord.Embed(
                title="🗑️ Stockage Vidé",
                description=f"✅ **{entries_count} entrées** supprimées avec succès",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary)
    async def cancel_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Annulé",
            description="Suppression annulée. Aucune donnée n'a été supprimée.",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)


class ProjectSelectionView(discord.ui.View):
    """Vue pour la sélection de projet dans /history"""
    
    def __init__(self, epitech_api: EpitechAPI, projects_map: dict):
        super().__init__(timeout=300)
        self.epitech_api = epitech_api
        self.projects_map = projects_map
        
        # Ajouter le menu de sélection des projets
        self.add_item(ProjectSelect(epitech_api, projects_map))


class ProjectSelect(discord.ui.Select):
    """Menu déroulant pour sélectionner un projet"""
    
    def __init__(self, epitech_api: EpitechAPI, projects_map: dict):
        self.epitech_api = epitech_api
        self.projects_map = projects_map
        
        # Créer les options pour le menu (max 25)
        options = []
        for project_id, project_data in list(projects_map.items())[:25]:
            project_name = project_data["name"]
            module_code = project_data["module"]
            
            # Tronquer si trop long
            display_name = project_name[:50] + "..." if len(project_name) > 50 else project_name
            display_code = module_code[:50] + "..." if len(module_code) > 50 else module_code
            
            options.append(discord.SelectOption(
                label=display_name,
                description=display_code,
                value=project_id
            ))
        
        super().__init__(
            placeholder="📋 Choisissez un projet...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Traite la sélection du projet"""
        selected_project = self.values[0]
        project_data = self.projects_map.get(selected_project)
        
        if not project_data:
            embed = discord.Embed(
                title="❌ Erreur",
                description="Projet sélectionné introuvable",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Récupérer l'historique du projet
            history = self.epitech_api.get_project_history(selected_project)
            
            if not history:
                embed = discord.Embed(
                    title="❌ Aucun historique",
                    description=f"Aucun historique trouvé pour le projet `{selected_project}`",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Créer l'embed d'historique
            project_name = project_data["name"]
            embed = discord.Embed(
                title=f"📈 Historique - {project_name}",
                description=f"**Projet:** `{selected_project}`\n**Passages trouvés:** {len(history)}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Statistiques d'évolution
            if len(history) >= 2:
                latest = history[0]
                previous = history[1]
                
                latest_rate = self._calculate_rate(latest)
                previous_rate = self._calculate_rate(previous)
                evolution = latest_rate - previous_rate
                
                evolution_text = f"+{evolution:.1f}%" if evolution > 0 else f"{evolution:.1f}%"
                evolution_emoji = "📈" if evolution > 0 else "📉" if evolution < 0 else "➡️"
                
                embed.add_field(
                    name="📊 Évolution Récente",
                    value=f"{evolution_emoji} **{evolution_text}**\n🔄 {previous_rate:.1f}% → {latest_rate:.1f}%",
                    inline=True
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
            
            embed.set_footer(text="MouliCord • Historique détaillé du projet")
            
            # Créer une vue avec menu pour naviguer dans l'historique
            history_view = HistoryView(self.epitech_api, history[:25])
            await interaction.followup.send(embed=embed, view=history_view, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur lors de la récupération de l'historique:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    def _calculate_rate(self, result):
        """Calcule le taux de réussite d'un résultat"""
        skills = result.get("results", {}).get("skills", {})
        total_tests = sum(skill.get("count", 0) for skill in skills.values())
        total_passed = sum(skill.get("passed", 0) for skill in skills.values())
        return (total_passed / total_tests * 100) if total_tests > 0 else 0


class HistoryView(discord.ui.View):
    """Vue pour naviguer dans l'historique d'un projet"""
    
    def __init__(self, epitech_api: EpitechAPI, history: list):
        super().__init__(timeout=300)
        self.epitech_api = epitech_api
        self.history = history
        
        if history:
            self.add_item(HistorySelect(epitech_api, history))


class HistorySelect(discord.ui.Select):
    """Menu déroulant pour sélectionner un passage dans l'historique"""
    
    def __init__(self, epitech_api: EpitechAPI, history: list):
        self.epitech_api = epitech_api
        self.history = history
        
        # Créer les options pour chaque passage (max 25)
        options = []
        for i, entry in enumerate(history[:25]):
            date = entry.get("date", "Date inconnue")
            try:
                # Formater la date
                dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                date_str = date[:16] if len(date) > 16 else date
            
            # Calculer le taux
            skills = entry.get("results", {}).get("skills", {})
            total_tests = sum(skill.get("count", 0) for skill in skills.values())
            total_passed = sum(skill.get("passed", 0) for skill in skills.values())
            rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
            
            options.append(discord.SelectOption(
                label=f"#{i+1} - {rate:.1f}%",
                description=f"{date_str} • {total_passed}/{total_tests} tests",
                value=str(i)
            ))
        
        super().__init__(
            placeholder="📅 Choisissez un passage...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Affiche les détails d'un passage spécifique"""
        try:
            run_index = int(self.values[0])
            run_data = self.history[run_index]
            
            await interaction.response.defer()
            
            # Créer l'embed détaillé pour ce passage
            embed = self.epitech_api.format_detailed_summary([run_data])
            embed.title = f"📊 Passage #{run_index + 1}"
            
            # Ajouter la date
            date = run_data.get("date", "")
            if date:
                try:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    embed.add_field(
                        name="📅 Date",
                        value=dt.strftime("%d/%m/%Y à %H:%M:%S"),
                        inline=True
                    )
                except:
                    embed.add_field(
                        name="📅 Date",
                        value=date,
                        inline=True
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except (ValueError, IndexError):
            embed = discord.Embed(
                title="❌ Passage introuvable",
                description=f"Impossible de récupérer les détails pour ce passage",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class HelpView(discord.ui.View):
    """Vue d'aide avec navigation par pages"""
    
    def __init__(self):
        super().__init__(timeout=300)
        self.current_page = 0
        self.pages = [
            {
                "title": "🏠 MouliCord - Accueil",
                "description": "**Le bot Discord Epitech le plus avancé !** 🚀\n\n🎯 **Fonctionnalités principales:**\n• 📊 Surveillance automatique des résultats\n• 🔔 Notifications @everyone instantanées\n• 📈 Analyses et statistiques détaillées\n• 🔄 Actualisation automatique des tokens\n• 💾 Sauvegarde intelligente des données\n• 📱 Interface moderne avec menus interactifs",
                "fields": [
                    {"name": "🚀 Version", "value": "MouliCord v2.0 - Full Slash Commands", "inline": True},
                    {"name": "⚡ Surveillance", "value": "Active 24/7", "inline": True},
                    {"name": "📱 Interface", "value": "100% Modern UI", "inline": True}
                ]
            },
            {
                "title": "📊 Commandes Principales",
                "description": "**Commandes essentielles pour surveiller vos résultats:**",
                "fields": [
                    {"name": "`/mouli`", "value": "📊 Derniers résultats avec actualisation", "inline": False},
                    {"name": "`/details <projet>`", "value": "🔍 Détails complets d'un projet", "inline": False},
                    {"name": "`/history`", "value": "📈 Sélection projet + navigation", "inline": False},
                    {"name": "`/stats`", "value": "📈 Statistiques complètes", "inline": False}
                ]
            },
            {
                "title": "🔧 Commandes Système",
                "description": "**Gestion et configuration du bot:**",
                "fields": [
                    {"name": "`/status`", "value": "📊 État du bot, API et token", "inline": False},
                    {"name": "`/check_now`", "value": "🔄 Vérification immédiate", "inline": False},
                    {"name": "`/token`", "value": "🔐 Vérification du token", "inline": False},
                    {"name": "`/refresh_token`", "value": "🔄 Actualisation du token", "inline": False},
                    {"name": "`/watch`", "value": "👁️ Statut de surveillance", "inline": False}
                ]
            },
            {
                "title": "💾 Gestion des Données", 
                "description": "**Sauvegarde et maintenance:**",
                "fields": [
                    {"name": "`/backup`", "value": "💾 Sauvegarde horodatée", "inline": False},
                    {"name": "`/clear_storage`", "value": "🗑️ Vider le stockage", "inline": False},
                    {"name": "`/help`", "value": "❓ Ce guide interactif", "inline": False}
                ]
            },
            {
                "title": "🔐 Système de Tokens",
                "description": "**Informations importantes:**",
                "fields": [
                    {"name": "⏰ Durée de vie", "value": "Les tokens Epitech expirent **toutes les heures**", "inline": False},
                    {"name": "🔄 Renouvellement", "value": "Automatique et transparent pour l'utilisateur", "inline": False},
                    {"name": "🛡️ Sécurité", "value": "Aucun stockage permanent, récupération à la demande", "inline": False}
                ]
            }
        ]
    
    def get_embed(self):
        page = self.pages[self.current_page]
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for field in page["fields"]:
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False)
            )
        
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)} • MouliCord v2.0")
        return embed
    
    @discord.ui.button(label="◀️ Précédent", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        
        # Mettre à jour les boutons
        self.children[0].disabled = (self.current_page == 0)
        self.children[1].disabled = (self.current_page == len(self.pages) - 1)
        
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @discord.ui.button(label="Suivant ▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        
        # Mettre à jour les boutons
        self.children[0].disabled = (self.current_page == 0)
        self.children[1].disabled = (self.current_page == len(self.pages) - 1)
        
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


async def setup(bot: commands.Bot):
    """Fonction pour charger le Cog"""
    token = os.getenv('EPITECH_API_TOKEN') or "dummy_token"
    epitech_api = EpitechAPI(token, "results_history.json")
    await bot.add_cog(MouliCordSlashCommands(bot, epitech_api))