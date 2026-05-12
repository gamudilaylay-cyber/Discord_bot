import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import random
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

RANKING_CHANNEL_ID    = 1502347495332905111
TICKET_PANEL_KANAL_ID = 1502350869113339984
TEAM_ROLLE_NAME       = "{{{UCN HAUPT SERVER TEAM}}}"
KUNDE_LOG_KANAL_ID    = 1503717981547532408

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="§", intents=intents)

# ── In-Memory Storage ──────────────────────────────────────────────
warns = {}
decknamen = {}
operationen = {}
fahndungen = {}
verhöre = []
sabotagen = []
spion_meldungen = []
aktivität = {}
aufträge = {}
bot_start_time = datetime.utcnow()

SPION_ZITATE = [
    "\"Ein guter Agent hinterlässt keine Spuren.\"",
    "\"Vertraue niemandem — nicht einmal dir selbst.\"",
    "\"Information ist die mächtigste Waffe.\"",
    "\"Im Schatten liegt die Macht.\"",
    "\"Jeder hat Geheimnisse. Wir kennen sie alle.\"",
    "\"Die beste Tarnung ist ein ehrliches Gesicht.\"",
    "\"Schweigen ist Gold — Reden ist gefährlich.\"",
    "\"Ein Spion ohne Auftrag ist ein toter Spion.\"",
    "\"Verrat beginnt immer mit einem Lächeln.\"",
    "\"Wir existieren nicht — aber wir sind überall.\"",
]
ACHT_BALL_ANTWORTEN = [
    "✅ Ja, definitiv.", "✅ Ohne Zweifel.", "✅ Mit Sicherheit.",
    "✅ Sehr wahrscheinlich.", "🟡 Frag später nochmal.", "🟡 Nicht sicher.",
    "🟡 Schwer zu sagen.", "❌ Glaube ich nicht.", "❌ Nein.", "❌ Auf keinen Fall.",
]
MISSIONS_POOL = [
    "Beschaffe Informationen über Zielperson Alpha",
    "Infiltriere das feindliche Lager unbemerkt",
    "Sichere den Geheimcode aus der Botschaft",
    "Überwache Verdächtigen für 24 Stunden",
    "Stelle eine Verbindung zum Informanten her",
    "Deaktiviere das feindliche Kommunikationssystem",
    "Rette den gefangenen Agenten aus Zone 7",
    "Platziere einen Peilsender am Zielfahrzeug",
    "Stehle die Baupläne aus dem Hauptquartier",
    "Eliminiere die feindliche Drohnenstation",
    "Sichere den Fluchtwagen in Sektor 4",
    "Entschlüssele das abgefangene Signal",
    "Überbringe das Paket ohne Verfolgung",
    "Lass keinen Zeugen zurück",
    "Identifiziere den Maulwurf im Team",
]

# ── Channel ID Registry (filled by /setup_server) ──────────────────
kanäle = {
    "verwarnungen":   None,
    "fahndungen":     None,
    "operationen":    None,
    "sabotagen":      None,
    "verhöre":        None,
    "spion-meldungen": None,
    "hack-logs":      None,
    "polizei-funk":   None,
    "gang-funk":      None,
    "aktivität-log":  None,
}

TEAM_ROLLE = TEAM_ROLLE_NAME

KANAL_CONFIG = [
    (
        "📋・verwarnungen", "verwarnungen",
        "Verwarnungen, Kicks & Bans werden hier automatisch geloggt",
        "⚠️ **Verwarnungen**\nHier landen alle Moderationsaktionen automatisch:\n"
        "• `/warn` — Verwarnung eines Mitglieds\n"
        "• `/unwarn` — Verwarnung entfernen\n"
        "• `/kick` — Kick-Protokoll\n"
        "• `/ban` — Ban-Protokoll\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "🚨・fahndungen", "fahndungen",
        "Aktive Fahndungsaufrufe und Aufhebungen",
        "🚨 **Fahndungen**\nAlle aktiven Fahndungsaufrufe erscheinen hier automatisch:\n"
        "• `/fahndung @member grund` — Fahndung starten\n"
        "• `/fahndung_aufheben @member` — Fahndung aufheben\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "🎯・operationen", "operationen",
        "Geheime Operationen und deren Status",
        "🎯 **Operationen**\nAlle geheimen Operationen werden hier protokolliert:\n"
        "• `/operation name beschreibung` — Neue Operation starten\n"
        "• `/operationen` — Alle Operationen anzeigen\n"
        "• `/operation_abschliessen name` — Operation beenden\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "💣・sabotagen", "sabotagen",
        "Sabotage-Aktionen aller Agenten",
        "💣 **Sabotagen**\nJede Sabotage-Aktion wird hier automatisch eingetragen:\n"
        "• `/sabotage ziel beschreibung` — Sabotage loggen\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "🔒・verhöre", "verhöre",
        "Verhörprotokolle und Befragungen",
        "🔒 **Verhöre**\nAlle Verhörprotokolle landen automatisch hier:\n"
        "• `/verhör @verdächtiger grund` — Verhör einleiten\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "🕵️・spion-meldungen", "spion-meldungen",
        "Meldungen über verdächtige Spione",
        "🕵️ **Spion-Meldungen**\nGemeldete Spione werden hier protokolliert:\n"
        "• `/spion_melden @member info` — Verdächtigen melden\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "💻・hack-logs", "hack-logs",
        "Hack, Scan und Spy RP-Aktionen",
        "💻 **Hack-Logs**\nAlle RP-Systemaktionen werden hier geloggt:\n"
        "• `/hack @ziel` — Fake Hack-Terminal\n"
        "• `/scan @ziel` — Netzwerk-Scan\n"
        "• `/spy @ziel` — Spionagebericht\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "🚔・polizei-funk", "polizei-funk",
        "Polizei-Alarme und Einsatzmeldungen",
        "🚔 **Polizei-Funk**\nAlle Polizei-Alarme kommen automatisch hier an:\n"
        "• `/polizei_alarm nachricht` — Alarm an Polizei-Rolle senden\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "🔫・gang-funk", "gang-funk",
        "Gang-Alarme und interne Meldungen",
        "🔫 **Gang-Funk**\nAlle Gang-Alarme kommen automatisch hier an:\n"
        "• `/gang_alarm nachricht` — Alarm an Gang-Rolle senden\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
    (
        "📊・aktivität-log", "aktivität-log",
        "Mitglieder-Joins und Aktivitätsereignisse",
        "📊 **Aktivitäts-Log**\nMitglieder-Events werden hier automatisch protokolliert:\n"
        "• Neues Mitglied beigetreten\n"
        "• Nickname-Tarnungen\n"
        "• Bot-Statusmeldungen\n\n"
        "_Nur für `UCN HAUPT SERVER TEAM` sichtbar._"
    ),
]

# ── Helpers ────────────────────────────────────────────────────────
def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")

def warn_count(user_id):
    return len(warns.get(user_id, []))

async def log_to(key: str, embed: discord.Embed):
    cid = kanäle.get(key)
    if not cid:
        return
    kanal = bot.get_channel(cid)
    if kanal:
        try:
            await kanal.send(embed=embed)
        except Exception:
            pass

def fake_ip():
    return f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def fake_id():
    return ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12))

def fake_hash():
    return ''.join(random.choices("abcdef0123456789", k=40))

HACK_STUFEN = ["FIREWALL BYPASS", "PORT SCAN", "AUTH INJECTION", "ROOT ACCESS", "DATEN-EXTRAKTION"]
SCAN_PORTS = [22, 80, 443, 3306, 8080, 8443, 27017, 5432]
SPION_STANDORTE = ["Hamburg Altona", "Hamburg Mitte", "Reeperbahn", "Speicherstadt", "HafenCity", "Barmbek", "Eimsbüttel"]
SPION_FAHRZEUGE = ["Schwarzer Audi A6", "Weißer Mercedes E-Klasse", "Grauer BMW 5er", "Dunkelblauer VW Passat"]
SPION_STATUS = ["Aktiv im Feld", "Unter Beobachtung", "Tarnung intakt", "Verdächtig", "Gefährdet"]

# ══════════════════════════════════════════════════════════════════
# TICKET SYSTEM — Views & Logic
# ══════════════════════════════════════════════════════════════════

TICKET_KATEGORIEN = [
    discord.SelectOption(label="🆘 Support",           value="support",    description="Technische Hilfe oder ein Problem melden",        emoji="🆘"),
    discord.SelectOption(label="📝 Bewerbung",         value="bewerbung",  description="Bewirb dich bei unserem Team",                    emoji="📝"),
    discord.SelectOption(label="🚨 Meldung",           value="meldung",    description="Spieler oder Vorfall melden",                     emoji="🚨"),
    discord.SelectOption(label="💬 Beschwerde",        value="beschwerde", description="Beschwerde über ein Mitglied einreichen",         emoji="💬"),
    discord.SelectOption(label="❓ Allgemeine Anfrage", value="anfrage",    description="Sonstige Fragen an das Team",                     emoji="❓"),
]

TICKET_NAMEN = {
    "support":    "🆘 Support",
    "bewerbung":  "📝 Bewerbung",
    "meldung":    "🚨 Meldung",
    "beschwerde": "💬 Beschwerde",
    "anfrage":    "❓ Allgemeine Anfrage",
}

offene_tickets = {}  # {user_id: channel_id}

class TicketSchließenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Ticket schließen",
        style=discord.ButtonStyle.danger,
        custom_id="ucn_ticket_schliessen"
    )
    async def schliessen(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Ticket wird geschlossen...",
            description=f"Geschlossen von {interaction.user.mention}",
            color=discord.Color.red()
        )
        embed.set_footer(text=now_str())
        await interaction.response.send_message(embed=embed)
        for uid, cid in list(offene_tickets.items()):
            if cid == interaction.channel.id:
                del offene_tickets[uid]
                break
        await interaction.channel.delete(reason=f"Ticket geschlossen von {interaction.user.display_name}")

class TicketAuswahl(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="📋 Kategorie auswählen...",
            min_values=1,
            max_values=1,
            options=TICKET_KATEGORIEN,
            custom_id="ucn_ticket_auswahl"
        )

    async def callback(self, interaction: discord.Interaction):
        kategorie = self.values[0]
        guild = interaction.guild
        member = interaction.user

        if member.id in offene_tickets:
            existierender = guild.get_channel(offene_tickets[member.id])
            if existierender:
                await interaction.response.send_message(
                    f"❌ Du hast bereits ein offenes Ticket: {existierender.mention}",
                    ephemeral=True
                )
                return

        team_rolle = discord.utils.get(guild.roles, name=TEAM_ROLLE_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True, embed_links=True),
        }
        if team_rolle:
            overwrites[team_rolle] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )

        ticket_kat = discord.utils.get(guild.categories, name="🎫 TICKETS")
        if not ticket_kat:
            ticket_kat = await guild.create_category("🎫 TICKETS")

        kanal_name = f"ticket-{member.name.lower().replace(' ', '-')}-{kategorie}"
        ticket_kanal = await guild.create_text_channel(
            name=kanal_name,
            category=ticket_kat,
            topic=f"Ticket von {member.display_name} | Kategorie: {TICKET_NAMEN[kategorie]}",
            overwrites=overwrites
        )

        offene_tickets[member.id] = ticket_kanal.id

        embed = discord.Embed(
            title=f"🎫 {TICKET_NAMEN[kategorie]}",
            description=(
                f"Willkommen {member.mention}!\n\n"
                f"Dein Ticket wurde erfolgreich erstellt.\n"
                f"Das **{TEAM_ROLLE_NAME}** wird sich so schnell wie möglich bei dir melden.\n\n"
                f"**Kategorie:** {TICKET_NAMEN[kategorie]}\n"
                f"**Erstellt am:** {now_str()}\n\n"
                f"Bitte beschreibe dein Anliegen so genau wie möglich."
            ),
            color=discord.Color.dark_gold()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="UCN Bot — Notruf Hamburg RP")

        team_erwähnung = team_rolle.mention if team_rolle else f"@{TEAM_ROLLE_NAME}"
        await ticket_kanal.send(
            content=f"{member.mention} | {team_erwähnung}",
            embed=embed,
            view=TicketSchließenView()
        )

        await interaction.response.send_message(
            f"✅ Dein Ticket wurde erstellt: {ticket_kanal.mention}",
            ephemeral=True
        )

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketAuswahl())

# ══════════════════════════════════════════════════════════════════
# KUNDENANFRAGE — Modal
# ══════════════════════════════════════════════════════════════════

class KundenAnfrageModal(discord.ui.Modal, title="📩 Kundenanfrage"):
    anliegen = discord.ui.TextInput(
        label="Was brauchst du?",
        placeholder="Beschreibe dein Anliegen so genau wie möglich...",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=500,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        team_rolle = discord.utils.get(guild.roles, name=TEAM_ROLLE_NAME)
        team_erwähnung = team_rolle.mention if team_rolle else f"@{TEAM_ROLLE_NAME}"

        embed = discord.Embed(
            title="📩 NEUE KUNDENANFRAGE",
            description=(
                f"Ein Mitglied hat eine Anfrage gestellt und wartet auf Hilfe.\n\n"
                f"**📋 Anliegen:**\n{self.anliegen.value}"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Anfrage von", value=interaction.user.mention, inline=True)
        embed.add_field(name="📅 Zeitpunkt", value=now_str(), inline=True)
        embed.add_field(name="📍 Kanal", value=interaction.channel.mention, inline=True)
        embed.set_footer(text="UCN Bot — Notruf Hamburg RP")

        await interaction.response.send_message(
            content=f"📣 {team_erwähnung} — Neue Kundenanfrage!",
            embed=embed
        )

        # Log-Kanal: per fester ID
        log_kanal = bot.get_channel(KUNDE_LOG_KANAL_ID)

        if log_kanal:
            log_embed = discord.Embed(
                title="📋 KUNDENANFRAGE PROTOKOLLIERT",
                description=self.anliegen.value,
                color=discord.Color.dark_gold(),
                timestamp=datetime.utcnow()
            )
            log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
            log_embed.add_field(name="👤 Mitglied", value=f"{interaction.user.mention} (`{interaction.user}`)", inline=True)
            log_embed.add_field(name="📅 Zeit", value=now_str(), inline=True)
            log_embed.add_field(name="📍 Gesendet in", value=interaction.channel.mention, inline=True)
            log_embed.set_footer(text=f"ID: {interaction.user.id} • UCN Bot")
            await log_kanal.send(embed=log_embed)

# ── Auto Ranking Task ──────────────────────────────────────────────
@tasks.loop(hours=1)
async def auto_ranking():
    if not aktivität:
        return
    kanal = bot.get_channel(RANKING_CHANNEL_ID)
    if not kanal:
        return
    sortiert = sorted(aktivität.items(), key=lambda x: x[1]["punkte"], reverse=True)[:10]
    medaillen = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    embed = discord.Embed(title="🏆 UCN TOP AGENTEN — Stündliches Update", color=discord.Color.gold())
    beschreibung = ""
    for i, (uid, daten) in enumerate(sortiert):
        beschreibung += (
            f"{medaillen[i]} **{daten['name']}**\n"
            f"    ┣ 💠 Punkte: `{daten['punkte']}`\n"
            f"    ┗ 💬 Nachrichten: `{daten['nachrichten']}`\n"
        )
    embed.description = beschreibung
    embed.set_footer(text=f"Automatisches Update • {now_str()}")
    await kanal.send(embed=embed)

# ── Kundenlog Reset (alle 6 Stunden) ───────────────────────────────
@tasks.loop(hours=6)
async def kundenlog_reset():
    kanal = bot.get_channel(KUNDE_LOG_KANAL_ID)
    if not kanal:
        return
    try:
        await kanal.purge(limit=None)
    except discord.Forbidden:
        return
    embed = discord.Embed(
        title="🔄 LOG ERNEUERT",
        description=(
            "Dieser Kanal wurde automatisch zurückgesetzt.\n"
            "Neue Kundenanfragen werden ab jetzt hier geloggt."
        ),
        color=discord.Color.dark_gold(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"Nächste Erneuerung in 6 Stunden • UCN Bot")
    await kanal.send(embed=embed)

# ── Events ─────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    bot.add_view(TicketPanelView())
    bot.add_view(TicketSchließenView())
    app_info = await bot.application_info()
    bot.owner_id = app_info.owner.id
    print(f"✅ Bot online als {bot.user}")
    print(f"✅ Eigentümer: {app_info.owner} (ID: {bot.owner_id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash-Befehle synchronisiert")
    except Exception as e:
        print(f"⚠️ Sync fehlgeschlagen (Discord temporär nicht erreichbar): {e}")
    if not auto_ranking.is_running():
        auto_ranking.start()
    if not kundenlog_reset.is_running():
        kundenlog_reset.start()

@bot.tree.interaction_check
async def global_owner_check(interaction: discord.Interaction) -> bool:
    # Ticket-Buttons & Dropdowns dürfen alle nutzen
    if interaction.type == discord.InteractionType.component:
        return True
    # Modal-Submissions dürfen alle nutzen (z.B. Kundenanfrage)
    if interaction.type == discord.InteractionType.modal_submit:
        return True
    # Commands die jeder nutzen darf (Kunden + Mitglieder)
    PUBLIC_COMMANDS = {
        "kunde", "hilfe", "meine_stats", "mein_rang", "münzwurf",
        "wetter_hamburg", "treffpunkt", "identität", "stadtplan",
        "ruf_taxi", "job_angebot", "zufalls_code", "tipp", "notruf",
        "ucn_info", "feedback", "ping", "uptime", "user_info",
        "avatar", "mein_profil", "mein_auftrag", "würfeln", "8ball",
        "zitat", "ranking", "bot_info", "zähle_mitglieder",
        "server_icon", "boost_info", "kanal_info", "umfrage",
        "geheimnis", "deckname",
    }
    if interaction.command and interaction.command.name in PUBLIC_COMMANDS:
        return True
    # Alle anderen Slash-Commands: nur der Bot-Eigentümer
    if interaction.user.id != bot.owner_id:
        await interaction.response.send_message(
            "❌ Nur der Bot-Eigentümer darf Befehle benutzen.",
            ephemeral=True
        )
        return False
    return True

@bot.event
async def on_member_join(member):
    try:
        await member.edit(nick=f"UCN | {member.name}")
    except Exception as e:
        print(f"Nickname-Fehler: {e}")
    log_embed = discord.Embed(title="📥 Neues Mitglied", color=discord.Color.green())
    log_embed.set_thumbnail(url=member.display_avatar.url)
    log_embed.add_field(name="Mitglied", value=f"{member.mention} (`{member.name}`)")
    log_embed.add_field(name="Account erstellt", value=member.created_at.strftime("%d.%m.%Y"))
    log_embed.set_footer(text=now_str())
    await log_to("aktivität-log", log_embed)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    uid = message.author.id
    if uid not in aktivität:
        aktivität[uid] = {"punkte": 0, "nachrichten": 0, "name": message.author.display_name}
    aktivität[uid]["punkte"] += random.randint(1, 3)
    aktivität[uid]["nachrichten"] += 1
    aktivität[uid]["name"] = message.author.display_name
    await bot.process_commands(message)

# ══════════════════════════════════════════════════════════════════
# /setup_server — Alle 10 Kanäle erstellen
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="setup_server", description="⚙️ Erstellt alle UCN-System-Kanäle mit Berechtigungen")
@app_commands.checks.has_permissions(manage_channels=True)
async def setup_server_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    team_rolle = discord.utils.get(guild.roles, name=TEAM_ROLLE)
    if not team_rolle:
        alle_rollen = "\n".join(f"• `{r.name}`" for r in guild.roles if r.name != "@everyone")
        await interaction.followup.send(
            f"❌ Rolle `{TEAM_ROLLE}` nicht gefunden!\n\n"
            f"**Verfügbare Rollen auf diesem Server:**\n{alle_rollen}\n\n"
            f"Schreib mir bitte den exakten Namen deiner Team-Rolle!",
            ephemeral=True
        )
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False,
            send_messages=False,
            read_message_history=False
        ),
        team_rolle: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            embed_links=True,
            attach_files=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            embed_links=True
        )
    }

    kategorie = discord.utils.get(guild.categories, name="🕵️ UCN SYSTEM")
    if not kategorie:
        kategorie = await guild.create_category(
            "🕵️ UCN SYSTEM",
            overwrites=overwrites
        )

    erstellt = []
    übersprungen = []

    for kanal_name, key, thema, erklärung in KANAL_CONFIG:
        vorhanden = discord.utils.get(guild.channels, name=kanal_name)
        if vorhanden:
            await vorhanden.edit(overwrites=overwrites, topic=thema)
            kanäle[key] = vorhanden.id
            übersprungen.append(kanal_name)
            continue

        neuer_kanal = await guild.create_text_channel(
            name=kanal_name,
            category=kategorie,
            topic=thema,
            overwrites=overwrites
        )
        kanäle[key] = neuer_kanal.id
        erstellt.append(kanal_name)

        erklärungs_embed = discord.Embed(
            title=f"📌 Kanal-Info — {kanal_name}",
            description=erklärung,
            color=discord.Color.dark_gold()
        )
        erklärungs_embed.set_footer(text=f"UCN Bot • {now_str()}")
        await neuer_kanal.send(embed=erklärungs_embed)

    embed = discord.Embed(title="⚙️ SERVER SETUP ABGESCHLOSSEN", color=discord.Color.green())
    if erstellt:
        embed.add_field(
            name=f"✅ Erstellt ({len(erstellt)})",
            value="\n".join(f"• {k}" for k in erstellt),
            inline=False
        )
    if übersprungen:
        embed.add_field(
            name=f"🔄 Berechtigungen aktualisiert ({len(übersprungen)})",
            value="\n".join(f"• {k}" for k in übersprungen),
            inline=False
        )
    embed.add_field(name="📁 Kategorie", value="🕵️ UCN SYSTEM", inline=False)
    embed.add_field(
        name="🔒 Berechtigungen",
        value=f"• `@everyone` — ❌ Kein Zugriff\n• `{TEAM_ROLLE}` — ✅ Sehen & Schreiben",
        inline=False
    )
    embed.set_footer(text=f"Setup von {interaction.user.display_name} • {now_str()}")
    await interaction.followup.send(embed=embed, ephemeral=True)

    log_kanal = bot.get_channel(kanäle.get("aktivität-log"))
    if log_kanal:
        willkommen = discord.Embed(
            title="🤖 UCN Bot ist bereit!",
            description=(
                "Alle System-Kanäle wurden eingerichtet und gesichert.\n\n"
                f"🔒 **Zugriff:** Nur `{TEAM_ROLLE}`\n"
                "📡 **Auto-Logging:** Aktiv für alle Bot-Aktionen\n"
                "🕵️ **Server:** Notruf Hamburg RP"
            ),
            color=discord.Color.blurple()
        )
        willkommen.set_footer(text=now_str())
        await log_kanal.send(embed=willkommen)

# ══════════════════════════════════════════════════════════════════
# MODERATION
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="warn", description="⚠️ Verwarnt ein Mitglied")
@app_commands.describe(mitglied="Wen verwarnen?", grund="Warum?")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn_cmd(interaction: discord.Interaction, mitglied: discord.Member, grund: str = "Kein Grund angegeben"):
    uid = mitglied.id
    warns.setdefault(uid, []).append(grund)
    embed = discord.Embed(title="⚠️ Verwarnung", color=discord.Color.orange())
    embed.add_field(name="Mitglied", value=mitglied.mention)
    embed.add_field(name="Grund", value=grund)
    embed.add_field(name="Gesamt-Verwarnungen", value=str(warn_count(uid)))
    embed.set_footer(text=f"Von {interaction.user.display_name} • {now_str()}")
    await interaction.response.send_message(embed=embed)
    await log_to("verwarnungen", embed)

@bot.tree.command(name="unwarn", description="✅ Entfernt die letzte Verwarnung")
@app_commands.describe(mitglied="Von wem?")
@app_commands.checks.has_permissions(manage_messages=True)
async def unwarn_cmd(interaction: discord.Interaction, mitglied: discord.Member):
    uid = mitglied.id
    if uid in warns and warns[uid]:
        warns[uid].pop()
        msg = f"✅ Letzte Verwarnung von {mitglied.mention} entfernt. Noch: {warn_count(uid)}"
        await interaction.response.send_message(msg)
        log_embed = discord.Embed(title="✅ Verwarnung entfernt", color=discord.Color.green())
        log_embed.add_field(name="Mitglied", value=mitglied.mention)
        log_embed.add_field(name="Verbleibend", value=str(warn_count(uid)))
        log_embed.set_footer(text=f"Von {interaction.user.display_name} • {now_str()}")
        await log_to("verwarnungen", log_embed)
    else:
        await interaction.response.send_message("Keine Verwarnungen vorhanden.", ephemeral=True)

@bot.tree.command(name="warns", description="📊 Zeigt Verwarnungen eines Mitglieds")
@app_commands.describe(mitglied="Wessen Verwarnungen?")
async def warns_cmd(interaction: discord.Interaction, mitglied: discord.Member):
    uid = mitglied.id
    liste = warns.get(uid, [])
    embed = discord.Embed(title=f"📊 Verwarnungen — {mitglied.display_name}", color=discord.Color.yellow())
    embed.description = "\n".join(f"`{i+1}.` {w}" for i, w in enumerate(liste)) if liste else "Keine Verwarnungen."
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kick", description="👢 Kickt ein Mitglied vom Server")
@app_commands.describe(mitglied="Wen kicken?", grund="Warum?")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_cmd(interaction: discord.Interaction, mitglied: discord.Member, grund: str = "Kein Grund"):
    await mitglied.kick(reason=grund)
    embed = discord.Embed(title="👢 Mitglied gekickt", color=discord.Color.red())
    embed.add_field(name="Mitglied", value=f"{mitglied} (`{mitglied.id}`)")
    embed.add_field(name="Grund", value=grund)
    embed.set_footer(text=f"Von {interaction.user.display_name} • {now_str()}")
    await interaction.response.send_message(embed=embed)
    await log_to("verwarnungen", embed)

@bot.tree.command(name="ban", description="🔨 Bannt ein Mitglied permanent")
@app_commands.describe(mitglied="Wen bannen?", grund="Warum?")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_cmd(interaction: discord.Interaction, mitglied: discord.Member, grund: str = "Kein Grund"):
    await mitglied.ban(reason=grund)
    embed = discord.Embed(title="🔨 Mitglied gebannt", color=discord.Color.dark_red())
    embed.add_field(name="Mitglied", value=f"{mitglied} (`{mitglied.id}`)")
    embed.add_field(name="Grund", value=grund)
    embed.set_footer(text=f"Von {interaction.user.display_name} • {now_str()}")
    await interaction.response.send_message(embed=embed)
    await log_to("verwarnungen", embed)

# ══════════════════════════════════════════════════════════════════
# AKTEN & IDENTITÄT
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="akte", description="🗂️ Zeigt die Personalakte eines Mitglieds")
@app_commands.describe(mitglied="Wessen Akte?")
async def akte_cmd(interaction: discord.Interaction, mitglied: discord.Member):
    uid = mitglied.id
    rollen = [r.name for r in mitglied.roles if r.name != "@everyone"]
    embed = discord.Embed(title=f"🗂️ PERSONALAKTE — {mitglied.display_name}", color=discord.Color.dark_gray())
    embed.set_thumbnail(url=mitglied.display_avatar.url)
    embed.add_field(name="🆔 User-ID", value=str(uid), inline=True)
    embed.add_field(name="🕵️ Deckname", value=decknamen.get(uid, "Unbekannt"), inline=True)
    embed.add_field(name="📅 Beigetreten", value=mitglied.joined_at.strftime("%d.%m.%Y") if mitglied.joined_at else "?", inline=True)
    embed.add_field(name="⚠️ Verwarnungen", value=str(warn_count(uid)), inline=True)
    embed.add_field(name="🎭 Rollen", value=", ".join(rollen) if rollen else "Keine", inline=False)
    fahndung = fahndungen.get(uid)
    embed.add_field(name="🚨 Fahndung", value=f"AKTIV — {fahndung['grund']}" if fahndung else "Keine", inline=False)
    embed.set_footer(text=f"Abgerufen von {interaction.user.display_name} • {now_str()}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="deckname", description="🕵️ Setzt deinen Spion-Decknamen")
@app_commands.describe(name="Dein Deckname")
async def deckname_cmd(interaction: discord.Interaction, name: str):
    decknamen[interaction.user.id] = name
    await interaction.response.send_message(f"🕵️ Dein Deckname wurde auf **{name}** gesetzt.", ephemeral=True)

@bot.tree.command(name="tarnung", description="🎭 Gibt einem Mitglied einen Tarnnamen")
@app_commands.describe(mitglied="Wen tarnen?", tarnname="Welcher Tarnname?")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def tarnung_cmd(interaction: discord.Interaction, mitglied: discord.Member, tarnname: str):
    alter_name = mitglied.display_name
    try:
        await mitglied.edit(nick=tarnname)
        await interaction.response.send_message(f"🎭 **{alter_name}** wurde als **{tarnname}** getarnt.", ephemeral=True)
        log_embed = discord.Embed(title="🎭 Tarnung gesetzt", color=discord.Color.greyple())
        log_embed.add_field(name="Mitglied", value=mitglied.mention)
        log_embed.add_field(name="Neuer Name", value=tarnname)
        log_embed.set_footer(text=f"Von {interaction.user.display_name} • {now_str()}")
        await log_to("aktivität-log", log_embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)

# ══════════════════════════════════════════════════════════════════
# OPERATIONEN
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="operation", description="🎯 Startet eine neue geheime Operation")
@app_commands.describe(name="Operationsname", beschreibung="Was ist das Ziel?")
async def operation_cmd(interaction: discord.Interaction, name: str, beschreibung: str):
    if name in operationen:
        await interaction.response.send_message(f"❌ Operation **{name}** existiert bereits.", ephemeral=True)
        return
    operationen[name] = {
        "beschreibung": beschreibung,
        "ersteller_id": interaction.user.id,
        "ersteller": interaction.user.display_name,
        "zeit": now_str(),
        "status": "🟢 Aktiv"
    }
    embed = discord.Embed(title=f"🎯 NEUE OPERATION: {name}", color=discord.Color.green())
    embed.add_field(name="Ziel", value=beschreibung, inline=False)
    embed.add_field(name="Initiiert von", value=interaction.user.mention, inline=True)
    embed.add_field(name="Status", value="🟢 Aktiv", inline=True)
    embed.set_footer(text=now_str())
    await interaction.response.send_message(embed=embed)
    await log_to("operationen", embed)

@bot.tree.command(name="operationen", description="📋 Listet alle laufenden Operationen")
async def operationen_cmd(interaction: discord.Interaction):
    if not operationen:
        await interaction.response.send_message("📋 Keine aktiven Operationen.", ephemeral=True)
        return
    embed = discord.Embed(title="📋 ALLE OPERATIONEN", color=discord.Color.blurple())
    for name, data in operationen.items():
        embed.add_field(
            name=f"{data['status']} {name}",
            value=f"{data['beschreibung']}\n_Von {data['ersteller']} • {data['zeit']}_",
            inline=False
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="operation_abschliessen", description="✅ Markiert eine Operation als abgeschlossen")
@app_commands.describe(name="Welche Operation?")
@app_commands.checks.has_permissions(manage_messages=True)
async def op_abschliessen_cmd(interaction: discord.Interaction, name: str):
    if name not in operationen:
        await interaction.response.send_message(f"❌ Operation **{name}** nicht gefunden.", ephemeral=True)
        return
    operationen[name]["status"] = "✅ Abgeschlossen"
    embed = discord.Embed(title=f"✅ OPERATION ABGESCHLOSSEN: {name}", color=discord.Color.teal())
    embed.add_field(name="Beschreibung", value=operationen[name]["beschreibung"])
    embed.set_footer(text=f"Abgeschlossen von {interaction.user.display_name} • {now_str()}")
    await interaction.response.send_message(embed=embed)
    await log_to("operationen", embed)

# ══════════════════════════════════════════════════════════════════
# FAHNDUNG
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="fahndung", description="🚨 Startet einen Fahndungsaufruf")
@app_commands.describe(mitglied="Wer wird gesucht?", grund="Warum?")
@app_commands.checks.has_permissions(manage_messages=True)
async def fahndung_cmd(interaction: discord.Interaction, mitglied: discord.Member, grund: str):
    fahndungen[mitglied.id] = {
        "grund": grund, "ersteller_id": interaction.user.id,
        "ersteller": interaction.user.display_name, "zeit": now_str()
    }
    embed = discord.Embed(title="🚨 FAHNDUNGSAUFRUF", color=discord.Color.red())
    embed.set_thumbnail(url=mitglied.display_avatar.url)
    embed.add_field(name="🎯 Gesuchte Person", value=f"{mitglied.mention}\n`{mitglied.display_name}`", inline=True)
    embed.add_field(name="📄 Grund", value=grund, inline=False)
    embed.add_field(name="👮 Ausgestellt von", value=interaction.user.mention, inline=True)
    embed.set_footer(text=f"Fahndung aktiv seit {now_str()}")
    await interaction.response.send_message(embed=embed)
    await log_to("fahndungen", embed)

@bot.tree.command(name="fahndung_aufheben", description="✅ Hebt eine Fahndung auf")
@app_commands.describe(mitglied="Von wem?")
@app_commands.checks.has_permissions(manage_messages=True)
async def fahndung_aufheben_cmd(interaction: discord.Interaction, mitglied: discord.Member):
    if mitglied.id in fahndungen:
        del fahndungen[mitglied.id]
        await interaction.response.send_message(f"✅ Fahndung gegen {mitglied.mention} wurde aufgehoben.")
        log_embed = discord.Embed(title="✅ Fahndung aufgehoben", color=discord.Color.green())
        log_embed.add_field(name="Person", value=mitglied.mention)
        log_embed.set_footer(text=f"Von {interaction.user.display_name} • {now_str()}")
        await log_to("fahndungen", log_embed)
    else:
        await interaction.response.send_message("Keine aktive Fahndung.", ephemeral=True)

# ══════════════════════════════════════════════════════════════════
# SPIONAGE
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="verhör", description="🔒 Leitet ein Verhör ein")
@app_commands.describe(verdächtiger="Wer wird verhört?", grund="Warum?")
@app_commands.checks.has_permissions(manage_messages=True)
async def verhör_cmd(interaction: discord.Interaction, verdächtiger: discord.Member, grund: str):
    verhöre.append({
        "täter": verdächtiger.display_name, "täter_id": verdächtiger.id,
        "beamter": interaction.user.display_name, "beamter_id": interaction.user.id,
        "grund": grund, "zeit": now_str()
    })
    embed = discord.Embed(title="🔒 VERHÖR EINGELEITET", color=discord.Color.dark_orange())
    embed.add_field(name="Verdächtiger", value=verdächtiger.mention)
    embed.add_field(name="Verhört von", value=interaction.user.mention)
    embed.add_field(name="Grund", value=grund, inline=False)
    embed.set_footer(text=now_str())
    await interaction.response.send_message(embed=embed)
    await log_to("verhöre", embed)

@bot.tree.command(name="sabotage", description="💣 Loggt eine Sabotage-Aktion")
@app_commands.describe(ziel="Was wurde sabotiert?", beschreibung="Was wurde gemacht?")
async def sabotage_cmd(interaction: discord.Interaction, ziel: str, beschreibung: str):
    sabotagen.append({
        "ziel": ziel, "täter": interaction.user.display_name,
        "täter_id": interaction.user.id, "beschreibung": beschreibung, "zeit": now_str()
    })
    embed = discord.Embed(title="💣 SABOTAGE GEMELDET", color=discord.Color.dark_red())
    embed.add_field(name="🎯 Ziel", value=ziel)
    embed.add_field(name="👤 Ausgeführt von", value=interaction.user.mention)
    embed.add_field(name="📝 Beschreibung", value=beschreibung, inline=False)
    embed.set_footer(text=now_str())
    await interaction.response.send_message(embed=embed)
    await log_to("sabotagen", embed)

@bot.tree.command(name="spion_melden", description="🕵️ Meldet ein Mitglied als verdächtigen Spion")
@app_commands.describe(mitglied="Wer ist verdächtig?", info="Was ist verdächtig?")
async def spion_melden_cmd(interaction: discord.Interaction, mitglied: discord.Member, info: str):
    spion_meldungen.append({
        "verdächtig": mitglied.display_name, "verdächtig_id": mitglied.id,
        "melder": interaction.user.display_name, "melder_id": interaction.user.id,
        "info": info, "zeit": now_str()
    })
    embed = discord.Embed(title="🕵️ SPION GEMELDET", color=discord.Color.purple())
    embed.set_thumbnail(url=mitglied.display_avatar.url)
    embed.add_field(name="Verdächtiger", value=mitglied.mention)
    embed.add_field(name="Gemeldet von", value=interaction.user.mention)
    embed.add_field(name="Hinweis", value=info, inline=False)
    embed.set_footer(text=now_str())
    await interaction.response.send_message(embed=embed)
    await log_to("spion-meldungen", embed)

@bot.tree.command(name="geheimnis", description="🔐 Sendet eine verschlüsselte Geheimbotschaft")
@app_commands.describe(nachricht="Die geheime Nachricht")
async def geheimnis_cmd(interaction: discord.Interaction, nachricht: str):
    embed = discord.Embed(title="🔐 VERSCHLÜSSELTE NACHRICHT", color=discord.Color.dark_gray())
    embed.description = f"||{nachricht}||"
    embed.set_footer(text=f"Von einem anonymen Agenten • {now_str()}")
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════════════════════════
# ALARME
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="polizei_alarm", description="🚔 Sendet einen Alarm an die Polizei-Rolle")
@app_commands.describe(nachricht="Was ist der Notfall?", rolle="Rollenname (Standard: Polizei)")
async def polizei_alarm_cmd(interaction: discord.Interaction, nachricht: str, rolle: str = "Polizei"):
    ziel_rolle = discord.utils.get(interaction.guild.roles, name=rolle)
    erwähnung = ziel_rolle.mention if ziel_rolle else f"@{rolle}"
    embed = discord.Embed(title="🚔 POLIZEI-ALARM", color=discord.Color.blue())
    embed.add_field(name="📢 Nachricht", value=nachricht, inline=False)
    embed.add_field(name="Gesendet von", value=interaction.user.mention)
    embed.set_footer(text=now_str())
    await interaction.response.send_message(content=erwähnung, embed=embed)
    await log_to("polizei-funk", embed)

@bot.tree.command(name="gang_alarm", description="🔫 Sendet einen Alarm an die Gang-Rolle")
@app_commands.describe(nachricht="Was ist die Meldung?", rolle="Rollenname (Standard: Gang)")
async def gang_alarm_cmd(interaction: discord.Interaction, nachricht: str, rolle: str = "Gang"):
    ziel_rolle = discord.utils.get(interaction.guild.roles, name=rolle)
    erwähnung = ziel_rolle.mention if ziel_rolle else f"@{rolle}"
    embed = discord.Embed(title="🔫 GANG-ALARM", color=discord.Color.dark_green())
    embed.add_field(name="📢 Nachricht", value=nachricht, inline=False)
    embed.add_field(name="Gesendet von", value=interaction.user.mention)
    embed.set_footer(text=now_str())
    await interaction.response.send_message(content=erwähnung, embed=embed)
    await log_to("gang-funk", embed)

# ══════════════════════════════════════════════════════════════════
# FAKE RP SYSTEM
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="hack", description="💻 [RP] Hackt ein Zielsystem")
@app_commands.describe(ziel="Wen hacken?")
async def hack_cmd(interaction: discord.Interaction, ziel: discord.Member):
    await interaction.response.defer()
    fortschritt = "\n".join(f"[✓] {s}..." for s in HACK_STUFEN)
    output = (
        f"```ini\n"
        f"[ UCN HACKTOOLS v4.2.1 ]\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"TARGET    : {ziel.display_name} ({ziel.id})\n"
        f"IP-ADDR   : {fake_ip()}\n"
        f"SESSION   : {fake_id()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{fortschritt}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"[✓] ZUGRIFF GEWÄHRT\n"
        f"[✓] DATEN EXTRAHIERT: {random.randint(128, 9999)} MB\n"
        f"[✓] SPUREN VERWISCHT\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"HASH: {fake_hash()}\n"
        f"STATUS: ERFOLGREICH\n"
        f"```"
    )
    embed = discord.Embed(title="💻 HACK ERFOLGREICH", color=discord.Color.green())
    embed.description = output
    embed.set_footer(text=f"Agent: {interaction.user.display_name} • {now_str()}")
    await interaction.followup.send(embed=embed)
    await log_to("hack-logs", embed)

@bot.tree.command(name="scan", description="🔍 [RP] Scannt ein Ziel auf Schwachstellen")
@app_commands.describe(ziel="Wen scannen?")
async def scan_cmd(interaction: discord.Interaction, ziel: discord.Member):
    await interaction.response.defer()
    offene_ports = random.sample(SCAN_PORTS, random.randint(2, 5))
    port_zeilen = "\n".join(
        f"  PORT {p}/tcp   OPEN   {'ENCRYPTED' if p in [443, 8443] else 'VULNERABLE'}"
        for p in sorted(offene_ports)
    )
    output = (
        f"```ini\n"
        f"[ UCN NETWORK SCANNER v3.9 ]\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"TARGET    : {ziel.display_name}\n"
        f"IP-ADDR   : {fake_ip()}\n"
        f"SCAN-TYPE : SYN STEALTH SCAN\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"OFFENE PORTS:\n{port_zeilen}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"SCHWACHSTELLEN : {random.randint(1, 7)}\n"
        f"FIREWALL       : {'AKTIV' if random.random() > 0.5 else 'INAKTIV'}\n"
        f"BETRIEBSSYSTEM : {random.choice(['Linux 5.15', 'Windows Server 2022', 'Ubuntu 22.04'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"SCAN ABGESCHLOSSEN in {random.randint(2,8)}.{random.randint(10,99)}s\n"
        f"```"
    )
    embed = discord.Embed(title="🔍 SCAN ABGESCHLOSSEN", color=discord.Color.blue())
    embed.description = output
    embed.set_footer(text=f"Agent: {interaction.user.display_name} • {now_str()}")
    await interaction.followup.send(embed=embed)
    await log_to("hack-logs", embed)

@bot.tree.command(name="spy", description="🕵️ [RP] Erstellt einen Spionagebericht über ein Ziel")
@app_commands.describe(ziel="Wen ausspionieren?")
async def spy_cmd(interaction: discord.Interaction, ziel: discord.Member):
    await interaction.response.defer()
    output = (
        f"```ini\n"
        f"[ UCN FIELD INTELLIGENCE REPORT ]\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"ZIEL-ID       : {fake_id()}\n"
        f"ZIEL-NAME     : {ziel.display_name}\n"
        f"DECKNAME      : {decknamen.get(ziel.id, 'UNBEKANNT')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"LETZTER STANDORT  : {random.choice(SPION_STANDORTE)}\n"
        f"FAHRZEUG          : {random.choice(SPION_FAHRZEUGE)}\n"
        f"BEGLEITER         : {random.randint(0, 4)} Person(en)\n"
        f"BEWAFFNET         : {random.choice(['JA', 'NEIN', 'UNBEKANNT'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"AGENT-STATUS      : {random.choice(SPION_STATUS)}\n"
        f"FAHNDUNG AKTIV    : {'JA' if ziel.id in fahndungen else 'NEIN'}\n"
        f"VERWARNUNGEN      : {warn_count(ziel.id)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"BERICHT-HASH  : {fake_hash()[:16]}\n"
        f"KLASSIFIZIERT : STRENG GEHEIM\n"
        f"```"
    )
    embed = discord.Embed(title="🕵️ SPIONAGEBERICHT — STRENG GEHEIM", color=discord.Color.dark_purple())
    embed.set_thumbnail(url=ziel.display_avatar.url)
    embed.description = output
    embed.set_footer(text=f"Agent: {interaction.user.display_name} • {now_str()}")
    await interaction.followup.send(embed=embed)
    await log_to("hack-logs", embed)

# ══════════════════════════════════════════════════════════════════
# ACTIVITY SYSTEM
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="ranking", description="🏆 Zeigt die aktivsten Agenten")
async def ranking_cmd(interaction: discord.Interaction):
    if not aktivität:
        await interaction.response.send_message("📊 Noch keine Daten vorhanden.", ephemeral=True)
        return
    sortiert = sorted(aktivität.items(), key=lambda x: x[1]["punkte"], reverse=True)[:10]
    medaillen = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    embed = discord.Embed(title="🏆 UCN AGENTEN-RANGLISTE", color=discord.Color.gold())
    beschreibung = ""
    for i, (uid, daten) in enumerate(sortiert):
        beschreibung += (
            f"{medaillen[i]} **{daten['name']}**\n"
            f"    ┣ 💠 Punkte: `{daten['punkte']}`\n"
            f"    ┗ 💬 Nachrichten: `{daten['nachrichten']}`\n"
        )
    embed.description = beschreibung
    embed.set_footer(text=f"Stand: {now_str()}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="meinrang", description="📈 Zeigt deine persönlichen Aktivitätsdaten")
async def meinrang_cmd(interaction: discord.Interaction):
    uid = interaction.user.id
    daten = aktivität.get(uid)
    if not daten:
        await interaction.response.send_message("Du hast noch keine Punkte. Einfach Nachrichten schreiben!", ephemeral=True)
        return
    sortiert = sorted(aktivität.keys(), key=lambda x: aktivität[x]["punkte"], reverse=True)
    rang = sortiert.index(uid) + 1
    embed = discord.Embed(title=f"📈 Statistiken — {interaction.user.display_name}", color=discord.Color.teal())
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="🏅 Rang", value=f"#{rang} von {len(aktivität)}", inline=True)
    embed.add_field(name="💠 Punkte", value=str(daten["punkte"]), inline=True)
    embed.add_field(name="💬 Nachrichten", value=str(daten["nachrichten"]), inline=True)
    embed.set_footer(text=now_str())
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════════════════════════
# SONSTIGES
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="würfel", description="🎲 Würfelt einen Würfel")
@app_commands.describe(seiten="Wie viele Seiten? (Standard: 6)")
async def würfel_cmd(interaction: discord.Interaction, seiten: int = 6):
    ergebnis = random.randint(1, max(2, seiten))
    await interaction.response.send_message(f"🎲 Du würfelst einen W{seiten}... **{ergebnis}**!")

@bot.tree.command(name="münze", description="🪙 Wirft eine Münze")
async def münze_cmd(interaction: discord.Interaction):
    ergebnis = random.choice(["**Kopf** 👑", "**Zahl** 🔢"])
    await interaction.response.send_message(f"🪙 Die Münze zeigt: {ergebnis}")

@bot.tree.command(name="serverinfo", description="📊 Zeigt Server-Informationen")
async def serverinfo_cmd(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=f"📊 {g.name}", color=discord.Color.blurple())
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="👥 Mitglieder", value=str(g.member_count), inline=True)
    embed.add_field(name="📢 Kanäle", value=str(len(g.channels)), inline=True)
    embed.add_field(name="🎭 Rollen", value=str(len(g.roles)), inline=True)
    embed.add_field(name="📅 Erstellt am", value=g.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="👑 Eigentümer", value=g.owner.mention if g.owner else "?", inline=True)
    embed.set_footer(text=now_str())
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════════════════════════
# /ticket_panel — Panel im Ticket-Kanal posten
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="ticket_panel", description="🎫 Postet das Ticket-Panel im Ticket-Kanal")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_panel_cmd(interaction: discord.Interaction):
    kanal = bot.get_channel(TICKET_PANEL_KANAL_ID)
    if not kanal:
        await interaction.response.send_message(
            f"❌ Ticket-Kanal (`{TICKET_PANEL_KANAL_ID}`) nicht gefunden. Stelle sicher, dass der Bot Zugriff hat.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🎫 UCN TICKET SYSTEM",
        description=(
            "Brauchst du Hilfe oder möchtest etwas melden?\n"
            "Wähle unten die passende Kategorie aus — ein privater Kanal wird nur für dich erstellt.\n\n"
            "🆘 **Support** — Technische Hilfe oder Probleme\n"
            "📝 **Bewerbung** — Für eine Rolle oder Fraktion bewerben\n"
            "🚨 **Meldung** — Spieler oder Vorfall melden\n"
            "💬 **Beschwerde** — Beschwerde einreichen\n"
            "❓ **Allgemeine Anfrage** — Sonstige Fragen ans Team\n"
        ),
        color=discord.Color.dark_gold()
    )
    embed.set_footer(text="UCN Bot — Notruf Hamburg RP • Nur du und das Team können dein Ticket sehen")

    await kanal.send(embed=embed, view=TicketPanelView())
    await interaction.response.send_message(
        f"✅ Ticket-Panel wurde in {kanal.mention} gepostet!",
        ephemeral=True
    )

# ══════════════════════════════════════════════════════════════════
# KUNDENANFRAGE — Command
# ══════════════════════════════════════════════════════════════════
@bot.tree.command(name="kunde", description="📩 Stelle eine Anfrage ans Team")
async def kunde_cmd(interaction: discord.Interaction):
    await interaction.response.send_modal(KundenAnfrageModal())

# ── /geheimakte ────────────────────────────────────────────────────
@bot.tree.command(name="geheimakte", description="🗂️ Zeigt die komplette Geheimakte eines Agenten")
@app_commands.describe(mitglied="Welcher Agent soll analysiert werden?")
async def geheimakte_cmd(interaction: discord.Interaction, mitglied: discord.Member):
    await interaction.response.defer(ephemeral=True)

    warn_anzahl = len(warns.get(mitglied.id, []))

    if warn_anzahl == 0:
        bedrohung = "🟢 KEINE BEDROHUNG"
        bedrohung_farbe = discord.Color.green()
    elif warn_anzahl == 1:
        bedrohung = "🟡 NIEDRIG"
        bedrohung_farbe = discord.Color.yellow()
    elif warn_anzahl == 2:
        bedrohung = "🟠 MITTEL"
        bedrohung_farbe = discord.Color.orange()
    else:
        bedrohung = "🔴 HOCHGEFÄHRLICH"
        bedrohung_farbe = discord.Color.red()

    status_map = {
        discord.Status.online:    "🟢 Online",
        discord.Status.idle:      "🟡 Abwesend",
        discord.Status.dnd:       "🔴 Bitte nicht stören",
        discord.Status.offline:   "⚫ Offline",
    }
    agent_status = status_map.get(mitglied.status, "⚫ Unbekannt")

    join_delta  = datetime.utcnow() - mitglied.joined_at.replace(tzinfo=None)
    create_delta = datetime.utcnow() - mitglied.created_at.replace(tzinfo=None)
    rollen = [r.mention for r in mitglied.roles if r.name != "@everyone"]

    deckname = decknamen.get(mitglied.id, "—")

    embed = discord.Embed(
        title=f"🗂️ GEHEIMAKTE — STRENG GEHEIM",
        description=f"**Akte #{mitglied.id}**",
        color=bedrohung_farbe,
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=mitglied.display_avatar.url)
    embed.set_author(name="UCN Geheimdienstarchiv", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    embed.add_field(name="👤 Echter Name",      value=f"`{mitglied.name}`",                       inline=True)
    embed.add_field(name="🎭 Deckname",          value=f"`{deckname}`",                             inline=True)
    embed.add_field(name="📡 Status",            value=agent_status,                                inline=True)
    embed.add_field(name="📅 Server beigetreten",value=f"{mitglied.joined_at.strftime('%d.%m.%Y')} (vor {join_delta.days} Tagen)",  inline=True)
    embed.add_field(name="🎂 Account erstellt",  value=f"{mitglied.created_at.strftime('%d.%m.%Y')} (vor {create_delta.days} Tagen)", inline=True)
    embed.add_field(name="⚠️ Verwarnungen",      value=f"`{warn_anzahl}`",                          inline=True)
    embed.add_field(name="🚨 Bedrohungsstufe",   value=f"**{bedrohung}**",                          inline=False)
    embed.add_field(name=f"🏷️ Rollen ({len(rollen)})", value=" ".join(rollen) if rollen else "Keine", inline=False)
    embed.set_footer(text=f"Abgerufen von {interaction.user.display_name} • UCN Geheimdienst")

    await interaction.followup.send(embed=embed, ephemeral=True)

# ── /broadcast ─────────────────────────────────────────────────────
@bot.tree.command(name="broadcast", description="📢 Sendet eine offizielle Boss-Durchsage in einen Kanal")
@app_commands.describe(kanal="Zielkanal", nachricht="Die Durchsage")
async def broadcast_cmd(interaction: discord.Interaction, kanal: discord.TextChannel, nachricht: str):
    embed = discord.Embed(
        title="📢 OFFIZIELLE DURCHSAGE",
        description=nachricht,
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    embed.set_author(
        name="UCN Hauptquartier",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )
    embed.set_footer(text=f"Herausgegeben von {interaction.user.display_name} • Undercover Network")

    await kanal.send(embed=embed)
    await interaction.response.send_message(
        f"✅ Durchsage erfolgreich in {kanal.mention} gesendet!",
        ephemeral=True
    )

# ── /uprank ────────────────────────────────────────────────────────
@bot.tree.command(name="uprank", description="⬆️ Befördert ein Mitglied — alter Rang raus, neuer Rang rein")
@app_commands.describe(
    mitglied="Wer wird befördert?",
    alter_rang="Welche Rolle wird entfernt?",
    neuer_rang="Welche Rolle bekommt er/sie?",
    grund="Grund für die Beförderung"
)
async def uprank_cmd(interaction: discord.Interaction, mitglied: discord.Member, alter_rang: discord.Role, neuer_rang: discord.Role, grund: str):
    await interaction.response.defer()

    try:
        if alter_rang in mitglied.roles:
            await mitglied.remove_roles(alter_rang, reason=f"Uprank von {interaction.user}")
        await mitglied.add_roles(neuer_rang, reason=f"Uprank von {interaction.user}: {grund}")
    except discord.Forbidden:
        await interaction.followup.send("❌ Der Bot hat keine Rechte, diese Rollen zu ändern.", ephemeral=True)
        return

    embed = discord.Embed(
        title="⬆️ RANGBEFÖRDERUNG",
        color=discord.Color.brand_green(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=mitglied.display_avatar.url)
    embed.set_author(name="UCN Rangbüro", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.add_field(name="👤 Person",           value=mitglied.mention,        inline=False)
    embed.add_field(name="📉 Alter Rang",        value=alter_rang.mention,      inline=True)
    embed.add_field(name="📈 Neuer Rang",        value=neuer_rang.mention,      inline=True)
    embed.add_field(name="📋 Grund",             value=grund,                   inline=False)
    embed.add_field(name="✍️ Ausgestellt von",   value=interaction.user.mention, inline=False)
    embed.set_footer(text=f"UCN Undercover Network • {interaction.user.display_name}")

    await interaction.followup.send(embed=embed)

    try:
        dm = discord.Embed(
            title="⬆️ Du wurdest befördert!",
            description=(
                f"Dein Rang auf **Undercover Network** wurde geändert!\n\n"
                f"**Alter Rang:** {alter_rang.name}\n"
                f"**Neuer Rang:** {neuer_rang.name}\n"
                f"**Grund:** {grund}\n"
                f"**Ausgestellt von:** {interaction.user.display_name}"
            ),
            color=discord.Color.brand_green(),
            timestamp=datetime.utcnow()
        )
        if not mitglied.bot:
            await mitglied.send(embed=dm)
    except discord.Forbidden:
        pass

# ── /downrank ───────────────────────────────────────────────────────
@bot.tree.command(name="downrank", description="⬇️ Degradiert ein Mitglied — alter Rang raus, neuer Rang rein")
@app_commands.describe(
    mitglied="Wer wird degradiert?",
    alter_rang="Welche Rolle wird entfernt?",
    neuer_rang="Welche Rolle bekommt er/sie?",
    grund="Grund für die Degradierung"
)
async def downrank_cmd(interaction: discord.Interaction, mitglied: discord.Member, alter_rang: discord.Role, neuer_rang: discord.Role, grund: str):
    await interaction.response.defer()

    try:
        if alter_rang in mitglied.roles:
            await mitglied.remove_roles(alter_rang, reason=f"Downrank von {interaction.user}")
        await mitglied.add_roles(neuer_rang, reason=f"Downrank von {interaction.user}: {grund}")
    except discord.Forbidden:
        await interaction.followup.send("❌ Der Bot hat keine Rechte, diese Rollen zu ändern.", ephemeral=True)
        return

    embed = discord.Embed(
        title="⬇️ DEGRADIERUNG",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=mitglied.display_avatar.url)
    embed.set_author(name="UCN Rangbüro", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.add_field(name="👤 Person",           value=mitglied.mention,        inline=False)
    embed.add_field(name="📈 Alter Rang",        value=alter_rang.mention,      inline=True)
    embed.add_field(name="📉 Neuer Rang",        value=neuer_rang.mention,      inline=True)
    embed.add_field(name="📋 Grund",             value=grund,                   inline=False)
    embed.add_field(name="✍️ Ausgestellt von",   value=interaction.user.mention, inline=False)
    embed.set_footer(text=f"UCN Undercover Network • {interaction.user.display_name}")

    await interaction.followup.send(embed=embed)

    try:
        dm = discord.Embed(
            title="⬇️ Dein Rang wurde geändert",
            description=(
                f"Dein Rang auf **Undercover Network** wurde geändert.\n\n"
                f"**Alter Rang:** {alter_rang.name}\n"
                f"**Neuer Rang:** {neuer_rang.name}\n"
                f"**Grund:** {grund}\n"
                f"**Ausgestellt von:** {interaction.user.display_name}"
            ),
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        if not mitglied.bot:
            await mitglied.send(embed=dm)
    except discord.Forbidden:
        pass

# ── /clear ─────────────────────────────────────────────────────────
@bot.tree.command(name="clear", description="🗑️ Löscht eine bestimmte Anzahl Nachrichten im Kanal")
@app_commands.describe(anzahl="Wie viele Nachrichten löschen? (1–100)")
async def clear_cmd(interaction: discord.Interaction, anzahl: int):
    if anzahl < 1 or anzahl > 100:
        await interaction.response.send_message("❌ Bitte eine Zahl zwischen 1 und 100 angeben.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    gelöscht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(f"✅ **{len(gelöscht)}** Nachrichten gelöscht.", ephemeral=True)

# ── /timeout ────────────────────────────────────────────────────────
@bot.tree.command(name="timeout", description="🔇 Stummschaltet ein Mitglied für eine bestimmte Zeit")
@app_commands.describe(
    mitglied="Wer wird stummgeschaltet?",
    minuten="Wie viele Minuten? (max. 40320 = 28 Tage)",
    grund="Grund für den Timeout"
)
async def timeout_cmd(interaction: discord.Interaction, mitglied: discord.Member, minuten: int, grund: str):
    import datetime as dt
    if minuten < 1 or minuten > 40320:
        await interaction.response.send_message("❌ Minuten müssen zwischen 1 und 40320 liegen.", ephemeral=True)
        return
    try:
        until = dt.datetime.utcnow() + dt.timedelta(minutes=minuten)
        await mitglied.timeout(until, reason=f"{grund} — von {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Rechte für diesen Befehl.", ephemeral=True)
        return

    stunden  = minuten // 60
    rest_min = minuten % 60
    dauer_str = f"{stunden}h {rest_min}min" if stunden else f"{minuten} Minuten"

    embed = discord.Embed(title="🔇 TIMEOUT VERGEBEN", color=discord.Color.dark_gray(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=mitglied.display_avatar.url)
    embed.add_field(name="👤 Mitglied",        value=mitglied.mention,         inline=True)
    embed.add_field(name="⏱️ Dauer",           value=dauer_str,                inline=True)
    embed.add_field(name="📋 Grund",           value=grund,                    inline=False)
    embed.add_field(name="✍️ Ausgestellt von", value=interaction.user.mention, inline=False)
    embed.set_footer(text=f"UCN Undercover Network • {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

    try:
        dm = discord.Embed(
            title="🔇 Du wurdest stummgeschaltet",
            description=(
                f"Du wurdest auf **Undercover Network** für **{dauer_str}** stummgeschaltet.\n\n"
                f"**Grund:** {grund}\n**Von:** {interaction.user.display_name}"
            ),
            color=discord.Color.dark_gray()
        )
        if not mitglied.bot:
            await mitglied.send(embed=dm)
    except discord.Forbidden:
        pass

# ── /untimeout ──────────────────────────────────────────────────────
@bot.tree.command(name="untimeout", description="🔊 Hebt den Timeout eines Mitglieds auf")
@app_commands.describe(mitglied="Wessen Timeout wird aufgehoben?")
async def untimeout_cmd(interaction: discord.Interaction, mitglied: discord.Member):
    try:
        await mitglied.timeout(None, reason=f"Timeout aufgehoben von {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Rechte für diesen Befehl.", ephemeral=True)
        return
    embed = discord.Embed(title="🔊 TIMEOUT AUFGEHOBEN", color=discord.Color.green(), timestamp=datetime.utcnow())
    embed.add_field(name="👤 Mitglied",        value=mitglied.mention,         inline=True)
    embed.add_field(name="✍️ Aufgehoben von",  value=interaction.user.mention, inline=True)
    embed.set_footer(text=f"UCN Undercover Network • {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

# ── /server_stats ───────────────────────────────────────────────────
@bot.tree.command(name="server_stats", description="📊 Zeigt Live-Statistiken des Servers")
async def server_stats_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    g = interaction.guild
    await g.chunk()

    total     = g.member_count
    online    = sum(1 for m in g.members if m.status != discord.Status.offline and not m.bot)
    bots      = sum(1 for m in g.members if m.bot)
    text_ch   = len(g.text_channels)
    voice_ch  = len(g.voice_channels)
    rollen    = len(g.roles) - 1
    boosts    = g.premium_subscription_count
    stufe     = g.premium_tier
    alter     = (datetime.utcnow() - g.created_at.replace(tzinfo=None)).days
    verwarnungen_gesamt = sum(len(v) for v in warns.values())
    offene_t  = len(offene_tickets)

    embed = discord.Embed(
        title=f"📊 {g.name} — Server Statistiken",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)

    embed.add_field(name="👥 Mitglieder gesamt",  value=f"`{total}`",       inline=True)
    embed.add_field(name="🟢 Gerade online",       value=f"`{online}`",      inline=True)
    embed.add_field(name="🤖 Bots",                value=f"`{bots}`",        inline=True)
    embed.add_field(name="💬 Textkanäle",          value=f"`{text_ch}`",     inline=True)
    embed.add_field(name="🔊 Sprachkanäle",        value=f"`{voice_ch}`",    inline=True)
    embed.add_field(name="🏷️ Rollen",              value=f"`{rollen}`",      inline=True)
    embed.add_field(name="🚀 Boosts",              value=f"`{boosts}` (Stufe {stufe})", inline=True)
    embed.add_field(name="📅 Serveralter",         value=f"`{alter} Tage`",  inline=True)
    embed.add_field(name="⚠️ Aktive Verwarnungen", value=f"`{verwarnungen_gesamt}`", inline=True)
    embed.add_field(name="🎫 Offene Tickets",      value=f"`{offene_t}`",    inline=True)
    embed.set_footer(text="UCN Undercover Network • Live-Daten")

    await interaction.followup.send(embed=embed)

# ══ 50 EXTRA COMMANDS ══════════════════════════════════════════════

# 1 — /würfeln
@bot.tree.command(name="würfeln", description="🎲 Würfelt eine Zahl")
@app_commands.describe(seiten="Wie viele Seiten? (Standard: 6)")
async def würfeln_cmd(interaction: discord.Interaction, seiten: int = 6):
    if seiten < 2 or seiten > 1000:
        await interaction.response.send_message("❌ Zwischen 2 und 1000 Seiten.", ephemeral=True); return
    ergebnis = random.randint(1, seiten)
    embed = discord.Embed(title=f"🎲 Würfelwurf (W{seiten})", description=f"# **{ergebnis}**", color=discord.Color.blue())
    embed.set_footer(text=f"Gewürfelt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

# 2 — /8ball
@bot.tree.command(name="8ball", description="🎱 Stell dem magischen Ball eine Frage")
@app_commands.describe(frage="Deine Frage")
async def achtball_cmd(interaction: discord.Interaction, frage: str):
    embed = discord.Embed(title="🎱 Magischer Ball", color=discord.Color.dark_purple())
    embed.add_field(name="❓ Frage", value=frage, inline=False)
    embed.add_field(name="🔮 Antwort", value=random.choice(ACHT_BALL_ANTWORTEN), inline=False)
    embed.set_footer(text=f"Gefragt von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

# 3 — /zitat
@bot.tree.command(name="zitat", description="💬 Zeigt ein zufälliges Spionage-Zitat")
async def zitat_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="💬 UCN Spionage-Zitat", description=random.choice(SPION_ZITATE), color=discord.Color.gold())
    embed.set_footer(text="UCN Undercover Network")
    await interaction.response.send_message(embed=embed)

# 4 — /mission
@bot.tree.command(name="mission", description="🎯 Erteilt einem Agenten eine zufällige Mission")
@app_commands.describe(agent="Welcher Agent bekommt die Mission?")
async def mission_cmd(interaction: discord.Interaction, agent: discord.Member):
    aufgabe = random.choice(MISSIONS_POOL)
    embed = discord.Embed(title="🎯 MISSION ERTEILT", color=discord.Color.dark_green(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=agent.display_avatar.url)
    embed.add_field(name="👤 Agent", value=agent.mention, inline=True)
    embed.add_field(name="📋 Auftrag", value=aufgabe, inline=False)
    embed.add_field(name="✍️ Erteilt von", value=interaction.user.mention, inline=True)
    embed.set_footer(text="Streng geheim • UCN Geheimdienst")
    await interaction.response.send_message(embed=embed)

# 5 — /auftrag
@bot.tree.command(name="auftrag", description="📋 Erteilt einem Agenten einen eigenen Auftrag")
@app_commands.describe(agent="Welcher Agent?", auftrag="Was ist der Auftrag?")
async def auftrag_cmd(interaction: discord.Interaction, agent: discord.Member, auftrag: str):
    aufträge[agent.id] = {"auftrag": auftrag, "von": interaction.user.display_name, "zeit": now_str()}
    embed = discord.Embed(title="📋 AUFTRAG VERGEBEN", color=discord.Color.dark_teal(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=agent.display_avatar.url)
    embed.add_field(name="👤 Agent", value=agent.mention, inline=True)
    embed.add_field(name="📝 Auftrag", value=auftrag, inline=False)
    embed.add_field(name="✍️ Vergeben von", value=interaction.user.mention, inline=True)
    embed.set_footer(text="UCN Undercover Network")
    await interaction.response.send_message(embed=embed)
    try:
        if not agent.bot:
            await agent.send(embed=discord.Embed(title="📋 Neuer Auftrag!", description=f"**Auftrag:** {auftrag}\n**Von:** {interaction.user.display_name}", color=discord.Color.dark_teal()))
    except discord.Forbidden:
        pass

# 6 — /mein_auftrag
@bot.tree.command(name="mein_auftrag", description="📋 Zeigt deinen aktuellen Auftrag")
async def mein_auftrag_cmd(interaction: discord.Interaction):
    a = aufträge.get(interaction.user.id)
    if not a:
        await interaction.response.send_message("❌ Du hast keinen aktiven Auftrag.", ephemeral=True); return
    embed = discord.Embed(title="📋 DEIN AKTUELLER AUFTRAG", color=discord.Color.dark_teal())
    embed.add_field(name="📝 Auftrag", value=a["auftrag"], inline=False)
    embed.add_field(name="✍️ Von", value=a["von"], inline=True)
    embed.add_field(name="🕒 Zeit", value=a["zeit"], inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 7 — /lagebericht
@bot.tree.command(name="lagebericht", description="📡 Sendet einen offiziellen Lagebericht in einen Kanal")
@app_commands.describe(kanal="Zielkanal", bericht="Der Lagebericht")
async def lagebericht_cmd(interaction: discord.Interaction, kanal: discord.TextChannel, bericht: str):
    embed = discord.Embed(title="📡 LAGEBERICHT — UCN HAUPTQUARTIER", description=bericht, color=discord.Color.dark_blue(), timestamp=datetime.utcnow())
    embed.set_author(name="UCN Geheimdienst", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.add_field(name="✍️ Berichtet von", value=interaction.user.mention, inline=True)
    embed.set_footer(text="UCN Undercover Network • Streng vertraulich")
    await kanal.send(embed=embed)
    await interaction.response.send_message(f"✅ Lagebericht in {kanal.mention} gesendet!", ephemeral=True)

# 8 — /notfall
@bot.tree.command(name="notfall", description="🚨 Sendet einen Notfall-Alarm mit @everyone")
@app_commands.describe(kanal="Zielkanal", meldung="Die Notfall-Meldung")
async def notfall_cmd(interaction: discord.Interaction, kanal: discord.TextChannel, meldung: str):
    embed = discord.Embed(title="🚨 ⚠️ NOTFALL-ALARM ⚠️ 🚨", description=meldung, color=discord.Color.red(), timestamp=datetime.utcnow())
    embed.set_author(name="UCN Notfallzentrale", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.add_field(name="✍️ Gemeldet von", value=interaction.user.mention)
    embed.set_footer(text="UCN Undercover Network • Sofortiger Handlungsbedarf")
    await kanal.send("@everyone", embed=embed)
    await interaction.response.send_message(f"✅ Notfall-Alarm in {kanal.mention} gesendet!", ephemeral=True)

# 9 — /verrat
@bot.tree.command(name="verrat", description="🗡️ Meldet einen Verräter")
@app_commands.describe(verräter="Wer ist der Verräter?", grund="Was hat er/sie getan?")
async def verrat_cmd(interaction: discord.Interaction, verräter: discord.Member, grund: str):
    embed = discord.Embed(title="🗡️ VERRAT GEMELDET", color=discord.Color.dark_red(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=verräter.display_avatar.url)
    embed.add_field(name="🎯 Verräter", value=verräter.mention, inline=True)
    embed.add_field(name="📋 Grund", value=grund, inline=False)
    embed.add_field(name="👁️ Gemeldet von", value=interaction.user.mention, inline=True)
    embed.set_footer(text="UCN Geheimdienst • Interne Angelegenheit")
    await interaction.response.send_message(embed=embed)

# 10 — /codewort
@bot.tree.command(name="codewort", description="🔑 Generiert ein zufälliges Codewort")
async def codewort_cmd(interaction: discord.Interaction):
    adj = ["Schwarzer","Stiller","Roter","Blauer","Eisiger","Goldener","Silberner","Blinder","Schneller","Dunkler"]
    noun = ["Adler","Wolf","Schatten","Blitz","Sturm","Falke","Panther","Drache","Phönix","Rabe"]
    embed = discord.Embed(title="🔑 CODEWORT GENERIERT", description=f"## `{random.choice(adj)} {random.choice(noun)}`", color=discord.Color.gold())
    embed.set_footer(text="Streng geheim — nur einmalig verwenden!")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 11 — /morsecode
@bot.tree.command(name="morsecode", description="📻 Konvertiert Text zu Morsecode")
@app_commands.describe(text="Text zum Konvertieren")
async def morsecode_cmd(interaction: discord.Interaction, text: str):
    M = {'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..','0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.',' ':'/'}
    result = ' '.join(M.get(c.upper(), '?') for c in text)[:900]
    embed = discord.Embed(title="📻 MORSECODE", color=discord.Color.orange())
    embed.add_field(name="📝 Original", value=f"`{text[:200]}`", inline=False)
    embed.add_field(name="📡 Morse", value=f"`{result}`", inline=False)
    await interaction.response.send_message(embed=embed)

# 12 — /verschlüsseln
@bot.tree.command(name="verschlüsseln", description="🔒 Verschlüsselt eine Nachricht (Caesar-Chiffre)")
@app_commands.describe(text="Text", schlüssel="Verschiebung 1–25 (Standard: 13)")
async def verschlüsseln_cmd(interaction: discord.Interaction, text: str, schlüssel: int = 13):
    k = schlüssel % 26
    out = ''.join(chr((ord(c)-65+k)%26+65) if c.isupper() else chr((ord(c)-97+k)%26+97) if c.islower() else c for c in text)
    embed = discord.Embed(title="🔒 NACHRICHT VERSCHLÜSSELT", color=discord.Color.dark_green())
    embed.add_field(name="📝 Original", value=f"`{text[:200]}`", inline=False)
    embed.add_field(name="🔑 Schlüssel", value=f"`{k}`", inline=True)
    embed.add_field(name="🔒 Verschlüsselt", value=f"`{out[:200]}`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 13 — /entschlüsseln
@bot.tree.command(name="entschlüsseln", description="🔓 Entschlüsselt eine Caesar-Nachricht")
@app_commands.describe(text="Verschlüsselter Text", schlüssel="Verschiebung 1–25")
async def entschlüsseln_cmd(interaction: discord.Interaction, text: str, schlüssel: int = 13):
    k = schlüssel % 26
    out = ''.join(chr((ord(c)-65-k)%26+65) if c.isupper() else chr((ord(c)-97-k)%26+97) if c.islower() else c for c in text)
    embed = discord.Embed(title="🔓 NACHRICHT ENTSCHLÜSSELT", color=discord.Color.green())
    embed.add_field(name="🔒 Verschlüsselt", value=f"`{text[:200]}`", inline=False)
    embed.add_field(name="🔑 Schlüssel", value=f"`{k}`", inline=True)
    embed.add_field(name="📝 Entschlüsselt", value=f"`{out[:200]}`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 14 — /agenten_ausweis
@bot.tree.command(name="agenten_ausweis", description="🪪 Generiert einen offiziellen Agenten-Ausweis")
@app_commands.describe(agent="Für welchen Agenten?")
async def agenten_ausweis_cmd(interaction: discord.Interaction, agent: discord.Member):
    embed = discord.Embed(title="🪪 UCN AGENTEN-AUSWEIS", color=discord.Color.dark_gold(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=agent.display_avatar.url)
    embed.set_author(name="Undercover Network • Offiziell", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.add_field(name="👤 Name", value=f"`{agent.name}`", inline=True)
    embed.add_field(name="🎭 Deckname", value=f"`{decknamen.get(agent.id, 'UNBEKANNT')}`", inline=True)
    embed.add_field(name="🆔 Agenten-ID", value=f"`#{agent.id % 99999:05d}`", inline=True)
    embed.add_field(name="📅 Beigetreten", value=f"`{agent.joined_at.strftime('%d.%m.%Y') if agent.joined_at else '?'}`", inline=True)
    embed.add_field(name="⚠️ Einträge", value=f"`{len(warns.get(agent.id, []))}`", inline=True)
    embed.add_field(name="🔰 Status", value="`AKTIV`", inline=True)
    embed.set_footer(text="UCN • Streng Geheim • Ausgestellt vom UCN Geheimdienst")
    await interaction.response.send_message(embed=embed)

# 15 — /nick
@bot.tree.command(name="nick", description="✏️ Ändert den Spitznamen eines Mitglieds")
@app_commands.describe(mitglied="Wessen Nick?", name="Neuer Name (leer = zurücksetzen)")
async def nick_cmd(interaction: discord.Interaction, mitglied: discord.Member, name: str = ""):
    try:
        await mitglied.edit(nick=name if name else None)
        await interaction.response.send_message(f"✅ Nickname von {mitglied.mention} → `{name if name else 'Original'}`", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)

# 16 — /kanal_sperren
@bot.tree.command(name="kanal_sperren", description="🔒 Sperrt einen Kanal für alle Mitglieder")
@app_commands.describe(kanal="Welcher Kanal? (leer = aktueller)")
async def kanal_sperren_cmd(interaction: discord.Interaction, kanal: discord.TextChannel = None):
    kanal = kanal or interaction.channel
    try:
        await kanal.set_permissions(interaction.guild.default_role, send_messages=False)
        embed = discord.Embed(title="🔒 KANAL GESPERRT", description=f"{kanal.mention} ist jetzt gesperrt.", color=discord.Color.red(), timestamp=datetime.utcnow())
        embed.add_field(name="✍️ Gesperrt von", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)
        await kanal.send(embed=discord.Embed(title="🔒 Dieser Kanal ist gesperrt.", description="Nur das Team kann hier schreiben.", color=discord.Color.red()))
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)

# 17 — /kanal_entsperren
@bot.tree.command(name="kanal_entsperren", description="🔓 Entsperrt einen Kanal wieder")
@app_commands.describe(kanal="Welcher Kanal? (leer = aktueller)")
async def kanal_entsperren_cmd(interaction: discord.Interaction, kanal: discord.TextChannel = None):
    kanal = kanal or interaction.channel
    try:
        await kanal.set_permissions(interaction.guild.default_role, send_messages=None)
        embed = discord.Embed(title="🔓 KANAL ENTSPERRT", description=f"{kanal.mention} ist wieder geöffnet.", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.add_field(name="✍️ Entsperrt von", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)

# 18 — /slowmode
@bot.tree.command(name="slowmode", description="🐌 Setzt den Slowmode in einem Kanal")
@app_commands.describe(sekunden="Sekunden (0 = aus)", kanal="Welcher Kanal?")
async def slowmode_cmd(interaction: discord.Interaction, sekunden: int, kanal: discord.TextChannel = None):
    kanal = kanal or interaction.channel
    if sekunden < 0 or sekunden > 21600:
        await interaction.response.send_message("❌ Zwischen 0 und 21600 Sekunden.", ephemeral=True); return
    try:
        await kanal.edit(slowmode_delay=sekunden)
        status = f"{sekunden}s" if sekunden > 0 else "Deaktiviert"
        await interaction.response.send_message(f"✅ Slowmode in {kanal.mention}: **{status}**", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)

# 19 — /rolle_geben
@bot.tree.command(name="rolle_geben", description="➕ Gibt einem Mitglied eine Rolle")
@app_commands.describe(mitglied="Wer?", rolle="Welche Rolle?")
async def rolle_geben_cmd(interaction: discord.Interaction, mitglied: discord.Member, rolle: discord.Role):
    try:
        await mitglied.add_roles(rolle)
        await interaction.response.send_message(f"✅ {rolle.mention} an {mitglied.mention} vergeben.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)

# 20 — /rolle_entfernen
@bot.tree.command(name="rolle_entfernen", description="➖ Entfernt eine Rolle von einem Mitglied")
@app_commands.describe(mitglied="Wer?", rolle="Welche Rolle?")
async def rolle_entfernen_cmd(interaction: discord.Interaction, mitglied: discord.Member, rolle: discord.Role):
    try:
        await mitglied.remove_roles(rolle)
        await interaction.response.send_message(f"✅ {rolle.mention} von {mitglied.mention} entfernt.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)

# 21 — /user_info
@bot.tree.command(name="user_info", description="ℹ️ Zeigt Basis-Infos über ein Mitglied")
@app_commands.describe(mitglied="Wer?")
async def user_info_cmd(interaction: discord.Interaction, mitglied: discord.Member = None):
    m = mitglied or interaction.user
    embed = discord.Embed(title=f"ℹ️ {m.display_name}", color=m.color, timestamp=datetime.utcnow())
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="🆔 ID", value=f"`{m.id}`", inline=True)
    embed.add_field(name="📅 Account erstellt", value=m.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="📥 Server beigetreten", value=m.joined_at.strftime("%d.%m.%Y") if m.joined_at else "?", inline=True)
    embed.add_field(name="🤖 Bot", value="Ja" if m.bot else "Nein", inline=True)
    embed.add_field(name="🏷️ Rollen", value=str(len(m.roles)-1), inline=True)
    await interaction.response.send_message(embed=embed)

# 22 — /rolle_info
@bot.tree.command(name="rolle_info", description="ℹ️ Zeigt Infos über eine Rolle")
@app_commands.describe(rolle="Welche Rolle?")
async def rolle_info_cmd(interaction: discord.Interaction, rolle: discord.Role):
    embed = discord.Embed(title=f"ℹ️ {rolle.name}", color=rolle.color, timestamp=datetime.utcnow())
    embed.add_field(name="🆔 ID", value=f"`{rolle.id}`", inline=True)
    embed.add_field(name="👥 Mitglieder", value=f"`{len(rolle.members)}`", inline=True)
    embed.add_field(name="📅 Erstellt", value=rolle.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="🎨 Farbe", value=str(rolle.color), inline=True)
    embed.add_field(name="📌 Angepinnt", value="Ja" if rolle.hoist else "Nein", inline=True)
    embed.add_field(name="🔔 Erwähnbar", value="Ja" if rolle.mentionable else "Nein", inline=True)
    await interaction.response.send_message(embed=embed)

# 23 — /avatar
@bot.tree.command(name="avatar", description="🖼️ Zeigt das Profilbild eines Mitglieds")
@app_commands.describe(mitglied="Wessen Avatar?")
async def avatar_cmd(interaction: discord.Interaction, mitglied: discord.Member = None):
    m = mitglied or interaction.user
    embed = discord.Embed(title=f"🖼️ Avatar von {m.display_name}", color=discord.Color.blurple())
    embed.set_image(url=m.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# 24 — /warn_liste
@bot.tree.command(name="warn_liste", description="📋 Zeigt alle Verwarnungen aller Mitglieder")
async def warn_liste_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not warns:
        await interaction.followup.send("✅ Keine Verwarnungen vorhanden.", ephemeral=True); return
    text = ""
    for uid, wl in warns.items():
        if wl:
            member = interaction.guild.get_member(uid)
            name = member.display_name if member else f"ID:{uid}"
            text += f"**{name}** — {len(wl)} Verwarnung(en)\n"
    embed = discord.Embed(title="📋 ALLE VERWARNUNGEN", description=text[:2000] or "Keine", color=discord.Color.orange())
    await interaction.followup.send(embed=embed, ephemeral=True)

# 25 — /alle_warns_löschen
@bot.tree.command(name="alle_warns_löschen", description="🗑️ Löscht alle Verwarnungen eines Mitglieds")
@app_commands.describe(mitglied="Wessen Verwarnungen löschen?")
async def alle_warns_löschen_cmd(interaction: discord.Interaction, mitglied: discord.Member):
    warns[mitglied.id] = []
    await interaction.response.send_message(f"✅ Alle Verwarnungen von {mitglied.mention} gelöscht.", ephemeral=True)

# 26 — /ping
@bot.tree.command(name="ping", description="🏓 Zeigt die Bot-Latenz")
async def ping_cmd(interaction: discord.Interaction):
    latenz = round(bot.latency * 1000)
    farbe = discord.Color.green() if latenz < 100 else discord.Color.yellow() if latenz < 200 else discord.Color.red()
    embed = discord.Embed(title="🏓 Pong!", description=f"**Latenz:** `{latenz}ms`", color=farbe)
    await interaction.response.send_message(embed=embed)

# 27 — /uptime
@bot.tree.command(name="uptime", description="⏱️ Zeigt wie lange der Bot schon läuft")
async def uptime_cmd(interaction: discord.Interaction):
    delta = datetime.utcnow() - bot_start_time
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    embed = discord.Embed(title="⏱️ Bot Uptime", description=f"`{h}h {m}m {s}s`", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

# 28 — /bot_info
@bot.tree.command(name="bot_info", description="🤖 Zeigt Infos über den Bot")
async def bot_info_cmd(interaction: discord.Interaction):
    delta = datetime.utcnow() - bot_start_time
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m2, s = divmod(rem, 60)
    embed = discord.Embed(title="🤖 UCN Bot Informationen", color=discord.Color.blurple(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.add_field(name="🏷️ Name", value=f"`{bot.user}`", inline=True)
    embed.add_field(name="🆔 ID", value=f"`{bot.user.id}`", inline=True)
    embed.add_field(name="📡 Latenz", value=f"`{round(bot.latency*1000)}ms`", inline=True)
    embed.add_field(name="⏱️ Uptime", value=f"`{h}h {m2}m {s}s`", inline=True)
    embed.add_field(name="🏠 Server", value=f"`{len(bot.guilds)}`", inline=True)
    embed.set_footer(text="Undercover Network • UCN")
    await interaction.response.send_message(embed=embed)

# 29 — /zufall_mitglied
@bot.tree.command(name="zufall_mitglied", description="🎲 Wählt ein zufälliges Mitglied aus")
async def zufall_mitglied_cmd(interaction: discord.Interaction):
    echte = [m for m in interaction.guild.members if not m.bot]
    if not echte:
        await interaction.response.send_message("❌ Keine Mitglieder.", ephemeral=True); return
    g = random.choice(echte)
    embed = discord.Embed(title="🎲 Zufälliges Mitglied", description=f"### {g.mention}", color=discord.Color.blue())
    embed.set_thumbnail(url=g.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# 30 — /umfrage
@bot.tree.command(name="umfrage", description="📊 Erstellt eine Ja/Nein Umfrage")
@app_commands.describe(frage="Die Umfrage-Frage")
async def umfrage_cmd(interaction: discord.Interaction, frage: str):
    embed = discord.Embed(title="📊 UMFRAGE", description=f"**{frage}**", color=discord.Color.blurple(), timestamp=datetime.utcnow())
    embed.set_footer(text=f"Erstellt von {interaction.user.display_name}")
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    await interaction.response.send_message("✅ Umfrage erstellt!", ephemeral=True)

# 31 — /rollen_liste
@bot.tree.command(name="rollen_liste", description="🏷️ Zeigt alle Rollen des Servers")
async def rollen_liste_cmd(interaction: discord.Interaction):
    rollen = [f"{r.mention} — `{len(r.members)}` Mitglieder" for r in reversed(interaction.guild.roles) if r.name != "@everyone"]
    embed = discord.Embed(title=f"🏷️ Rollen — {interaction.guild.name}", description="\n".join(rollen[:25]) or "Keine", color=discord.Color.blurple())
    embed.set_footer(text=f"Gesamt: {len(rollen)} Rollen")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 32 — /kanal_info
@bot.tree.command(name="kanal_info", description="ℹ️ Zeigt Infos über den aktuellen Kanal")
async def kanal_info_cmd(interaction: discord.Interaction):
    k = interaction.channel
    embed = discord.Embed(title=f"ℹ️ #{k.name}", color=discord.Color.blurple(), timestamp=datetime.utcnow())
    embed.add_field(name="🆔 ID", value=f"`{k.id}`", inline=True)
    embed.add_field(name="📅 Erstellt", value=k.created_at.strftime("%d.%m.%Y"), inline=True)
    if hasattr(k, 'topic') and k.topic:
        embed.add_field(name="📝 Thema", value=k.topic[:200], inline=False)
    if hasattr(k, 'slowmode_delay'):
        embed.add_field(name="🐌 Slowmode", value=f"`{k.slowmode_delay}s`", inline=True)
    await interaction.response.send_message(embed=embed)

# 33 — /id
@bot.tree.command(name="id", description="🆔 Zeigt die Discord-ID eines Mitglieds")
@app_commands.describe(mitglied="Wessen ID?")
async def id_cmd(interaction: discord.Interaction, mitglied: discord.Member = None):
    m = mitglied or interaction.user
    await interaction.response.send_message(f"🆔 **{m.display_name}** → `{m.id}`", ephemeral=True)

# 34 — /server_icon
@bot.tree.command(name="server_icon", description="🖼️ Zeigt das Server-Icon")
async def server_icon_cmd(interaction: discord.Interaction):
    if not interaction.guild.icon:
        await interaction.response.send_message("❌ Kein Server-Icon.", ephemeral=True); return
    embed = discord.Embed(title=f"🖼️ {interaction.guild.name}", color=discord.Color.blurple())
    embed.set_image(url=interaction.guild.icon.url)
    await interaction.response.send_message(embed=embed)

# 35 — /verhör_liste
@bot.tree.command(name="verhör_liste", description="📋 Zeigt alle Verhör-Protokolle")
async def verhör_liste_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not verhöre:
        await interaction.followup.send("📋 Keine Verhöre eingetragen.", ephemeral=True); return
    text = "\n".join(f"• **{v['täter']}** — von {v['beamter']} ({v['zeit']})" for v in verhöre[-10:])
    embed = discord.Embed(title="📋 VERHÖR-PROTOKOLL (letzte 10)", description=text, color=discord.Color.dark_orange())
    await interaction.followup.send(embed=embed, ephemeral=True)

# 36 — /spion_liste
@bot.tree.command(name="spion_liste", description="🕵️ Zeigt alle gemeldeten Spione")
async def spion_liste_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not spion_meldungen:
        await interaction.followup.send("📋 Keine Spion-Meldungen.", ephemeral=True); return
    text = "\n".join(f"• **{s['verdächtig']}** — von {s['melder']} ({s['zeit']})" for s in spion_meldungen[-10:])
    embed = discord.Embed(title="🕵️ SPION-MELDUNGEN (letzte 10)", description=text, color=discord.Color.purple())
    await interaction.followup.send(embed=embed, ephemeral=True)

# 37 — /fahndungsliste
@bot.tree.command(name="fahndungsliste", description="🚨 Zeigt alle aktiven Fahndungen")
async def fahndungsliste_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    aktive = {uid: f for uid, f in fahndungen.items() if f.get("aktiv")}
    if not aktive:
        await interaction.followup.send("✅ Keine aktiven Fahndungen.", ephemeral=True); return
    text = "\n".join(f"• **{f['name']}** — {f['grund']} ({f['zeit']})" for f in aktive.values())
    embed = discord.Embed(title="🚨 AKTIVE FAHNDUNGEN", description=text[:2000], color=discord.Color.red())
    await interaction.followup.send(embed=embed, ephemeral=True)

# 38 — /mein_profil
@bot.tree.command(name="mein_profil", description="👤 Zeigt dein eigenes UCN-Profil")
async def mein_profil_cmd(interaction: discord.Interaction):
    u = interaction.user
    a = aufträge.get(u.id)
    embed = discord.Embed(title="👤 MEIN UCN-PROFIL", color=discord.Color.dark_blue(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=u.display_avatar.url)
    embed.add_field(name="🎭 Deckname", value=f"`{decknamen.get(u.id, '—')}`", inline=True)
    embed.add_field(name="⚠️ Verwarnungen", value=f"`{len(warns.get(u.id, []))}`", inline=True)
    embed.add_field(name="📋 Aktiver Auftrag", value=a["auftrag"][:100] if a else "Keiner", inline=False)
    embed.set_footer(text="UCN Undercover Network")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 39 — /flüstern
@bot.tree.command(name="flüstern", description="🤫 Schickt jemandem anonym eine geheime DM-Nachricht")
@app_commands.describe(mitglied="An wen?", nachricht="Die geheime Nachricht")
async def flüstern_cmd(interaction: discord.Interaction, mitglied: discord.Member, nachricht: str):
    try:
        embed = discord.Embed(title="🤫 ANONYME GEHEIMBOTSCHAFT", description=nachricht, color=discord.Color.dark_purple(), timestamp=datetime.utcnow())
        embed.set_footer(text="Diese Nachricht wurde anonym übermittelt • UCN Geheimdienst")
        await mitglied.send(embed=embed)
        await interaction.response.send_message(f"✅ Anonyme Botschaft an {mitglied.mention} gesendet!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ DMs sind bei diesem Mitglied deaktiviert.", ephemeral=True)

# 40 — /ankündigung
@bot.tree.command(name="ankündigung", description="📣 Sendet eine Ankündigung mit optionalem Ping")
@app_commands.describe(kanal="Zielkanal", nachricht="Die Ankündigung", rolle="Welche Rolle anpingen?")
async def ankündigung_cmd(interaction: discord.Interaction, kanal: discord.TextChannel, nachricht: str, rolle: discord.Role = None):
    embed = discord.Embed(title="📣 ANKÜNDIGUNG", description=nachricht, color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.set_footer(text=f"Von {interaction.user.display_name}")
    await kanal.send(content=rolle.mention if rolle else "", embed=embed)
    await interaction.response.send_message(f"✅ Ankündigung in {kanal.mention} gesendet!", ephemeral=True)

# 41 — /emoji_liste
@bot.tree.command(name="emoji_liste", description="😀 Zeigt alle Custom-Emojis des Servers")
async def emoji_liste_cmd(interaction: discord.Interaction):
    emojis = interaction.guild.emojis
    if not emojis:
        await interaction.response.send_message("❌ Keine Custom-Emojis.", ephemeral=True); return
    text = " ".join(str(e) for e in emojis[:50])
    embed = discord.Embed(title=f"😀 Custom Emojis ({len(emojis)})", description=text, color=discord.Color.yellow())
    await interaction.response.send_message(embed=embed)

# 42 — /boost_info
@bot.tree.command(name="boost_info", description="🚀 Zeigt Server-Boost Informationen")
async def boost_info_cmd(interaction: discord.Interaction):
    g = interaction.guild
    booster = [m.mention for m in g.premium_subscribers]
    embed = discord.Embed(title="🚀 Server Boost Status", color=discord.Color.nitro_pink(), timestamp=datetime.utcnow())
    embed.add_field(name="📈 Boost-Stufe", value=f"`{g.premium_tier}`", inline=True)
    embed.add_field(name="🚀 Boosts", value=f"`{g.premium_subscription_count}`", inline=True)
    embed.add_field(name=f"💎 Booster ({len(booster)})", value=", ".join(booster[:10]) or "Keine", inline=False)
    await interaction.response.send_message(embed=embed)

# 43 — /kanal_thema
@bot.tree.command(name="kanal_thema", description="📝 Setzt das Thema eines Kanals")
@app_commands.describe(thema="Das neue Thema", kanal="Welcher Kanal?")
async def kanal_thema_cmd(interaction: discord.Interaction, thema: str, kanal: discord.TextChannel = None):
    kanal = kanal or interaction.channel
    try:
        await kanal.edit(topic=thema)
        await interaction.response.send_message(f"✅ Thema von {kanal.mention} gesetzt: `{thema}`", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Keine Berechtigung.", ephemeral=True)

# 44 — /warnung_detail
@bot.tree.command(name="warnung_detail", description="🔍 Alle Verwarnungen eines Mitglieds im Detail")
@app_commands.describe(mitglied="Wessen Verwarnungen?")
async def warnung_detail_cmd(interaction: discord.Interaction, mitglied: discord.Member):
    wl = warns.get(mitglied.id, [])
    if not wl:
        await interaction.response.send_message(f"✅ {mitglied.mention} hat keine Verwarnungen.", ephemeral=True); return
    text = "\n".join(f"`{i+1}.` {w}" for i, w in enumerate(wl))
    embed = discord.Embed(title=f"⚠️ Verwarnungen: {mitglied.display_name}", description=text[:2000], color=discord.Color.orange())
    embed.set_thumbnail(url=mitglied.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 45 — /mitglieder_mit_rolle
@bot.tree.command(name="mitglieder_mit_rolle", description="👥 Zeigt alle Mitglieder mit einer bestimmten Rolle")
@app_commands.describe(rolle="Welche Rolle?")
async def mitglieder_mit_rolle_cmd(interaction: discord.Interaction, rolle: discord.Role):
    mitglieder = [m.mention for m in rolle.members if not m.bot]
    embed = discord.Embed(title=f"👥 {rolle.name} ({len(mitglieder)})", description=", ".join(mitglieder[:30]) or "Niemand", color=rolle.color)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 46 — /bericht
@bot.tree.command(name="bericht", description="📄 Erstellt einen offiziellen Ereignisbericht")
@app_commands.describe(titel="Titel des Berichts", inhalt="Inhalt")
async def bericht_cmd(interaction: discord.Interaction, titel: str, inhalt: str):
    embed = discord.Embed(title=f"📄 BERICHT: {titel}", description=inhalt, color=discord.Color.dark_gray(), timestamp=datetime.utcnow())
    embed.set_author(name=f"Verfasst von {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text="UCN Undercover Network • Offizielles Dokument")
    await interaction.response.send_message(embed=embed)

# 47 — /timer
@bot.tree.command(name="timer", description="⏰ Setzt einen Timer (max 60 Min) und erinnert dich")
@app_commands.describe(minuten="Wie viele Minuten?", nachricht="Was soll erinnert werden?")
async def timer_cmd(interaction: discord.Interaction, minuten: int, nachricht: str = "Zeit ist um!"):
    import asyncio
    if minuten < 1 or minuten > 60:
        await interaction.response.send_message("❌ Zwischen 1 und 60 Minuten.", ephemeral=True); return
    await interaction.response.send_message(f"⏰ Timer gesetzt! Ich erinnere dich in **{minuten} Minuten**.", ephemeral=True)
    await asyncio.sleep(minuten * 60)
    try:
        await interaction.followup.send(f"⏰ {interaction.user.mention} — **Timer abgelaufen!**\n📝 {nachricht}")
    except Exception:
        pass

# 48 — /willkommen_test
@bot.tree.command(name="willkommen_test", description="👋 Testet die Willkommensnachricht")
@app_commands.describe(mitglied="Wessen Willkommen testen?")
async def willkommen_test_cmd(interaction: discord.Interaction, mitglied: discord.Member = None):
    m = mitglied or interaction.user
    embed = discord.Embed(title="👋 WILLKOMMEN BEI UCN!", description=f"**{m.mention}** ist dem **Undercover Network** beigetreten!\n\nWillkommen im Schatten. Vertraue niemandem. 🕵️", color=discord.Color.dark_gold(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="👥 Mitglied Nr.", value=f"`#{interaction.guild.member_count}`")
    embed.set_footer(text="UCN Undercover Network")
    await interaction.response.send_message(embed=embed)

# 49 — /zähle_mitglieder
@bot.tree.command(name="zähle_mitglieder", description="👥 Zählt alle Mitglieder nach Typ")
async def zähle_mitglieder_cmd(interaction: discord.Interaction):
    g = interaction.guild
    bots = sum(1 for m in g.members if m.bot)
    embed = discord.Embed(title="👥 Mitglieder-Statistik", color=discord.Color.blurple())
    embed.add_field(name="👥 Gesamt", value=f"`{g.member_count}`", inline=True)
    embed.add_field(name="👤 Menschen", value=f"`{g.member_count - bots}`", inline=True)
    embed.add_field(name="🤖 Bots", value=f"`{bots}`", inline=True)
    await interaction.response.send_message(embed=embed)

# 50 — /löschen_nach
@bot.tree.command(name="löschen_nach", description="🗑️ Löscht nur Nachrichten eines bestimmten Mitglieds")
@app_commands.describe(mitglied="Wessen Nachrichten?", anzahl="Wie viele prüfen? (max 100)")
async def löschen_nach_cmd(interaction: discord.Interaction, mitglied: discord.Member, anzahl: int = 50):
    await interaction.response.defer(ephemeral=True)
    anzahl = min(anzahl, 100)
    gelöscht = await interaction.channel.purge(limit=anzahl, check=lambda msg: msg.author.id == mitglied.id)
    await interaction.followup.send(f"✅ **{len(gelöscht)}** Nachrichten von {mitglied.mention} gelöscht.", ephemeral=True)

# ══════════════════════════════════════════════════════════════════
# 20 NEUE COMMANDS — 5 NUR TEAM | 15 FÜR ALLE
# ══════════════════════════════════════════════════════════════════

# ── Datenpools für neue Commands ───────────────────────────────────
HAMBURG_STADTTEILE = [
    "Hamburg Altona", "Reeperbahn / St. Pauli", "Speicherstadt", "HafenCity",
    "Barmbek-Nord", "Eimsbüttel", "Wandsbek", "Harburg", "Bergedorf",
    "Blankenese", "Rahlstedt", "Billstedt", "Poppenbüttel", "Schnelsen",
]
HAMBURG_TREFFPUNKTE = [
    "Jungfernstieg (Alster-Ufer, Süd-Ende)", "Hauptbahnhof (Ausgang Kirchenallee)",
    "Fischmarkt (Eingang Hafentreppe)", "Speicherstadt Block G (Hintereingang)",
    "Reeperbahn Ecke Davidstraße", "HafenCity Überseequartier (Brunnen)",
    "Elbphilharmonie Plaza (Westseite)", "Blankenese Süllberg (Aussichtsplatz)",
    "Rathausmarkt (Hinterseite Rathaus)", "Containerterminal Altenwerder (Zaun Nord)"
]
HAMBURG_WETTER = [
    ("☁️ Bewölkt", "14°C", "Leichter Wind aus NW", "Sichtbarkeit: Gut"),
    ("🌧️ Regnerisch", "11°C", "Starker Wind aus W", "Sichtbarkeit: Eingeschränkt"),
    ("☀️ Sonnig", "19°C", "Windstill", "Sichtbarkeit: Ausgezeichnet"),
    ("🌩️ Gewitter", "9°C", "Böen bis 60 km/h aus SW", "Sichtbarkeit: Sehr schlecht"),
    ("🌫️ Neblig", "8°C", "Kein Wind", "Sichtbarkeit: Gefährlich niedrig"),
    ("🌦️ Wechselhaft", "13°C", "Mäßiger Wind aus NO", "Sichtbarkeit: Mittel"),
]
RP_TIPPS = [
    "💡 Bleib immer im Charakter — auch wenn es schwer wird.",
    "💡 Plane deine Aktionen vorher, damit alles realistisch wirkt.",
    "💡 Kommuniziere mit anderen Spielern bevor du große Aktionen startest.",
    "💡 Nutze /deckname um deine RP-Identität festzulegen.",
    "💡 Bei Konflikten: immer zuerst OOC klären, dann IC fortfahren.",
    "💡 Respektiere die Grenzen anderer Spieler — RP macht nur Spaß wenn alle Spaß haben.",
    "💡 Dokumentiere wichtige RP-Events mit Screenshots für spätere Berichte.",
    "💡 Nutze /geheimnis für vertrauliche Infos, die nur bestimmte Leute lesen sollen.",
    "💡 Als Kunde: nutze /kunde damit das Team schnell auf dich aufmerksam wird.",
    "💡 Sei kreativ — je detaillierter deine RP-Beschreibungen, desto besser das Erlebnis.",
]
RP_JOBS = [
    ("🚗 Taxifahrer", "Fahrgäste durch Hamburg kutschieren. Keine Fragen stellen.", "200–500€/h"),
    ("🍕 Pizzabote", "Pakete liefern — was drin ist, geht dich nichts an.", "150–300€/h"),
    ("🔧 Mechaniker", "Fahrzeuge reparieren & 'vorbereiten'. Diskretion garantiert.", "400–800€/h"),
    ("📸 Fotograf", "Personen & Orte dokumentieren. Für wen? Geht dich nichts an.", "300–600€/h"),
    ("🚢 Hafenarbeiter", "Fracht entladen. Augen zu, Mund zu.", "250€/h + Bonus"),
    ("🏥 Sanitäter", "Ersten Versorgung — keine Polizei rufen, unter keinen Umständen.", "500€/h"),
    ("🎰 Kassierer", "Gewinne auszahlen in unserem 'Club'. Kein Quittungsblock nötig.", "350€/h"),
    ("🚁 Pilot", "Kurzstrecken innerhalb Hamburgs. VIP-Transport. Fragen verboten.", "1000€/h"),
]
INFILTRATIONS_ZIELE = [
    "Hamburger Polizeipräsidium", "BKA-Außenstelle Nord", "CIA-Anlaufstelle Speicherstadt",
    "Bundeswehr-Depot Harburg", "Interpol-Büro HafenCity", "UCN-Feindbase Barmbek",
]
BATTLE_KOMMENTARE_GEWINNER = [
    "ohne auch nur ins Schwitzen zu kommen", "in einem blitzschnellen Manöver",
    "nach einem epischen Zweikampf", "mit einem einzigen präzisen Schlag",
    "dank überlegener Geheimdiensttaktik", "durch einen unerwarteten Hinterhalt",
]
BATTLE_KOMMENTARE_VERLIERER = [
    "liegt am Boden und bereut seine Entscheidung",
    "hat keine Chance gehabt", "wurde komplett überrumpelt",
    "muss sich jetzt eine neue Strategie überlegen",
    "ist fürs erste ausgeschaltet", "wird diesen Tag nicht vergessen",
]

# ══════════════════════════════════════════════════════════════════
# 5 TEAM-COMMANDS (Fun & Geil — nur für das Team)
# ══════════════════════════════════════════════════════════════════

# T1 — /geheimtreffen
@bot.tree.command(name="geheimtreffen", description="🤝 [TEAM] Generiert ein geheimes Agenten-Treffen mit Ort & Passwort")
@app_commands.describe(thema="Worum geht es beim Treffen?")
@app_commands.checks.has_permissions(manage_messages=True)
async def geheimtreffen_cmd(interaction: discord.Interaction, thema: str):
    ort = random.choice(HAMBURG_TREFFPUNKTE)
    passwort = f"{random.choice(['Schwarzer','Stiller','Roter','Goldener','Eisiger'])} {random.choice(['Adler','Wolf','Rabe','Falke','Panther'])}"
    uhrzeit = f"{random.randint(19,23)}:{random.choice(['00','15','30','45'])} Uhr"
    embed = discord.Embed(
        title="🤝 GEHEIMES AGENTEN-TREFFEN",
        description=f"**Alle Agenten melden sich 5 Minuten vorher am Treffpunkt.**",
        color=discord.Color.dark_gold(),
        timestamp=datetime.utcnow()
    )
    embed.set_author(name="UCN Einsatzzentrale", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.add_field(name="📍 Treffpunkt",     value=f"`{ort}`",       inline=False)
    embed.add_field(name="🕐 Uhrzeit",        value=f"`{uhrzeit}`",   inline=True)
    embed.add_field(name="🔑 Codewort",       value=f"||`{passwort}`||", inline=True)
    embed.add_field(name="📋 Thema",          value=thema,            inline=False)
    embed.add_field(name="✍️ Einberufen von", value=interaction.user.mention, inline=True)
    embed.set_footer(text="⚠️ Streng geheim — nicht weiterleiten • UCN Geheimdienst")
    await interaction.response.send_message(embed=embed)

# T2 — /ucn_battle
@bot.tree.command(name="ucn_battle", description="⚔️ [TEAM] RP-Kampf zwischen zwei Agenten — wer gewinnt?")
@app_commands.describe(agent1="Erster Agent", agent2="Zweiter Agent")
@app_commands.checks.has_permissions(manage_messages=True)
async def ucn_battle_cmd(interaction: discord.Interaction, agent1: discord.Member, agent2: discord.Member):
    import asyncio
    await interaction.response.defer()
    ladebalken = ["▱▱▱▱▱▱▱▱▱▱", "▰▱▱▱▱▱▱▱▱▱", "▰▰▰▱▱▱▱▱▱▱",
                  "▰▰▰▰▰▱▱▱▱▱", "▰▰▰▰▰▰▰▱▱▱", "▰▰▰▰▰▰▰▰▰▰"]
    lade_embed = discord.Embed(title="⚔️ UCN BATTLE WIRD VORBEREITET...", color=discord.Color.orange())
    lade_embed.description = f"**{agent1.display_name}** vs **{agent2.display_name}**\n\n`▱▱▱▱▱▱▱▱▱▱`"
    msg = await interaction.followup.send(embed=lade_embed)
    for balken in ladebalken[1:]:
        await asyncio.sleep(0.8)
        lade_embed.description = f"**{agent1.display_name}** vs **{agent2.display_name}**\n\n`{balken}`"
        await msg.edit(embed=lade_embed)
    await asyncio.sleep(0.5)
    gewinner, verlierer = random.choice([(agent1, agent2), (agent2, agent1)])
    punkte_g = random.randint(75, 100)
    punkte_v = random.randint(0, 40)
    kommentar_g = random.choice(BATTLE_KOMMENTARE_GEWINNER)
    kommentar_v = random.choice(BATTLE_KOMMENTARE_VERLIERER)
    ergebnis = discord.Embed(
        title="⚔️ UCN BATTLE — ERGEBNIS",
        color=discord.Color.brand_green(),
        timestamp=datetime.utcnow()
    )
    ergebnis.set_thumbnail(url=gewinner.display_avatar.url)
    ergebnis.add_field(name="🏆 SIEGER",    value=f"{gewinner.mention}\n`{punkte_g} Kampfpunkte`",  inline=True)
    ergebnis.add_field(name="💀 VERLIERER", value=f"{verlierer.mention}\n`{punkte_v} Kampfpunkte`", inline=True)
    ergebnis.add_field(name="📖 Kampfbericht", inline=False,
        value=f"{gewinner.mention} hat {kommentar_g} gewonnen.\n{verlierer.mention} {kommentar_v}.")
    ergebnis.add_field(name="✍️ Ausgerichtet von", value=interaction.user.mention, inline=True)
    ergebnis.set_footer(text="UCN Battle System • Undercover Network")
    await msg.edit(embed=ergebnis)

# T3 — /agent_spotlight
@bot.tree.command(name="agent_spotlight", description="🌟 [TEAM] Krönt zufällig einen Agent des Tages")
@app_commands.checks.has_permissions(manage_messages=True)
async def agent_spotlight_cmd(interaction: discord.Interaction):
    echte = [m for m in interaction.guild.members if not m.bot]
    if not echte:
        await interaction.response.send_message("❌ Keine Mitglieder gefunden.", ephemeral=True)
        return
    agent = random.choice(echte)
    titel_pool = [
        "Der unaufhaltbare Schatten", "Der Meister der Tarnung", "Der schnellste Agent im Feld",
        "Der unfehlbare Scharfschütze", "Das Gehirn der Operation", "Der Meister des Verhörs",
        "Der König der Straßen", "Der Legendäre Undercover-Agent",
    ]
    punkte = aktivität.get(agent.id, {}).get("punkte", 0)
    embed = discord.Embed(
        title="🌟 AGENT DES TAGES",
        description=f"Das UCN Hauptquartier ehrt heute einen besonderen Agenten!",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=agent.display_avatar.url)
    embed.set_author(name="UCN Ehrungszeremonie", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.add_field(name="🏆 Agent",        value=agent.mention,                    inline=True)
    embed.add_field(name="🎖️ Ehrentitel",   value=random.choice(titel_pool),        inline=False)
    embed.add_field(name="💠 Aktivitätspunkte", value=f"`{punkte}`",                inline=True)
    embed.add_field(name="🕵️ Deckname",     value=f"`{decknamen.get(agent.id, 'Unbekannt')}`", inline=True)
    embed.set_footer(text="UCN Undercover Network • Täglich wird ein neuer Agent geehrt")
    await interaction.response.send_message(embed=embed)

# T4 — /aktenvernichtung
@bot.tree.command(name="aktenvernichtung", description="🔥 [TEAM] Vernichtet dramatisch die komplette Akte eines Mitglieds")
@app_commands.describe(mitglied="Wessen Akte vernichten?", grund="Warum wird die Akte vernichtet?")
@app_commands.checks.has_permissions(manage_messages=True)
async def aktenvernichtung_cmd(interaction: discord.Interaction, mitglied: discord.Member, grund: str):
    import asyncio
    await interaction.response.defer()
    alte_warns = len(warns.get(mitglied.id, []))
    hatte_auftrag = mitglied.id in aufträge
    hatte_deckname = mitglied.id in decknamen
    warns[mitglied.id] = []
    aufträge.pop(mitglied.id, None)
    decknamen.pop(mitglied.id, None)
    lade = discord.Embed(title="🔥 AKTEN-SCHREDDER WIRD GESTARTET...", color=discord.Color.orange())
    lade.description = "```\n[■□□□□□□□□□] 0%  — Datei wird geladen...\n```"
    msg = await interaction.followup.send(embed=lade)
    stufen = [
        (0.9, "```\n[■■■□□□□□□□] 30% — Verwarnungen werden gelöscht...\n```"),
        (0.9, "```\n[■■■■■■□□□□] 60% — Aufträge werden vernichtet...\n```"),
        (0.9, "```\n[■■■■■■■■□□] 80% — Deckname wird getilgt...\n```"),
        (0.7, "```\n[■■■■■■■■■■] 100% — AKTE VOLLSTÄNDIG VERNICHTET\n```"),
    ]
    for pause, text in stufen:
        await asyncio.sleep(pause)
        lade.description = text
        await msg.edit(embed=lade)
    await asyncio.sleep(0.5)
    ergebnis = discord.Embed(
        title="🔥 AKTE VERNICHTET — STRENG GEHEIM",
        color=discord.Color.dark_red(),
        timestamp=datetime.utcnow()
    )
    ergebnis.set_thumbnail(url=mitglied.display_avatar.url)
    ergebnis.add_field(name="🎯 Ziel",             value=mitglied.mention,            inline=True)
    ergebnis.add_field(name="📋 Grund",            value=grund,                       inline=False)
    ergebnis.add_field(name="⚠️ Verwarnungen",     value=f"`{alte_warns}` gelöscht",  inline=True)
    ergebnis.add_field(name="📝 Auftrag",          value="Vernichtet" if hatte_auftrag else "Keiner",   inline=True)
    ergebnis.add_field(name="🎭 Deckname",         value="Getilgt" if hatte_deckname else "Keiner",     inline=True)
    ergebnis.add_field(name="✍️ Ausgeführt von",   value=interaction.user.mention,    inline=False)
    ergebnis.set_footer(text="⚠️ Diese Aktion ist unwiderruflich • UCN Geheimdienst")
    await msg.edit(embed=ergebnis)

# T5 — /infiltration
@bot.tree.command(name="infiltration", description="🕵️ [TEAM] Generiert ein detailliertes Fake-Infiltrations-Briefing")
@app_commands.describe(agent="Welcher Agent wird eingesetzt?")
@app_commands.checks.has_permissions(manage_messages=True)
async def infiltration_cmd(interaction: discord.Interaction, agent: discord.Member):
    ziel      = random.choice(INFILTRATIONS_ZIELE)
    eintritt  = random.choice(["Hintereingang (Kanalisation)", "Dachzugang (Lüftungsschacht)",
                                "Lieferanten-Zufahrt", "Unterirdischer Tunnel", "Fenster 3. OG Westseite"])
    tarnung   = random.choice(["Reinigungspersonal", "IT-Techniker", "Lieferant", "Journalist", "Sicherheitsbeamter"])
    zeit      = f"{random.randint(0,5):02d}:{random.choice(['00','15','30','45'])} Uhr"
    dauer     = f"{random.randint(15,90)} Minuten"
    schwierig = random.choice(["🟢 NIEDRIG", "🟡 MITTEL", "🟠 HOCH", "🔴 EXTREM"])
    code      = fake_id()
    embed = discord.Embed(
        title=f"🕵️ INFILTRATIONS-BRIEFING — STRENG GEHEIM",
        color=discord.Color.dark_gray(),
        timestamp=datetime.utcnow()
    )
    embed.set_author(name="UCN Einsatzzentrale — LEVEL 5 FREIGABE", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.set_thumbnail(url=agent.display_avatar.url)
    embed.add_field(name="👤 Eingesetzter Agent",  value=agent.mention,      inline=True)
    embed.add_field(name="🎯 Zielobjekt",          value=f"`{ziel}`",        inline=True)
    embed.add_field(name="🚪 Eintritt via",        value=f"`{eintritt}`",    inline=False)
    embed.add_field(name="🎭 Tarnung",             value=f"`{tarnung}`",     inline=True)
    embed.add_field(name="⏰ Einsatzbeginn",       value=f"`{zeit}`",        inline=True)
    embed.add_field(name="⏱️ Geschätzte Dauer",    value=f"`{dauer}`",       inline=True)
    embed.add_field(name="⚠️ Schwierigkeitsgrad",  value=schwierig,          inline=True)
    embed.add_field(name="🔑 Ops-Code",            value=f"||`{code}`||",   inline=True)
    embed.add_field(name="✍️ Briefing von",        value=interaction.user.mention, inline=False)
    embed.set_footer(text="Bei Fehlschlag: keine Kenntnis dieser Mission • UCN Geheimdienst")
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════════════════════════
# 15 PUBLIC COMMANDS (Jeder kann nutzen — auch Kunden)
# ══════════════════════════════════════════════════════════════════

# P1 — /hilfe
@bot.tree.command(name="hilfe", description="❓ Zeigt alle öffentlichen UCN-Commands")
async def hilfe_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="❓ UCN BOT — ÖFFENTLICHE COMMANDS",
        description="Diese Commands stehen **allen Mitgliedern** zur Verfügung:",
        color=discord.Color.dark_gold()
    )
    public_cmds = [
        ("`/kunde`",         "📩 Kundenanfrage ans Team senden"),
        ("`/hilfe`",         "❓ Diese Übersicht anzeigen"),
        ("`/meine_stats`",   "📊 Deine Aktivitätspunkte anzeigen"),
        ("`/mein_profil`",   "👤 Dein UCN-Profil anzeigen"),
        ("`/mein_rang`",     "🏷️ Deine aktuellen Rollen anzeigen"),
        ("`/mein_auftrag`",  "📋 Deinen aktiven Auftrag anzeigen"),
        ("`/münzwurf`",      "🪙 Kopf oder Zahl"),
        ("`/würfeln`",       "🎲 Würfel werfen"),
        ("`/8ball`",         "🎱 Magischen Ball befragen"),
        ("`/zitat`",         "💬 Spionage-Zitat anzeigen"),
        ("`/tipp`",          "💡 Zufälligen RP-Tipp erhalten"),
        ("`/wetter_hamburg`","🌦️ Aktuelles Hamburg-Wetter"),
        ("`/treffpunkt`",    "📍 Zufälligen Treffpunkt in HH generieren"),
        ("`/identität`",     "🪪 Fake RP-Identitätskarte erstellen"),
        ("`/stadtplan`",     "🗺️ Zufälligen Hamburger Stadtteil anzeigen"),
        ("`/ruf_taxi`",      "🚕 [RP] Ein Taxi rufen"),
        ("`/job_angebot`",   "💼 Zufälliges RP-Jobangebot anzeigen"),
        ("`/zufalls_code`",  "🔢 Zufälligen Code generieren"),
        ("`/notruf`",        "🆘 [RP] Einen Notruf absetzen"),
        ("`/feedback`",      "📝 Feedback/Vorschlag ans Team schicken"),
        ("`/ping`",          "🏓 Bot-Latenz anzeigen"),
        ("`/uptime`",        "⏱️ Bot-Laufzeit anzeigen"),
        ("`/user_info`",     "ℹ️ Infos über ein Mitglied"),
        ("`/avatar`",        "🖼️ Profilbild anzeigen"),
        ("`/ucn_info`",      "🕵️ Infos über UCN"),
    ]
    for cmd, desc in public_cmds:
        embed.add_field(name=cmd, value=desc, inline=True)
    embed.set_footer(text="UCN Bot — Notruf Hamburg RP")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# P2 — /meine_stats
@bot.tree.command(name="meine_stats", description="📊 Zeigt deine eigenen Aktivitätspunkte auf dem Server")
async def meine_stats_cmd(interaction: discord.Interaction):
    u = interaction.user
    daten = aktivität.get(u.id)
    embed = discord.Embed(title="📊 DEINE UCN STATISTIKEN", color=discord.Color.blurple(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=u.display_avatar.url)
    if daten:
        rang = sorted(aktivität.keys(), key=lambda x: aktivität[x]["punkte"], reverse=True).index(u.id) + 1
        embed.add_field(name="💠 Aktivitätspunkte", value=f"`{daten['punkte']}`",     inline=True)
        embed.add_field(name="💬 Nachrichten",       value=f"`{daten['nachrichten']}`", inline=True)
        embed.add_field(name="🏅 Server-Rang",       value=f"`#{rang}`",               inline=True)
    else:
        embed.description = "📭 Noch keine Aktivität aufgezeichnet. Schreib etwas im Server!"
    embed.set_footer(text="UCN Undercover Network")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# P3 — /mein_rang
@bot.tree.command(name="mein_rang", description="🏷️ Zeigt deine aktuellen Rollen auf dem Server")
async def mein_rang_cmd(interaction: discord.Interaction):
    u = interaction.user
    rollen = [r for r in u.roles if r.name != "@everyone"]
    embed = discord.Embed(title="🏷️ DEINE ROLLEN", color=u.color, timestamp=datetime.utcnow())
    embed.set_thumbnail(url=u.display_avatar.url)
    embed.add_field(name=f"🏷️ Rollen ({len(rollen)})", value=" ".join(r.mention for r in reversed(rollen)) if rollen else "Keine Rollen", inline=False)
    embed.set_footer(text="UCN Undercover Network")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# P4 — /münzwurf
@bot.tree.command(name="münzwurf", description="🪙 Wirf eine Münze — Kopf oder Zahl?")
async def münzwurf_cmd(interaction: discord.Interaction):
    ergebnis = random.choice(["🪙 KOPF", "🔢 ZAHL"])
    farbe = discord.Color.gold() if "KOPF" in ergebnis else discord.Color.greyple()
    embed = discord.Embed(title="🪙 MÜNZWURF", description=f"# {ergebnis}", color=farbe)
    embed.set_footer(text=f"Geworfen von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

# P5 — /wetter_hamburg
@bot.tree.command(name="wetter_hamburg", description="🌦️ Zeigt das aktuelle RP-Wetter in Hamburg")
async def wetter_hamburg_cmd(interaction: discord.Interaction):
    zustand, temp, wind, sicht = random.choice(HAMBURG_WETTER)
    embed = discord.Embed(title=f"🌆 HAMBURG WETTER — {datetime.now().strftime('%d.%m.%Y')}", color=discord.Color.blue())
    embed.set_author(name="UCN Wetterstation Hamburg")
    embed.add_field(name="🌡️ Zustand",     value=zustand, inline=True)
    embed.add_field(name="🌡️ Temperatur",  value=temp,    inline=True)
    embed.add_field(name="💨 Wind",        value=wind,    inline=True)
    embed.add_field(name="👁️ Sichtbarkeit",value=sicht,   inline=True)
    embed.set_footer(text="UCN Wetterservice • Notruf Hamburg RP")
    await interaction.response.send_message(embed=embed)

# P6 — /treffpunkt
@bot.tree.command(name="treffpunkt", description="📍 Generiert einen zufälligen Treffpunkt in Hamburg")
async def treffpunkt_cmd(interaction: discord.Interaction):
    ort  = random.choice(HAMBURG_TREFFPUNKTE)
    code = f"{random.randint(10,99)}-{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
    embed = discord.Embed(title="📍 ZUFÄLLIGER TREFFPUNKT", color=discord.Color.dark_green())
    embed.add_field(name="🗺️ Ort",       value=f"`{ort}`",  inline=False)
    embed.add_field(name="🔑 Treffcode", value=f"`{code}`", inline=True)
    embed.set_footer(text=f"Generiert für {interaction.user.display_name} • UCN")
    await interaction.response.send_message(embed=embed)

# P7 — /identität
@bot.tree.command(name="identität", description="🪪 Erstellt eine zufällige RP-Identitätskarte für dich")
async def identität_cmd(interaction: discord.Interaction):
    vornamen = ["Klaus","Markus","Stefan","Anna","Julia","Lena","Tobias","Felix","Lukas","Jana"]
    nachnamen = ["Müller","Schmidt","Weber","Fischer","Wagner","Becker","Schulz","Richter","Koch","Bauer"]
    berufe = ["Freier Journalist","Sicherheitsberater","Privatdetektiv","Unternehmensberater",
              "Import/Export Händler","Logistikmanager","Freier Fotograf","Sprachlehrer"]
    vorname   = random.choice(vornamen)
    nachname  = random.choice(nachnamen)
    geburtsjahr = random.randint(1975, 2000)
    ausweis_nr  = fake_id()
    beruf       = random.choice(berufe)
    stadtteil   = random.choice(HAMBURG_STADTTEILE)
    embed = discord.Embed(
        title="🪪 HAMBURGER PERSONALAUSWEIS — RP",
        color=discord.Color.dark_blue(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="👤 Name",         value=f"`{vorname} {nachname}`",        inline=True)
    embed.add_field(name="🎂 Geburtsjahr",  value=f"`{geburtsjahr}`",               inline=True)
    embed.add_field(name="🏠 Wohnort",      value=f"`{stadtteil}`",                 inline=True)
    embed.add_field(name="💼 Beruf",        value=f"`{beruf}`",                     inline=True)
    embed.add_field(name="🔢 Ausweis-Nr.",  value=f"`{ausweis_nr}`",               inline=True)
    embed.set_footer(text=f"RP-Identität für {interaction.user.display_name} • UCN Notruf Hamburg")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# P8 — /stadtplan
@bot.tree.command(name="stadtplan", description="🗺️ Zeigt Infos zu einem zufälligen Hamburger Stadtteil")
async def stadtplan_cmd(interaction: discord.Interaction):
    stadtteil = random.choice(HAMBURG_STADTTEILE)
    aktivität_level = random.choice(["🔴 HOCH — starke Polizeipräsenz", "🟡 MITTEL — gelegentliche Streifen",
                                      "🟢 NIEDRIG — kaum Überwachung"])
    kontrollpunkte = random.randint(0, 4)
    embed = discord.Embed(title=f"🗺️ STADTTEIL: {stadtteil.upper()}", color=discord.Color.dark_teal())
    embed.add_field(name="📡 Aktivitätslevel",      value=aktivität_level,         inline=False)
    embed.add_field(name="🚔 Kontrollpunkte",       value=f"`{kontrollpunkte}`",   inline=True)
    embed.add_field(name="🔒 Sicherheitsstufe",     value=f"`{random.randint(1,5)}/5`", inline=True)
    embed.add_field(name="📍 UCN-Präsenz",          value=random.choice(["Bekannt","Unbekannt","Vermutet"]), inline=True)
    embed.set_footer(text="UCN Feldkarte • Notruf Hamburg RP")
    await interaction.response.send_message(embed=embed)

# P9 — /ruf_taxi
@bot.tree.command(name="ruf_taxi", description="🚕 [RP] Ruft ein Taxi — bekomme einen Fahrer und eine ETA")
async def ruf_taxi_cmd(interaction: discord.Interaction):
    fahrer_namen = ["Klaus K.","Mehmet A.","Igor P.","Sven L.","Tariq M.","Osman D."]
    kennzeichen  = f"HH-{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')} {random.randint(100,999)}"
    fahrzeug     = random.choice(["Mercedes E-Klasse (Weiß)","Toyota Prius (Schwarz)","Skoda Octavia (Silber)","VW Passat (Dunkelblau)"])
    eta          = random.randint(3, 15)
    embed = discord.Embed(title="🚕 TAXI GERUFEN!", color=discord.Color.yellow(), timestamp=datetime.utcnow())
    embed.add_field(name="👤 Fahrer",       value=f"`{random.choice(fahrer_namen)}`", inline=True)
    embed.add_field(name="🚗 Fahrzeug",     value=f"`{fahrzeug}`",                    inline=True)
    embed.add_field(name="🔢 Kennzeichen",  value=f"`{kennzeichen}`",                 inline=True)
    embed.add_field(name="⏱️ ETA",          value=f"`{eta} Minuten`",                 inline=True)
    embed.set_footer(text=f"Gerufen von {interaction.user.display_name} • UCN Notruf Hamburg RP")
    await interaction.response.send_message(embed=embed)

# P10 — /job_angebot
@bot.tree.command(name="job_angebot", description="💼 Zeigt ein zufälliges RP-Jobangebot in Hamburg")
async def job_angebot_cmd(interaction: discord.Interaction):
    job, beschreibung, lohn = random.choice(RP_JOBS)
    embed = discord.Embed(title=f"💼 JOBANGEBOT: {job}", color=discord.Color.dark_green(), timestamp=datetime.utcnow())
    embed.add_field(name="📋 Beschreibung", value=beschreibung, inline=False)
    embed.add_field(name="💰 Lohn",         value=f"`{lohn}`",  inline=True)
    embed.add_field(name="📍 Standort",     value=f"`{random.choice(HAMBURG_STADTTEILE)}`", inline=True)
    embed.set_footer(text="⚠️ Diskretion wird vorausgesetzt • UCN Notruf Hamburg RP")
    await interaction.response.send_message(embed=embed)

# P11 — /zufalls_code
@bot.tree.command(name="zufalls_code", description="🔢 Generiert einen zufälligen Geheim-Code")
async def zufalls_code_cmd(interaction: discord.Interaction):
    code = '-'.join(''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4)) for _ in range(3))
    embed = discord.Embed(title="🔢 ZUFALLS-CODE GENERIERT", description=f"## `{code}`", color=discord.Color.blurple())
    embed.set_footer(text=f"Nur einmalig gültig • Generiert von {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# P12 — /tipp
@bot.tree.command(name="tipp", description="💡 Erhalte einen zufälligen RP-Tipp für Notruf Hamburg")
async def tipp_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="💡 UCN RP-TIPP", description=random.choice(RP_TIPPS), color=discord.Color.gold())
    embed.set_footer(text="UCN Notruf Hamburg RP • Viel Spaß beim Spielen!")
    await interaction.response.send_message(embed=embed)

# P13 — /notruf
@bot.tree.command(name="notruf", description="🆘 [RP] Setzt einen Notruf ab — das Team wird benachrichtigt")
@app_commands.describe(situation="Was ist die Notlage?", ort="Wo bist du?")
async def notruf_cmd(interaction: discord.Interaction, situation: str, ort: str = "Unbekannt"):
    guild = interaction.guild
    team_rolle = discord.utils.get(guild.roles, name=TEAM_ROLLE_NAME)
    team_erwähnung = team_rolle.mention if team_rolle else f"@{TEAM_ROLLE_NAME}"
    notruf_nr = random.randint(10000, 99999)
    embed = discord.Embed(
        title="🆘 NOTRUF EINGEGANGEN",
        description=f"**Ein Mitglied benötigt sofort Hilfe!**",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="🆘 Notruf-Nr.",   value=f"`#{notruf_nr}`",          inline=True)
    embed.add_field(name="👤 Melder",        value=interaction.user.mention,   inline=True)
    embed.add_field(name="📍 Ort",           value=f"`{ort}`",                 inline=True)
    embed.add_field(name="🚨 Situation",     value=situation,                  inline=False)
    embed.set_footer(text="UCN Notfallzentrale • Notruf Hamburg RP")
    await interaction.response.send_message(
        content=f"🚨 {team_erwähnung} — **NOTRUF #{notruf_nr}!**",
        embed=embed
    )

# P14 — /ucn_info
@bot.tree.command(name="ucn_info", description="🕵️ Zeigt Informationen über das UCN — Notruf Hamburg RP")
async def ucn_info_cmd(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(
        title="🕵️ UNDERCOVER NETWORK — UCN",
        description=(
            "**UCN** *(Undercover Network)* ist das Herzstück von **Notruf Hamburg RP**.\n\n"
            "Wir sind ein Roleplay-Server basierend auf Hamburg, Deutschland.\n"
            "Hier treffen Polizei, Geheimdienst, Gangs und Zivilisten aufeinander."
        ),
        color=discord.Color.dark_gold(),
        timestamp=datetime.utcnow()
    )
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="🏠 Server",          value=f"`{g.name}`",                        inline=True)
    embed.add_field(name="👥 Mitglieder",       value=f"`{g.member_count}`",                inline=True)
    embed.add_field(name="🚀 Boost-Stufe",      value=f"`{g.premium_tier}`",               inline=True)
    embed.add_field(name="📋 Ticket-System",    value="✅ Aktiv (`/ticket_panel`)",         inline=True)
    embed.add_field(name="📩 Kundenanfragen",   value="✅ Aktiv (`/kunde`)",                inline=True)
    embed.add_field(name="🤖 Bot-Version",      value="`UCN Bot v2.0`",                    inline=True)
    embed.add_field(
        name="📖 Wichtige Commands für Kunden",
        value="`/kunde` — Anfrage ans Team\n`/notruf` — Notfall melden\n`/hilfe` — Alle Commands\n`/feedback` — Vorschlag senden",
        inline=False
    )
    embed.set_footer(text="UCN Undercover Network • Notruf Hamburg RP")
    await interaction.response.send_message(embed=embed)

# P15 — /feedback
@bot.tree.command(name="feedback", description="📝 Schicke ein Feedback oder einen Vorschlag ans Team")
@app_commands.describe(betreff="Kurzer Betreff", nachricht="Dein Feedback oder dein Vorschlag")
async def feedback_cmd(interaction: discord.Interaction, betreff: str, nachricht: str):
    guild = interaction.guild
    team_rolle = discord.utils.get(guild.roles, name=TEAM_ROLLE_NAME)
    team_erwähnung = team_rolle.mention if team_rolle else f"@{TEAM_ROLLE_NAME}"
    feedback_nr = random.randint(1000, 9999)
    embed = discord.Embed(
        title=f"📝 FEEDBACK #{feedback_nr} — {betreff}",
        description=nachricht,
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="👤 Von",      value=interaction.user.mention,      inline=True)
    embed.add_field(name="📅 Zeit",     value=now_str(),                     inline=True)
    embed.set_footer(text=f"UCN Feedback-System • ID #{feedback_nr}")
    log_kanal = bot.get_channel(KUNDE_LOG_KANAL_ID)
    if log_kanal:
        await log_kanal.send(content=f"📝 Neues Feedback von {interaction.user.mention}", embed=embed)
    await interaction.response.send_message(
        f"✅ Dein Feedback wurde ans Team gesendet! **Feedback-Nr.: #{feedback_nr}**\nDanke für deine Meinung! 🙏",
        ephemeral=True
    )

# ── Error Handler ──────────────────────────────────────────────────
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Du hast keine Berechtigung für diesen Befehl.", ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message("❌ Der Bot hat nicht genug Rechte.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Fehler: {str(error)}", ephemeral=True)

# ── Web-Server für Deployment (Replit braucht einen HTTP-Endpunkt) ─
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/api/healthz", "/api/ping", "/"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"UCN Bot laeuft!")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def webserver_starten():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        print(f"✅ Webserver auf Port {port} gestartet (für Deployment)")
        server.serve_forever()
    except OSError:
        print("⚠️ Webserver-Port bereits belegt (Dev-Modus) — wird übersprungen")

Thread(target=webserver_starten, daemon=True).start()

# ── Start ──────────────────────────────────────────────────────────
token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ist nicht gesetzt.")

bot.run(token)
