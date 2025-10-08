import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import json
import base64
import csv
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from epitech_api import EpitechAPI
from token_refresher import auto_refresh_token
import os


# (ProjectDetailsView et ProjectSelect supprimées - utilisées uniquement pour /details)

class TokenView(discord.ui.View):
    """Vue pour la commande /token avec bouton de rafraîchissement"""
    
    def __init__(self, epitech_api):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.epitech_api = epitech_api
    
    @discord.ui.button(label="🔄 Actualiser Token", style=discord.ButtonStyle.primary)
    async def refresh_token_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Bouton pour actualiser le token"""
        await interaction.response.defer()
        
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
            success = auto_refresh_token(headless=True, update_env=False)
            
            if success:
                # Vérifier le nouveau token et relier l'API en mémoire
                try:
                    import bot as bot_module
                    if bot_module.ensure_valid_token() and getattr(bot_module, 'epitech_api', None):
                        self.epitech_api = bot_module.epitech_api
                except Exception:
                    pass

                # Construire un résumé avec timestamps Discord
                token_info = self.epitech_api.get_token_info()
                is_expired = token_info.get("is_expired", True)
                # Temps restant (approx)
                minutes_left = token_info.get("minutes_remaining", 0)
                hours_left = token_info.get("hours_remaining", 0)
                days_left = token_info.get("days_remaining", 0)
                if days_left > 0:
                    time_left = f"{days_left} jour{'s' if days_left > 1 else ''} {hours_left}h"
                elif hours_left > 0:
                    suffix = f" {minutes_left}min" if minutes_left > 0 else ""
                    time_left = f"{hours_left}h{suffix}"
                else:
                    time_left = f"{minutes_left} minute{'s' if minutes_left > 1 else ''}"

                exp_epoch = token_info.get("exp_epoch")
                iat_epoch = token_info.get("iat_epoch")
                expires_text = f"<t:{exp_epoch}:F> (<t:{exp_epoch}:R>)" if exp_epoch else token_info.get("expires_at", "Inconnu")
                issued_text = f"<t:{iat_epoch}:F> (<t:{iat_epoch}:R>)" if iat_epoch else token_info.get("issued_at", "Inconnu")

                token_summary = (
                    "✅ **Token valide**\n" if not is_expired else "❌ **Token expiré**\n"
                ) + (
                    f"⏰ Temps restant: **{time_left}**\n" if not is_expired else ""
                ) + (
                    f"📅 Expire le: {expires_text}\n"
                ) + (
                    f"🕐 Émis le: {issued_text}" if token_info.get("issued_at") or iat_epoch else ""
                )

                embed = discord.Embed(
                    title="✅ Token Actualisé",
                    description="🎉 Le token a été actualisé avec succès !",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="🔑 Nouveau Token", value=token_summary, inline=False)
                
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

            # Trier par date (plus récent en premier) puis limiter au nombre demandé
            results_sorted = sorted(results, key=lambda x: x.get("date", ""), reverse=True)
            limited_results = results_sorted[:self.nombre]
            
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
                    
                    # Choisir les couleurs selon le taux de réussite
                    if rate >= 100:
                        emoji = "✅"
                    elif rate >= 80:
                        emoji = "🟡"
                    elif rate >= 50:
                        emoji = "🟠"
                    else:
                        emoji = "❌"
                    
                    progress = self.epitech_api._generate_progress_bar(total_passed, total_tests, 10)
                    
                    embed.add_field(
                        name=f"{emoji} {name}",
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
    
    def update_epitech_api(self, new_api):
        """Met à jour l'instance de l'API Epitech"""
        self.epitech_api = new_api
        # Log côté bot uniquement; éviter le bruit ici
        pass
    
    async def get_results_with_fallback(self, year=2025):
        """Récupère les résultats avec fallback automatique vers les données locales en cas d'erreur API"""
        try:
            # Tentative via l'API
            results = self.epitech_api.get_moulinette_results(year)
            return results, None  # results, error_message
        except Exception as api_err:
            api_error = str(api_err)
            
            # Vérifier si c'est une erreur de token (403)
            if "403" in api_error or "Forbidden" in api_error:
                # Tentative silencieuse de renouvellement
                
                try:
                    import importlib
                    import bot
                    importlib.reload(bot)  # Recharger pour obtenir les variables globales mises à jour
                    
                    if bot.ensure_valid_token() and bot.epitech_api:
                        self.epitech_api = bot.epitech_api
                        results = self.epitech_api.get_moulinette_results(year)
                        return results, None
                    else:
                        pass
                except Exception as refresh_err:
                    pass
            
            # Fallback vers les données locales
            try:
                with open("results_history.json", "r") as f:
                    local_data = json.load(f)
                    results = local_data.get("results", [])
                    
                if results:
                    return results, f"Token expiré - Données du cache local"
                else:
                    return None, api_error
            except Exception as local_err:
                return None, api_error

    async def _run_check_now(self) -> discord.Embed:
        """Exécute la vérification immédiate et retourne l'embed approprié."""
        try:
            results = self.epitech_api.get_moulinette_results(2025)
            if results:
                embed = discord.Embed(
                    title="🔍 Vérification terminée",
                    description=f"{len(results)} projet(s) trouvés dans les résultats actuels",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                # Trier par date (plus récent en premier) puis prendre les 3 premiers
                results_sorted = sorted(results, key=lambda x: x.get("date", ""), reverse=True)
                for i, result in enumerate(results_sorted[:3]):
                    # Extraire le nom du projet depuis la structure correcte
                    project_data = result.get("project", {})
                    project_name = project_data.get("name", "Projet inconnu")
                    
                    skills = result.get("results", {}).get("skills", {})
                    total_tests = sum(skill.get("count", 0) for skill in skills.values())
                    total_passed = sum(skill.get("passed", 0) for skill in skills.values())
                    rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
                    
                    # Choisir l'emoji selon le taux de réussite
                    if rate >= 100:
                        emoji = "✅"
                    elif rate >= 80:
                        emoji = "🟡"
                    elif rate >= 50:
                        emoji = "🟠"
                    else:
                        emoji = "❌"
                    
                    embed.add_field(
                        name=f"{emoji} {project_name}",
                        value=f"📊 {total_passed}/{total_tests} ({rate:.1f}%)",
                        inline=True
                    )
            else:
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="Récupération des résultats impossible",
                    color=discord.Color.red()
                )
            return embed
        except Exception as e:
            return discord.Embed(
                title="❌ Erreur lors de la vérification",
                description=f"```{str(e)}```",
                color=discord.Color.red()
            )

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
            # Utiliser la méthode avec fallback
            results, error_msg = await self.get_results_with_fallback(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucun résultat disponible",
                    description="• ⚠️ Token expiré (validité ~1h)\n• 📡 API inaccessible (403 Forbidden)\n• 💾 Aucune donnée locale disponible\n\n💡 Utilisez `/token` puis cliquez sur 'Actualiser Token'",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Trier par date (plus récent en premier) puis limiter aux résultats demandés
            results_sorted = sorted(results, key=lambda x: x.get("date", ""), reverse=True)
            limited_results = results_sorted[:nombre]
            
            # Créer l'embed manuellement (format_summary peut ne pas être disponible)
            embed = discord.Embed(
                title=f"📊 Résultats Moulinette ({len(limited_results)} derniers)",
                color=discord.Color.green() if not error_msg else discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            # Indication de la source des données
            embed.description = "Source: 🌐 Temps réel" if not error_msg else "Source: 💾 Cache local (token expiré)"
            
            # Ajouter les résultats
            for result in limited_results:
                project = result.get("project", {})
                name = project.get("name", "Projet inconnu")
                skills = result.get("results", {}).get("skills", {})
                total_tests = sum(skill.get("count", 0) for skill in skills.values())
                total_passed = sum(skill.get("passed", 0) for skill in skills.values())
                rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
                
                # Créer une barre de progression colorée
                progress_length = 10
                filled = int((total_passed / total_tests) * progress_length) if total_tests > 0 else 0
                
                # Choisir les couleurs selon le taux de réussite (carrés)
                if rate >= 100:
                    filled_char = "🟩"
                    empty_char = "⬜"
                    emoji = "✅"
                elif rate >= 80:
                    filled_char = "🟨"
                    empty_char = "⬜"
                    emoji = "🟡"
                elif rate >= 50:
                    filled_char = "🟧"
                    empty_char = "⬜"
                    emoji = "🟠"
                else:
                    filled_char = "🟥"
                    empty_char = "⬜"
                    emoji = "❌"
                
                progress_bar = filled_char * filled + empty_char * (progress_length - filled)
                
                embed.add_field(
                    name=f"{emoji} {name}",
                    value=f"📊 {total_passed}/{total_tests} ({rate:.1f}%)\n📈 {progress_bar}",
                    inline=False
                )
            
            # Footer avec info sur le token
            if error_msg:
                embed.set_footer(text="Mode dégradé • Utilisez /token pour actualiser")
            else:
                embed.set_footer(text="Token valide ~1h • Actualisation automatique")
            
            view = RefreshView(self.epitech_api, nombre)
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur Critique",
                description=f"```{str(e)[:300]}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    # (/details supprimée)
    # (/watch supprimée)

    @app_commands.command(name="status", description="📊 Affiche le statut du bot et de l'API")
    async def status_slash(self, interaction: discord.Interaction):
        """Slash command pour le statut"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Vérifier l'état de l'API
            try:
                results = self.epitech_api.get_moulinette_results(2025)
                api_status = "✅ Connectée et fonctionnelle"
                
                # Vérifier le token
                token_info = self.epitech_api.check_token_expiration()
                
            except Exception as e:
                api_status = f"❌ Erreur: {str(e)[:50]}..."
                token_info = "❌ Impossible de vérifier"
            
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
        
        embed = await self._run_check_now()
        await interaction.followup.send(embed=embed, ephemeral=True)

    # (Alias /force_check supprimé)

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
                    # Préférer le nom du projet si disponible
                    project_info = project.get("project", {}) if isinstance(project.get("project"), dict) else {}
                    project_name = project_info.get("name") if project_info else None
                    # Fallback: code du module dans project.project.module.code ou ancienne clé "module"
                    module_info = project_info.get("module", {}) if project_info else {}
                    module_code = module_info.get("code") if isinstance(module_info, dict) else None
                    legacy_module = project.get("module")
                    display_name = project_name or module_code or legacy_module or "Projet inconnu"

                    rate = get_project_rate(project)
                    medals = ["🥇", "🥈", "🥉"]
                    top_text += f"{medals[i]} `{display_name}` ({rate:.1f}%)\n"
                
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
        """Slash command pour vérifier le token avec bouton de rafraîchissement"""
        
        await interaction.response.defer(thinking=True)
        
        try:
            expiration_info = self.epitech_api.check_token_expiration()
            
            embed = discord.Embed(
                title="🔐 Statut du Token",
                description=expiration_info,
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Ajouter des informations supplémentaires
            embed.add_field(
                name="🔧 Actions",
                value="• Cliquez sur le bouton ci-dessous pour actualiser\n• Le token expire automatiquement après 1h\n• Actualisation automatique en arrière-plan",
                inline=False
            )
            
            # Créer la vue avec le bouton de rafraîchissement
            view = TokenView(self.epitech_api)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Impossible de vérifier le token:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    # (/refresh_token supprimée - fonctionnalité intégrée dans /token)

    @app_commands.command(name="history", description="📈 Analyse l'historique d'un projet avec sélection interactive")
    async def history_slash(self, interaction: discord.Interaction):
        """Slash command pour l'historique avec sélection de projet"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Récupérer tous les résultats avec fallback automatique
            results, error_msg = await self.get_results_with_fallback(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucun résultat disponible",
                    description="• ⚠️ Token expiré (validité ~1h)\n• 📡 API inaccessible (403 Forbidden)\n• 💾 Aucune donnée locale disponible\n\n💡 Utilisez `/token` puis cliquez sur 'Actualiser Token'",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Extraire tous les projets uniques avec leurs informations
            projects_map = {}
            for result in results:
                # Extraire les informations du projet depuis la structure correcte
                project_data = result.get("project", {})
                module_code = project_data.get("module", {}).get("code", "")
                project_slug = project_data.get("slug", "")
                project_name = project_data.get("name", project_slug)
                
                # Construire l'ID du projet au format "module/project"
                if module_code and project_slug:
                    project_id = f"{module_code}/{project_slug}"
                    
                    if project_id not in projects_map:
                        projects_map[project_id] = {
                            "name": project_name,
                            "module": module_code,
                            "slug": project_slug
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

    @app_commands.command(name="logs", description="📋 Affiche les logs d'erreur des dernières moulinettes")
    async def logs_slash(self, interaction: discord.Interaction):
        """Slash command pour afficher les logs d'erreur des moulinettes"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Récupérer tous les résultats avec fallback automatique
            results, error_msg = await self.get_results_with_fallback(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucun résultat disponible",
                    description="• ⚠️ Token expiré (validité ~1h)\n• 📡 API inaccessible (403 Forbidden)\n• 💾 Aucune donnée locale disponible\n\n💡 Utilisez `/token` puis cliquez sur 'Actualiser Token'",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Trier par date (plus récent en premier) et limiter à 25 pour le menu
            results_sorted = sorted(results, key=lambda x: x.get("date", ""), reverse=True)
            limited_results = results_sorted[:25]
            
            # Créer l'embed de sélection
            embed = discord.Embed(
                title="📋 Logs d'Erreur des Moulinettes",
                description=f"**Sélectionnez une moulinette** pour voir les détails des erreurs.\n\n📊 **{len(limited_results)} moulinettes** disponibles",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🔍 Fonctionnalités",
                value="• Messages d'erreur détaillés\n• Première tâche qui échoue\n• Détails des tests",
                inline=True
            )
            
            embed.add_field(
                name="📊 Informations",
                value="• Troncature des erreurs\n• Navigation interactive\n• Détails complets",
                inline=True
            )
            
            # Créer la vue de sélection
            logs_view = LogsSelectionView(self.epitech_api, limited_results)
            await interaction.followup.send(embed=embed, view=logs_view, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur lors de la récupération des logs:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="export", description="📊 Exporte vos données en CSV, JSON ou PDF")
    @app_commands.choices(format=[
        app_commands.Choice(name="CSV", value="csv"),
        app_commands.Choice(name="JSON", value="json"),
        app_commands.Choice(name="PDF", value="pdf")
    ])
    async def export_slash(self, interaction: discord.Interaction, format: str = "csv"):
        """Slash command pour exporter les données"""
        await interaction.response.defer(thinking=True)
        
        try:
            # Récupérer les résultats
            results, error_msg = await self.get_results_with_fallback(2025)
            
            if not results:
                embed = discord.Embed(
                    title="❌ Aucun résultat disponible",
                    description="• ⚠️ Token expiré (validité ~1h)\n• 📡 API inaccessible (403 Forbidden)\n• 💾 Aucune donnée locale disponible\n\n💡 Utilisez `/token` puis cliquez sur 'Actualiser Token'",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Préparer les données pour l'export
            export_data = []
            for result in results:
                # Extraire les informations de base depuis différentes structures possibles
                project_name = result.get("projectName") or result.get("project", {}).get("name") or "N/A"
                module_code = result.get("moduleCode") or result.get("project", {}).get("module", {}).get("code") or "N/A"
                date = result.get("date", "N/A")
                
                # Extraire le score depuis différentes sources
                score = result.get("score", 0)
                if score == 0:
                    # Essayer de calculer le score depuis les skills
                    skills = result.get("results", {}).get("skills", {})
                    if skills:
                        total_tasks = 0
                        passed_tasks = 0
                        for skill_data in skills.values():
                            if isinstance(skill_data, dict):
                                count = skill_data.get("count", 0)
                                passed = skill_data.get("passed", 0)
                                total_tasks += count
                                passed_tasks += passed
                        if total_tasks > 0:
                            score = int((passed_tasks / total_tasks) * 100)
                
                status = result.get("status", "N/A")
                
                # Extraire les détails des skills
                skills = result.get("results", {}).get("skills", {})
                total_tasks = 0
                passed_tasks = 0
                failed_tasks = 0
                
                for skill_name, skill_data in skills.items():
                    if isinstance(skill_data, dict):
                        count = skill_data.get("count", 0)
                        passed = skill_data.get("passed", 0)
                        total_tasks += count
                        passed_tasks += passed
                        failed_tasks += (count - passed)
                
                export_data.append({
                    "Date": date,
                    "Module": module_code,
                    "Projet": project_name,
                    "Score": score,
                    "Statut": status,
                    "Tâches Total": total_tasks,
                    "Tâches Réussies": passed_tasks,
                    "Tâches Échouées": failed_tasks,
                    "Taux de Réussite": f"{(passed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
                })
            
            # Trier par date (plus récentes en premier)
            export_data.sort(key=lambda x: x["Date"], reverse=True)
            
            # Créer le fichier selon le format demandé
            if format.lower() == "csv":
                # Créer le CSV
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
                file_content = output.getvalue()
                file_extension = "csv"
                mime_type = "text/csv"
            elif format.lower() == "pdf":
                # Créer le PDF
                file_content = self._generate_pdf_report(export_data)
                file_extension = "pdf"
                mime_type = "application/pdf"
            else:  # JSON
                file_content = json.dumps(export_data, indent=2, ensure_ascii=False)
                file_extension = "json"
                mime_type = "application/json"
            
            # Créer le fichier Discord
            if format.lower() == "pdf":
                file = discord.File(io.BytesIO(file_content), 
                                  filename=f"moulicord_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}")
            else:
                file = discord.File(io.BytesIO(file_content.encode('utf-8')), 
                                  filename=f"moulicord_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}")
            
            embed = discord.Embed(
                title="📊 Export terminé",
                description=f"Vos données ont été exportées en format **{format.upper()}**\n\n"
                           f"📈 **{len(export_data)}** entrées exportées\n"
                           f"📅 Du {export_data[-1]['Date']} au {export_data[0]['Date']}",
                color=discord.Color.green()
            )
            
            await interaction.followup.send(embed=embed, file=file, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur d'export",
                description=f"Erreur lors de l'export: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="❓ Guide complet des commandes MouliCord")
    async def help_slash(self, interaction: discord.Interaction):
        """Slash command d'aide avec navigation par pages"""
        
        view = HelpView()
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

    def _generate_pdf_report(self, export_data: list) -> bytes:
        """Génère un rapport PDF des données exportées"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Centré
            textColor=colors.HexColor('#2E86AB')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#A23B72')
        )
        
        # Contenu du PDF
        story = []
        
        # Titre
        story.append(Paragraph("📊 Rapport MouliCord", title_style))
        story.append(Spacer(1, 12))
        
        # Informations générales
        total_entries = len(export_data)
        if export_data:
            avg_score = sum(int(row["Score"]) for row in export_data if row["Score"] != "N/A") / len([r for r in export_data if r["Score"] != "N/A"])
            date_range = f"Du {export_data[-1]['Date'][:10]} au {export_data[0]['Date'][:10]}"
        else:
            avg_score = 0
            date_range = "Aucune donnée"
        
        story.append(Paragraph(f"<b>Résumé des performances</b>", heading_style))
        story.append(Paragraph(f"• <b>Total des entrées:</b> {total_entries}", styles['Normal']))
        story.append(Paragraph(f"• <b>Score moyen:</b> {avg_score:.1f}%", styles['Normal']))
        story.append(Paragraph(f"• <b>Période:</b> {date_range}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Tableau des données
        if export_data:
            story.append(Paragraph("<b>Détails des moulinettes</b>", heading_style))
            
            # Préparer les données du tableau
            table_data = [["Date", "Module", "Projet", "Score", "Tâches", "Réussite"]]
            
            for row in export_data[:50]:  # Limiter à 50 entrées pour éviter les PDF trop longs
                date_str = row["Date"][:10] if row["Date"] != "N/A" else "N/A"
                module = row["Module"][:15] + "..." if len(row["Module"]) > 15 else row["Module"]
                project = row["Projet"][:20] + "..." if len(row["Projet"]) > 20 else row["Projet"]
                score = str(row["Score"]) + "%" if row["Score"] != "N/A" else "N/A"
                tasks = f"{row['Tâches Réussies']}/{row['Tâches Total']}"
                success_rate = row["Taux de Réussite"]
                
                table_data.append([date_str, module, project, score, tasks, success_rate])
            
            # Créer le tableau
            table = Table(table_data, colWidths=[1.2*inch, 1.2*inch, 1.8*inch, 0.8*inch, 0.8*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Statistiques par performance
        if export_data:
            story.append(Paragraph("<b>Répartition par performance</b>", heading_style))
            
            excellent = len([r for r in export_data if int(r["Score"]) >= 90])
            good = len([r for r in export_data if 70 <= int(r["Score"]) < 90])
            average = len([r for r in export_data if 50 <= int(r["Score"]) < 70])
            poor = len([r for r in export_data if int(r["Score"]) < 50])
            
            stats_data = [
                ["Performance", "Nombre", "Pourcentage"],
                ["🟢 Excellent (≥90%)", str(excellent), f"{(excellent/total_entries*100):.1f}%"],
                ["🟡 Bon (70-89%)", str(good), f"{(good/total_entries*100):.1f}%"],
                ["🟠 Moyen (50-69%)", str(average), f"{(average/total_entries*100):.1f}%"],
                ["🔴 À améliorer (<50%)", str(poor), f"{(poor/total_entries*100):.1f}%"]
            ]
            
            stats_table = Table(stats_data, colWidths=[2*inch, 1*inch, 1*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#A23B72')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            
            story.append(stats_table)
        
        # Pied de page
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"<i>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par MouliCord</i>", styles['Normal']))
        
        # Construire le PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


# VIEWS ET COMPOSANTS INTERACTIFS

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
        self.add_item(HistoryProjectSelect(epitech_api, projects_map))


class HistoryProjectSelect(discord.ui.Select):
    """Menu déroulant pour sélectionner un projet dans l'historique"""
    
    def __init__(self, epitech_api: EpitechAPI, projects_map: dict):
        self.epitech_api = epitech_api
        self.projects_map = projects_map
        
        # Créer les options pour le menu (max 25) - triées dans l'ordre inverse
        options = []
        sorted_projects = sorted(projects_map.items(), key=lambda x: x[0], reverse=True)
        for project_id, project_data in sorted_projects:
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
            # Vérifier que l'API est disponible
            if not self.epitech_api:
                embed = discord.Embed(
                    title="❌ API non disponible",
                    description="L'API Epitech n'est pas initialisée. Utilisez `/token` pour la réinitialiser.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Récupérer l'historique du projet (API + fallback local)
            history = self.epitech_api.get_project_history(selected_project)
            
            # Si pas d'historique via API, essayer de construire depuis les données locales
            if not history:
                history = self._get_local_project_history(selected_project)
            
            if not history:
                embed = discord.Embed(
                    title="❌ Aucun historique",
                    description=f"Aucun historique trouvé pour le projet `{selected_project}`\n\n💡 Vérifiez que le projet existe et que vous avez des résultats pour celui-ci.",
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
    
    def _get_local_project_history(self, project_id: str):
        """Construit l'historique d'un projet depuis les données locales"""
        try:
            # Charger les données locales
            with open("results_history.json", "r") as f:
                data = json.load(f)
            
            results = data.get("results", [])
            
            # Filtrer les résultats pour ce projet
            project_history = []
            for result in results:
                project_data = result.get("project", {})
                module_code = project_data.get("module", {}).get("code", "")
                project_slug = project_data.get("slug", "")
                
                if module_code and project_slug:
                    current_project_id = f"{module_code}/{project_slug}"
                    if current_project_id == project_id:
                        project_history.append(result)
            
            # Trier par date (plus récent en premier)
            project_history.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            return project_history
            
        except Exception as e:
            print(f"Erreur lors de la récupération de l'historique local pour {project_id}: {e}")
            return []


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
            
            # Créer l'embed détaillé pour ce passage manuellement
            project = run_data.get("project", {})
            project_name = project.get("name", "Projet inconnu")
            skills = run_data.get("results", {}).get("skills", {})
            total_tests = sum(skill.get("count", 0) for skill in skills.values())
            total_passed = sum(skill.get("passed", 0) for skill in skills.values())
            rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
            progress = self.epitech_api._generate_progress_bar(total_passed, total_tests, 15)
            
            embed = discord.Embed(
                title=f"📊 Passage #{run_index + 1} - {project_name}",
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


class LogsSelectionView(discord.ui.View):
    """Vue pour la sélection de moulinette dans /logs"""
    
    def __init__(self, epitech_api: EpitechAPI, results: list):
        super().__init__(timeout=300)
        self.epitech_api = epitech_api
        self.results = results
        
        # Ajouter le menu de sélection des moulinettes
        self.add_item(LogsMoulinetteSelect(epitech_api, results))


class LogsMoulinetteSelect(discord.ui.Select):
    """Menu déroulant pour sélectionner une moulinette dans /logs"""
    
    def __init__(self, epitech_api: EpitechAPI, results: list):
        self.epitech_api = epitech_api
        self.results = results
        
        # Créer les options pour le menu (max 25)
        options = []
        for i, result in enumerate(results[:25]):
            project = result.get("project", {})
            project_name = project.get("name", "Projet inconnu")
            date = result.get("date", "")
            
            # Formater la date
            try:
                dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                date_str = date[:16] if len(date) > 16 else date
            
            # Calculer le score
            skills = result.get("results", {}).get("skills", {})
            total_tests = sum(skill.get("count", 0) for skill in skills.values())
            total_passed = sum(skill.get("passed", 0) for skill in skills.values())
            rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
            
            # Tronquer le nom si trop long
            display_name = project_name[:50] + "..." if len(project_name) > 50 else project_name
            
            # Choisir l'emoji selon le score
            if rate >= 100:
                emoji = "✅"
            elif rate >= 80:
                emoji = "🟡"
            elif rate >= 50:
                emoji = "🟠"
            else:
                emoji = "❌"
            
            options.append(discord.SelectOption(
                label=f"{emoji} {display_name}",
                description=f"{date_str} • {rate:.1f}%",
                value=str(i)
            ))
        
        super().__init__(
            placeholder="📋 Choisissez une moulinette...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Traite la sélection de la moulinette"""
        try:
            moulinette_index = int(self.values[0])
            moulinette_data = self.results[moulinette_index]
            
            await interaction.response.defer()
            
            # Récupérer les détails de la moulinette
            test_run_id = moulinette_data.get("results", {}).get("testRunId")
            if not test_run_id:
                embed = discord.Embed(
                    title="❌ Erreur",
                    description="ID de test non trouvé pour cette moulinette",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Récupérer les détails via l'API
            details = self.epitech_api.get_detailed_results(test_run_id)
            
            if not details:
                # Fallback: utiliser les données de base
                await self._show_basic_logs(interaction, moulinette_data)
                return
            
            # Afficher les logs détaillés
            await self._show_detailed_logs(interaction, moulinette_data, details)
            
        except (ValueError, IndexError):
            embed = discord.Embed(
                title="❌ Moulinette introuvable",
                description="Impossible de récupérer les détails pour cette moulinette",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur lors de la récupération des logs:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _show_basic_logs(self, interaction: discord.Interaction, moulinette_data: dict):
        """Affiche les logs basiques quand les détails ne sont pas disponibles"""
        project = moulinette_data.get("project", {})
        project_name = project.get("name", "Projet inconnu")
        skills = moulinette_data.get("results", {}).get("skills", {})
        
        # Trouver la première tâche qui échoue
        first_failed_task = None
        for task_name, task_data in skills.items():
            task_passed = task_data.get("passed", 0)
            task_count = task_data.get("count", 0)
            task_crashed = task_data.get("crashed", 0)
            task_mandatory_failed = task_data.get("mandatoryFailed", 0)
            
            # Une tâche échoue si : pas tous les tests passés, ou des tests crashés, ou des échecs obligatoires
            if (task_passed < task_count and task_count > 0) or task_crashed > 0 or task_mandatory_failed > 0:
                first_failed_task = {
                    "name": task_name,
                    "passed": task_passed,
                    "count": task_count,
                    "crashed": task_crashed,
                    "mandatory_failed": task_mandatory_failed
                }
                break
        
        embed = discord.Embed(
            title=f"📋 Logs - {project_name}",
            description="Détails des erreurs de la moulinette",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        if first_failed_task:
            # Construire le message d'erreur selon le type d'échec
            error_details = f"**{first_failed_task['name']}**\n"
            error_details += f"Tests: {first_failed_task['passed']}/{first_failed_task['count']}\n"
            
            if first_failed_task['crashed'] > 0:
                error_details += f"💥 **Crashed:** {first_failed_task['crashed']}\n"
            if first_failed_task['mandatory_failed'] > 0:
                error_details += f"🚫 **Mandatory Failed:** {first_failed_task['mandatory_failed']}\n"
            
            # Déterminer l'icône selon le type d'échec
            if first_failed_task['crashed'] > 0:
                icon = "💥"
                error_type = "Tâche crashée"
            elif first_failed_task['mandatory_failed'] > 0:
                icon = "🚫"
                error_type = "Échec obligatoire"
            else:
                icon = "❌"
                error_type = "Tests échoués"
            
            embed.add_field(
                name=f"{icon} {error_type}",
                value=error_details,
                inline=False
            )
            
            # Ajouter un message pour les logs détaillés
            embed.add_field(
                name="🔍 Logs d'erreur",
                value="Les logs détaillés ne sont pas disponibles en mode basique.\n"
                      "Utilisez `/token` pour actualiser et obtenir les détails complets.",
                inline=False
            )
        else:
            embed.add_field(
                name="✅ Aucune erreur",
                value="Toutes les tâches ont réussi",
                inline=False
            )
        
        # Résumé des compétences
        skills_summary = []
        for task_name, task_data in list(skills.items())[:10]:  # Limiter à 10
            task_passed = task_data.get("passed", 0)
            task_count = task_data.get("count", 0)
            task_crashed = task_data.get("crashed", 0)
            
            if task_passed == task_count and task_count > 0:
                icon = "✅"
            elif task_crashed > 0:
                icon = "💥"
            elif task_passed > 0:
                icon = "⚠️"
            else:
                icon = "❌"
            
            skills_summary.append(f"{icon} **{task_name}**: {task_passed}/{task_count}")
        
        if skills_summary:
            embed.add_field(
                name="📊 Résumé des tâches",
                value="\n".join(skills_summary),
                inline=False
            )
        
        embed.set_footer(text="MouliCord • Logs basiques (détails non disponibles)")
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    def _get_performance_color(self, score: int) -> discord.Color:
        """Retourne une couleur selon le score de performance"""
        if score >= 90:
            return discord.Color.green()
        elif score >= 70:
            return discord.Color.yellow()
        elif score >= 50:
            return discord.Color.orange()
        else:
            return discord.Color.red()
    
    def _get_performance_emoji(self, score: int) -> str:
        """Retourne un emoji selon le score de performance"""
        if score >= 90:
            return "🟢"
        elif score >= 70:
            return "🟡"
        elif score >= 50:
            return "🟠"
        else:
            return "🔴"

    def _extract_failed_task_output(self, output: str, task_name: str) -> str:
        """Extrait uniquement la partie pertinente des logs d'erreur d'une tâche"""
        if not output:
            return ""
        
        # Nettoyer l'output (enlever les caractères de contrôle)
        cleaned_output = output.replace('\x1b[0m', '').replace('\x1b[31m', '').replace('\x1b[32m', '').replace('\x1b[33m', '')
        
        # Diviser par lignes
        lines = cleaned_output.split('\n')
        
        # Chercher la première tâche qui échoue (FAILURE)
        failed_task_start = -1
        for i, line in enumerate(lines):
            if ": FAILURE" in line or "Test failed:" in line:
                # Remonter pour trouver le début de la section de cette tâche
                for j in range(i, max(0, i-20), -1):
                    if "====" in lines[j] and ("task" in lines[j].lower() or "====" in lines[j]):
                        failed_task_start = j
                        break
                break
        
        if failed_task_start == -1:
            # Si on ne trouve pas de FAILURE, chercher la tâche spécifique par nom
            task_name_short = task_name.split(' - ')[1] if ' - ' in task_name else task_name
            for i, line in enumerate(lines):
                if f"task{task_name_short}" in line and "====" in line:
                    failed_task_start = i
                    break
            
            if failed_task_start == -1:
                return cleaned_output[:2000] + ("..." if len(cleaned_output) > 2000 else "")
        
        # Extraire la section de la tâche qui échoue
        task_lines = []
        
        for i in range(failed_task_start, len(lines)):
            line = lines[i]
            task_lines.append(line)
            
            # Arrêter à la prochaine section de tâche ou à la fin
            if i + 1 < len(lines) and "====" in lines[i + 1] and "task" in lines[i + 1].lower():
                break
        
        # Filtrer pour ne garder que la partie "Executing all tests..." et les résultats d'erreur
        filtered_lines = []
        in_execution_section = False
        
        for line in task_lines:
            if "# Executing all tests..." in line:
                in_execution_section = True
                filtered_lines.append(line)
            elif in_execution_section:
                # Garder toutes les lignes importantes, même vides
                if not line.startswith("# Building...") and not line.startswith("# Checking for forbidden functions..."):
                    filtered_lines.append(line)
                # Ne pas s'arrêter à la première ligne qui commence par "#"
                # Continuer jusqu'à la fin de la section de la tâche
        
        result = '\n'.join(filtered_lines)
        
        # Tronquer si trop long
        if len(result) > 2000:
            result = result[:2000] + "\n... (tronqué)"
        
        return result

    async def _show_detailed_logs(self, interaction: discord.Interaction, moulinette_data: dict, details: dict):
        """Affiche les logs détaillés avec les messages d'erreur"""
        project = moulinette_data.get("project", {})
        project_name = project.get("name", "Projet inconnu")
        
        # Utiliser les données de moulinette_data en priorité (comme les autres commandes)
        skills = moulinette_data.get("results", {}).get("skills", {})
        
        # Si pas de skills dans moulinette_data, essayer de récupérer depuis les détails
        if not skills:
            results = details.get("results", {})
            skills = results.get("skills", {})
        
        # Trouver la première tâche qui échoue
        first_failed_task = None
        for task_name, task_data in skills.items():
            task_passed = task_data.get("passed", 0)
            task_count = task_data.get("count", 0)
            task_crashed = task_data.get("crashed", 0)
            task_mandatory_failed = task_data.get("mandatoryFailed", 0)
            
            # Une tâche échoue si : pas tous les tests passés, ou des tests crashés, ou des échecs obligatoires
            if (task_passed < task_count and task_count > 0) or task_crashed > 0 or task_mandatory_failed > 0:
                first_failed_task = {
                    "name": task_name,
                    "passed": task_passed,
                    "count": task_count,
                    "crashed": task_crashed,
                    "mandatory_failed": task_mandatory_failed,
                    "tests": task_data.get("tests", [])
                }
                break
        
        embed = discord.Embed(
            title=f"📋 Logs Détaillés - {project_name}",
            description="Messages d'erreur de la moulinette",
            color=discord.Color.red() if first_failed_task else discord.Color.green(),
            timestamp=datetime.now()
        )
        
        if first_failed_task:
            # Construire le message d'erreur selon le type d'échec
            error_details = f"**{first_failed_task['name']}**\n"
            error_details += f"Tests: {first_failed_task['passed']}/{first_failed_task['count']}\n"
            
            if first_failed_task['crashed'] > 0:
                error_details += f"💥 **Crashed:** {first_failed_task['crashed']}\n"
            if first_failed_task['mandatory_failed'] > 0:
                error_details += f"🚫 **Mandatory Failed:** {first_failed_task['mandatory_failed']}\n"
            
            # Déterminer l'icône selon le type d'échec
            if first_failed_task['crashed'] > 0:
                icon = "💥"
                error_type = "Tâche crashée"
            elif first_failed_task['mandatory_failed'] > 0:
                icon = "🚫"
                error_type = "Échec obligatoire"
            else:
                icon = "❌"
                error_type = "Tests échoués"
            
            # Afficher les détails de la première tâche échouée
            embed.add_field(
                name=f"{icon} {error_type}",
                value=error_details,
                inline=False
            )
            
            # Afficher les détails des tests échoués de la première tâche
            failed_tests = []
            
            # Essayer de récupérer les logs depuis les détails de l'API
            if details and "externalItems" in details:
                external_items = details.get("externalItems", [])
                
                # Chercher l'item de type "trace-pool" qui contient les logs
                for item in external_items:
                    if item.get("type") == "trace-pool":
                        trace_content = item.get("comment", "")
                        
                        # Extraire les logs de la tâche échouée
                        cleaned_output = self._extract_failed_task_output(trace_content, first_failed_task['name'])
                        if cleaned_output:
                            failed_tests.append(f"```\n{cleaned_output}\n```")
                        break
            
            # Si pas de logs trouvés, essayer depuis moulinette_data
            if not failed_tests:
                for test in first_failed_task.get("tests", []):
                    if not test.get("passed", False):
                        test_output = test.get("output", "")
                        if test_output:
                            cleaned_output = self._extract_failed_task_output(test_output, first_failed_task['name'])
                            if cleaned_output:
                                failed_tests.append(f"```\n{cleaned_output}\n```")
                                break
            
            if failed_tests:
                embed.add_field(
                    name="🔍 Logs d'erreur de la première tâche",
                    value="\n\n".join(failed_tests),
                    inline=False
                )
            else:
                # Si pas de détails de tests, afficher un message générique
                embed.add_field(
                    name="🔍 Détails de l'échec",
                    value=f"Tâche **{first_failed_task['name']}** échouée\n"
                          f"Tests passés: {first_failed_task['passed']}/{first_failed_task['count']}\n"
                          f"Pour plus de détails, consultez le rapport complet sur EpiTest",
                    inline=False
                )
        else:
            embed.add_field(
                name="✅ Aucune erreur",
                value="Toutes les tâches ont réussi",
                inline=False
            )
        
        # Résumé des compétences
        skills_summary = []
        for task_name, task_data in list(skills.items())[:10]:  # Limiter à 10
            task_passed = task_data.get("passed", 0)
            task_count = task_data.get("count", 0)
            task_crashed = task_data.get("crashed", 0)
            
            if task_passed == task_count and task_count > 0:
                icon = "✅"
            elif task_crashed > 0:
                icon = "💥"
            elif task_passed > 0:
                icon = "⚠️"
            else:
                icon = "❌"
            
            skills_summary.append(f"{icon} **{task_name}**: {task_passed}/{task_count}")
        
        if skills_summary:
            embed.add_field(
                name="📊 Résumé des tâches",
                value="\n".join(skills_summary),
                inline=False
            )
        
        embed.set_footer(text="MouliCord • Logs détaillés avec messages d'erreur")
        await interaction.followup.send(embed=embed, ephemeral=True)


class PaginatedResultsView(discord.ui.View):
    """Vue avec pagination pour les résultats"""
    
    def __init__(self, results: list, page_size: int = 10):
        super().__init__(timeout=300)
        self.results = results
        self.page_size = page_size
        self.current_page = 0
        self.max_pages = (len(results) - 1) // page_size + 1
        
        # Mettre à jour les boutons
        self.update_buttons()
    
    def update_buttons(self):
        """Met à jour l'état des boutons de pagination"""
        self.clear_items()
        
        # Bouton Précédent
        prev_button = discord.ui.Button(
            label="⬅️ Précédent",
            style=discord.ButtonStyle.secondary,
            disabled=self.current_page == 0
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # Bouton Page actuelle
        page_button = discord.ui.Button(
            label=f"📄 {self.current_page + 1}/{self.max_pages}",
            style=discord.ButtonStyle.primary,
            disabled=True
        )
        self.add_item(page_button)
        
        # Bouton Suivant
        next_button = discord.ui.Button(
            label="Suivant ➡️",
            style=discord.ButtonStyle.secondary,
            disabled=self.current_page >= self.max_pages - 1
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
    
    def get_current_page_results(self):
        """Retourne les résultats de la page actuelle"""
        start = self.current_page * self.page_size
        end = start + self.page_size
        return self.results[start:end]
    
    async def previous_page(self, interaction: discord.Interaction):
        """Page précédente"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await self.update_embed(interaction)
    
    async def next_page(self, interaction: discord.Interaction):
        """Page suivante"""
        if self.current_page < self.max_pages - 1:
            self.current_page += 1
            self.update_buttons()
            await self.update_embed(interaction)
    
    async def update_embed(self, interaction: discord.Interaction):
        """Met à jour l'embed avec la page actuelle"""
        # Cette méthode sera surchargée par les classes filles
        pass

class HistoryPaginatedView(PaginatedResultsView):
    """Vue paginée pour l'historique des projets"""
    
    def __init__(self, epitech_api: EpitechAPI, projects_list: list):
        super().__init__(projects_list, page_size=15)
        self.epitech_api = epitech_api
    
    def get_embed(self):
        """Retourne l'embed pour la page actuelle"""
        current_projects = self.get_current_page_results()
        
        # Calculer les statistiques globales
        total_projects = len(self.results)
        avg_score = sum(p.get("avg_score", 0) for p in self.results) / len(self.results) if self.results else 0
        
        # Couleur dynamique basée sur la moyenne
        color = self._get_performance_color(int(avg_score))
        
        embed = discord.Embed(
            title="📈 Historique des Projets",
            description=f"**Page {self.current_page + 1}/{self.max_pages}** • {len(current_projects)} projets affichés\n\n"
                       f"📊 **{total_projects} projets** au total • Moyenne: **{avg_score:.1f}%**",
            color=color,
            timestamp=datetime.now()
        )
        
        # Ajouter les projets de la page actuelle
        for i, project in enumerate(current_projects, start=self.current_page * self.page_size + 1):
            project_name = project.get("name", "N/A")
            module_code = project.get("module", "N/A")
            avg_score = project.get("avg_score", 0)
            total_runs = project.get("total_runs", 0)
            
            # Emoji et couleur selon la performance
            emoji = self._get_performance_emoji(int(avg_score))
            
            embed.add_field(
                name=f"{emoji} {i}. {project_name}",
                value=f"**Module:** {module_code}\n"
                      f"**Score moyen:** {avg_score:.1f}%\n"
                      f"**Moulinettes:** {total_runs}",
                inline=True
            )
        
        embed.set_footer(text="MouliCord • Navigation avec les boutons ci-dessous")
        return embed
    
    def _get_performance_color(self, score: int) -> discord.Color:
        """Retourne une couleur selon le score de performance"""
        if score >= 90:
            return discord.Color.green()
        elif score >= 70:
            return discord.Color.yellow()
        elif score >= 50:
            return discord.Color.orange()
        else:
            return discord.Color.red()
    
    def _get_performance_emoji(self, score: int) -> str:
        """Retourne un emoji selon le score de performance"""
        if score >= 90:
            return "🟢"
        elif score >= 70:
            return "🟡"
        elif score >= 50:
            return "🟠"
        else:
            return "🔴"
    
    async def update_embed(self, interaction: discord.Interaction):
        """Met à jour l'embed avec la page actuelle"""
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=self)

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
                    {"name": "`/results`", "value": "📊 Derniers résultats avec actualisation", "inline": False},
                    {"name": "`/history`", "value": "📈 Sélection projet + pagination + couleurs dynamiques", "inline": False},
                    {"name": "`/stats`", "value": "📈 Statistiques complètes", "inline": False},
                    {"name": "`/logs`", "value": "📋 Logs d'erreur des moulinettes", "inline": False},
                    {"name": "`/export`", "value": "📊 Export des données en CSV/JSON/PDF", "inline": False}
                ]
            },
            {
                "title": "🔧 Commandes Système",
                "description": "**Gestion et configuration du bot:**",
                "fields": [
                    {"name": "`/status`", "value": "📊 État du bot, API et token", "inline": False},
                    {"name": "`/check_now`", "value": "🔄 Vérification immédiate", "inline": False},
                    {"name": "`/token`", "value": "🔐 Vérification + actualisation du token", "inline": False}
                ]
            },
            {
                "title": "💾 Gestion des Données", 
                "description": "**Sauvegarde et maintenance:**",
                "fields": [
                    
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
        
        # Mettre à jour l'état des boutons initialement
        self.update_buttons()
    
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
    
    def update_buttons(self):
        """Met à jour l'état des boutons de navigation"""
        # Note: Les boutons sont mis à jour dans les méthodes callback individuelles
    
    @discord.ui.button(label="◀️ Précédent", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Suivant ▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()


async def setup(bot: commands.Bot):
    """Fonction pour charger le Cog"""
    # Ne jamais lire un token depuis l'environnement; initialiser avec un token temporaire
    token = "dummy_token"
    try:
        epitech_api = EpitechAPI(token, "results_history.json")
        await bot.add_cog(MouliCordSlashCommands(bot, epitech_api))
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de l'API: {e}")
        # Utiliser un token dummy en cas d'erreur
        epitech_api = EpitechAPI("dummy_token", "results_history.json")
        await bot.add_cog(MouliCordSlashCommands(bot, epitech_api))