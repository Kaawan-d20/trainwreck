from interactions import Client, slash_command, SlashContext, OptionType, slash_option, SlashCommandChoice, Permissions, Embed, EmbedFooter, User, contexts, Extension, Button, ButtonStyle, ActionRow
from datetime import datetime, date, timedelta
import os

from TrainWreck import get_ics, get_embeds
from Enums import Subscription, RoleEnum, colors
from UserBase import get_user_base
from Calendar import get_calendar
from Tool import get_tool
from Filter import *


class MySlashCommand(Extension):
    """Classe contenant les commandes."""
    def __init__(self, bot: Client):
        self.bot = bot
        self.tool = get_tool(bot)

    @slash_command(name="wipe", description="Enlève tout les rôles.")
    async def wipe(self, ctx: SlashContext) -> None:
        """Fonction qui permet d'enlever tous les attribués"""
        await ctx.send("La commande est shunté pour des raisons de sécurité.", ephemeral=False)
        return
        for user in ctx.guild.members:
            for filiere in Filiere:
                if filiere in [Filiere.UKNW]:
                    continue
                if user.has_role(self.tool.get_roles()[filiere]):
                    print(user.display_name, " supp ", filiere)
                    #await user.remove_role(self.tool.get_roles()[filiere])
            for group in Group:
                if group in [Group.CM, Group.UKNW]:
                    continue
                if user.has_role(self.tool.get_roles()[group]):
                    print(user.display_name, " supp ", group)
                    #await user.remove_role(self.tool.get_roles()[group])
        await ctx.send("Les membres du serveur n'ont plus de rôle.", ephemeral=False)

    @slash_command(name="get_day", description="Envoie votre EDT pour un jour donné. Si une personne est donnée, donne le sien.")
    @slash_option(
        name="jour",
        description="Quel jour ? (DD-MM-YYYY)",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="personne",
        description="Quel utilisateur ?",
        required=False,
        opt_type=OptionType.USER
    )
    async def get_day(self, ctx: SlashContext, jour: str, personne: User = None) -> None:
        """Fonction qui permet d'obtenir l'EDT d'une journée spécifique, ou d'un autre utilisateur s'il est spécifié."""
        await self.tool.get_day_bt(ctx, jour, False, personne)

    @slash_command(name="today", description="Envoie votre EDT du jour.")
    async def today(self, ctx: SlashContext) -> None:
        """Fonction qui permet d'obtenir l'EDT d'aujourd'hui."""
        await self.tool.get_day_bt(ctx, date.today().strftime("%d-%m-%Y"), False)

    @slash_command(name="tomorrow", description="Envoie votre EDT de demain.")
    async def tomorrow(self, ctx: SlashContext) -> None:
        """Fonction qui permet d'obtenir l'EDT de demain."""
        await self.tool.get_day_bt(ctx, (date.today() + timedelta(days=1)).strftime("%d-%m-%Y"), False)

    @slash_command(name="get_week", description="Envoie votre EDT pour la semaine de la date. Si une personne est donnée, donne le sien.")
    @slash_option(
        name="semaine",
        description="Quel semaine ? (DD-MM-YYYY)",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="personne",
        description="Quel utilisateur ?",
        required=False,
        opt_type=OptionType.USER
    )
    async def get_week(self, ctx: SlashContext, semaine: str, personne: User = None) -> None:
        """Fonction qui permet d'obtenir l'EDT d'une semaine spécifique, ou d'un autre utilisateur s'il est spécifié."""
        await self.tool.get_week_bt(ctx, semaine, False, personne)

    @slash_command(name="week", description="Envoie votre EDT de la semaine.")
    async def week(self, ctx: SlashContext) -> None:
        """Fonction qui permet d'obtenir l'EDT de cette semaine."""
        await self.tool.get_week_bt(ctx, date.today().strftime("%d-%m-%Y"), False)

    @slash_command(name="userscan", description="Permet d'ajouter tout les membres dans la BD.", default_member_permissions=Permissions.ADMINISTRATOR)
    @contexts(guild=True, bot_dm=False)
    async def userscan(self, ctx: SlashContext) -> None:
        """Permet de scanner tous les membres du serveur et de mettre à jour la BD."""
        user_base = get_user_base()
        for user in ctx.guild.members:
            if not user_base.has_user(user.id):
                user_base.add_user(user.id, self.tool.get_groupes_as_list(user), self.tool.get_filiere_as_filiere(user))
            else:
                user_base.update_user(user.id, self.tool.get_groupes_as_list(user), self.tool.get_filiere_as_filiere(user))
        await ctx.send("Les membres du serveur ont été ajoutée et mit à jour.", ephemeral=True)

    @slash_command(name="help", description="Affiche la page d'Aide.")
    async def help(self, ctx: SlashContext) -> None:
        """Affiche le Contenu de HELP.md."""
        with open("data/HELP.md", "r", encoding="utf-8") as f:
            help_file = f.read()

        embed = Embed(description=help_file, footer=EmbedFooter(
            "Les EDT sont fournis a titre informatif uniquement -> Veuillez vous référer à votre page personnelle sur l'ENT.",
            self.bot.user.avatar_url), color=colors[2])

        repo = Button(
            style=ButtonStyle.URL,
            label="Repository bot",
            url="https://github.com/Kaawan-d20/trainwreck"
        )

        vincent = Button(
            style=ButtonStyle.URL,
            label="Github Vincent",
            url="https://github.com/VincentGonnet"
        )

        action_row = ActionRow(repo, vincent)
        ephemeral = False
        if self.tool.is_guild_chan(ctx.author):
            ephemeral = not ctx.author.has_role(self.tool.get_roles()[RoleEnum.ADMIN]) # Permanent pour les admins, mais pas pour les autres
        await ctx.send(embed=embed, components=action_row, ephemeral=ephemeral)

    @slash_command(name="ics", description="Envoie un fichier ICS importable dans la plupart des applications de calendrier.")
    @slash_option(
        name="debut",
        description="Quelle est la date de début ? (DD-MM-YYYY)",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="fin",
        description="Quelle est la date de fin ? (DD-MM-YYYY)",
        required=True,
        opt_type=OptionType.STRING
    )
    async def ics(self, ctx: SlashContext, debut: str, fin: str) -> None:
        """Génère le fichier ICS entre deux dates."""
        try:
            date_debut = datetime.strptime(debut, "%d-%m-%Y").date()
            date_fin = datetime.strptime(fin, "%d-%m-%Y").date()
            filename = f"output/{ctx.author.id}"
            get_ics(filter_events(get_calendar().get_events(),
                                  [TimeFilter(date_debut, Timing.AFTER), TimeFilter(date_fin, Timing.BEFORE),
                                   self.tool.get_filiere(ctx.author), self.tool.get_groupes(ctx.author)]),
                    filename=filename
                    )
            await ctx.send("Voici votre fichier ics (:warning: : Le calendrier n'est pas mis a jour dynamiquement)", files=[f"{filename}.ics"], ephemeral=self.tool.is_guild_chan(ctx.author))
            os.remove(f"{filename}.ics")
        except ValueError:
            await ctx.send(embeds=[self.tool.create_error_embed(f"La valeur `{debut}` ou `{fin}` ne correspond pas à une date.")], ephemeral=True)

    @slash_command(name="subscribe",
                   description="Vous permet de vous abonner à l'envoi de l'EDT dans vos DM, de manière quotidienne ou hebdomadaire.")
    @slash_option(
        name="service",
        description="Mise a jour Quotidienne `DAILY`, Hebdomadaire `WEEKLY`, ou les deux `BOTH`.",
        required=True,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Daily", value="DAILY"),
            SlashCommandChoice(name="Weekly", value="WEEKLY"),
            SlashCommandChoice(name="Both", value="BOTH")
        ]
    )
    async def subscribe(self, ctx: SlashContext, service: str) -> None:
        """Permet de s'abonnée à l'envoi automatique de l'EDT."""
        user_base = get_user_base()
        id = ctx.author_id
        if not user_base.has_user(ctx.author_id):
            user_base.add_user(id, self.tool.get_groupes_as_list(ctx.author), self.tool.get_filiere_as_filiere(ctx.author))
        match service:
            case "DAILY":
                user_base.user_subscribe(id, Subscription.DAILY)
            case "WEEKLY":
                user_base.user_subscribe(id, Subscription.WEEKLY)
            case "BOTH":
                user_base.user_subscribe(id, Subscription.BOTH)
        await ctx.send(
            embed=Embed(f"Abonnements de {ctx.author.display_name}",
                f"- Mise à Jour Quotidienne : {'✅' if (user_base.is_user_subscribed(id, Subscription.DAILY)) else '❌'}\n"
                f"- Mise à Jour Hebdomadaire : {'✅' if (user_base.is_user_subscribed(id, Subscription.WEEKLY)) else '❌'}"),
            ephemeral=self.tool.is_guild_chan(ctx.author))

    @slash_command(name="unsubscribe", description="Vous permet de vous désabonner à l'envoi de l'EDT dans vos DM.")
    @slash_option(
        name="service",
        description="mise a jour Quotidienne `DAILY`, Hebdomadaire `WEEKLY`, ou les deux `BOTH`.",
        required=True,
        opt_type=OptionType.STRING,
        choices=[
            SlashCommandChoice(name="Daily", value="DAILY"),
            SlashCommandChoice(name="Weekly", value="WEEKLY"),
            SlashCommandChoice(name="Both", value="BOTH")
        ]
    )
    async def unsubscribe(self, ctx: SlashContext, service: str) -> None:
        """Permet de se désabonnée à l'envoi automatique de l'EDT."""
        user_base = get_user_base()
        id = ctx.author_id
        if not user_base.has_user(ctx.author_id):
            user_base.add_user(id, self.tool.get_groupes_as_list(ctx.author), self.tool.get_filiere_as_filiere(ctx.author))
        match service:
            case "DAILY":
                user_base.user_unsubscribe(id, Subscription.DAILY)
            case "WEEKLY":
                user_base.user_unsubscribe(id, Subscription.WEEKLY)
            case "BOTH":
                user_base.user_unsubscribe(id, Subscription.BOTH)
        await ctx.send(
            embed=Embed(f"Abonnements de {ctx.author.display_name}",
                f"- Mise à Jour Quotidienne : {'✅' if (user_base.is_user_subscribed(id, Subscription.DAILY)) else '❌'}\n"
                f"- Mise à Jour Hebdomadaire : {'✅' if (user_base.is_user_subscribed(id, Subscription.WEEKLY)) else '❌'}"),
            ephemeral=self.tool.is_guild_chan(ctx.author)
        )

    @slash_command(name="check_subscription",
                   description="Vous permet de consulter à quels service d'envoi d'EDT vous êtes inscrit.")
    async def check_subscription(self, ctx: SlashContext) -> None:
        """Permet d'afficher quel sont les abonnements d'un utilisateur."""
        user_base = get_user_base()
        id = ctx.author_id
        await ctx.send(
            embed=Embed(f"Abonnements de {ctx.author.display_name}",
                f"- Mise à Jour Quotidienne : {'✅' if (user_base.is_user_subscribed(id, Subscription.DAILY)) else '❌'}\n"
                f"- Mise à Jour Hebdomadaire : {'✅' if (user_base.is_user_subscribed(id, Subscription.WEEKLY)) else '❌'}"),
            ephemeral=self.tool.is_guild_chan(ctx.author)
        )

    @slash_command(name="exam", description="Vous permet de consulter la liste des exams.")
    async def exam(self, ctx: SlashContext) -> None:
        exams = get_calendar().get_exams()
        embeds = get_embeds(exams, ctx.author)
        if not exams:
            embeds[0].description = "Aucun examens"
        embeds.insert(0, Embed(title="EXAMENS", description="ATTENTION CETTE LISTE D'EXAMS N'EST PEUT ÊTRE PAS A JOUR MERCI DE VERIFIER SUR LE SITE DE L'UNIVERSITÉ!", color=colors[0]))

        universite = Button(
            style=ButtonStyle.URL,
            label="Site de l'université",
            url="https://www.univ-orleans.fr/fr/sciences-techniques/etudiant/examens-reglementationrse/examens-20232024"
        )

        await ctx.send(embeds=embeds, components=universite, ephemeral=self.tool.is_guild_chan(ctx.author))
