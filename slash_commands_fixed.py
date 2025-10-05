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
            placeholder="🔍 Sélectionnez un projet...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.results = results
        self.epitech_api = epitech_api
    
    async def callback(self, interaction: discord.Interaction):
        """Callback when a project is selected"""
        await interaction.response.defer()
        
        selected_slug = self.values[0]
        
        # Trouver le projet sélectionné
        project_result = None
        for result in self.results:
            if result.get("project", {}).get("slug") == selected_slug:
                project_result = result
                break
        
        if not project_result:
            embed = discord.Embed(
                title="❌ Erreur",
                description="Projet non trouvé dans les résultats",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Créer l'embed détaillé manuellement
        project = project_result.get("project", {})
        project_name = project.get("name", "Projet inconnu")
        skills = project_result.get("results", {}).get("skills", {})
        total_tests = sum(skill.get("count", 0) for skill in skills.values())
        total_passed = sum(skill.get("passed", 0) for skill in skills.values())
        rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        progress = self.epitech_api._generate_progress_bar(total_passed, total_tests, 15)
        
        embed = discord.Embed(
            title=f"🔍 Détails - {project_name}",
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
                name=f"🎯 {skill_name}",
                value=f"{passed}/{count} ({skill_rate:.1f}%)\n{skill_progress}",
                inline=True
            )
        
        # Ajouter quelques infos supplémentaires
        embed.add_field(
            name="📅 Date",
            value=project_result.get("date", "Non disponible"),
            inline=True
        )
        
        embed.add_field(
            name="💾 Token",
            value="🔄 Expire dans ~1h\n⚠️ Actualisez si nécessaire",
            inline=True
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class RefreshView(discord.ui.View):
    """Vue pour les boutons de rafraîchissement"""
    
    def __init__(self, epitech_api, nombre: int = 5):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.epitech_api = epitech_api
        self.nombre = nombre

    @discord.ui.button(label="🔄 Actualiser", style=discord.ButtonStyle.primary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Bouton pour actualiser les résultats"""
        await interaction.response.defer()
        
        try:
            # Récupérer les nouveaux résultats
            results = self.epitech_api.get_moulinette_results(2025)
            if not results:
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="Impossible de récupérer les nouveaux résultats",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Limiter au nombre demandé
            limited_results = results[:self.nombre]
            
            # Créer le nouvel embed
            if hasattr(self.epitech_api, 'format_summary'):
                embed = self.epitech_api.format_summary(limited_results)
            else:
                # Fallback si format_summary n'existe pas
                embed = discord.Embed(
                    title=f"🏫 Résultats Moulinette ({self.nombre} derniers) - Actualisé",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                for result in limited_results:
                    project = result.get("project", {})
                    name = project.get("name", "Projet inconnu")
                    skills = result.get("results", {}).get("skills", {})
                    total_tests = sum(skill.get("count", 0) for skill in skills.values())
                    total_passed = sum(skill.get("passed", 0) for skill in skills.values())
                    rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
                    progress = self.epitech_api._generate_progress_bar(total_passed, total_tests, 10)
                    
                    embed.add_field(
                        name=f"📋 {name}",
                        value=f"📊 {total_passed}/{total_tests} ({rate:.1f}%)\n📈 {progress}",
                        inline=False
                    )

            embed.set_footer(text=f"Dernière actualisation: {datetime.now().strftime('%H:%M:%S')}")
            await interaction.edit_original_response(embed=embed, view=self)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur lors de l'actualisation",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class MouliCordSlashCommands(commands.Cog):
    """Cog contenant toutes les commandes slash de MouliCord"""
    
    def __init__(self, bot, epitech_api):
        self.bot = bot
        self.epitech_api = epitech_api

    @app_commands.command(name="ping", description="🏓 Teste la latence du bot")
    async def ping_slash(self, interaction: discord.Interaction):
        """Slash command pour tester la latence"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"⚡ Latence: **{latency}ms**",
            color=discord.Color.green() if latency < 100 else discord.Color.orange() if latency < 200 else discord.Color.red(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="results", description="📊 Affiche les résultats de la moulinette")
    @app_commands.describe(nombre="Nombre de résultats à afficher (par défaut: 5)")
    async def results_slash(self, interaction: discord.Interaction, nombre: Optional[int] = 5):
        """Slash command pour afficher les résultats"""
        await interaction.response.defer(thinking=True)
        
        # Gérer le cas où nombre est None
        if nombre is None:
            nombre = 5
            
        if nombre < 1 or nombre > 20:
            embed = discord.Embed(
                title="❌ Nombre invalide",
                description="Le nombre doit être entre 1 et 20",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
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

            # Limiter aux résultats demandés
            limited_results = results[:nombre]
            
            # Utiliser format_summary de l'API
            embed = self.epitech_api.format_summary(limited_results)
            embed.set_footer(text=f"💾 Token expire dans ~1h • 🔄 Actualisation auto")
            
            view = RefreshView(self.epitech_api, nombre)
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

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
            
            embed.add_field(
                name="💾 Token",
                value="🔄 Expire dans ~1h\n⚠️ Actualisez si nécessaire",
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