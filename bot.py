import discord
from discord.ext import commands
from discord import ui
from groq import Groq
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

ROLE_ALLOWED = 1329516197175103651

bot = commands.Bot(command_prefix="%", intents=intents)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def groq_ban_reason(user_input):
    prompt = (
        f"Reformula y mejora profesionalmente este motivo de baneo para Discord, justificando la acción sin repetir literalmente el texto original: '{user_input}'."
        if user_input else
        "Genera una razón profesional y justificada para banear a un usuario sospechoso de infiltración o raid en Discord."
    )
    completion = groq_client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75,
        max_completion_tokens=256,
        top_p=1,
        stream=False
    )
    ia_reason = completion.choices[0].message.content.strip()
    # Control antirrepetición directa (por si la IA no lo parafrasea)
    if ia_reason.lower().strip() == user_input.lower().strip():
        ia_reason = "Incumplimiento de normas comunitarias detectado y comportamiento que sugiere riesgo para la seguridad del servidor."
    return ia_reason

class BanView(ui.View):
    def __init__(self, target_id, target_user, reason, guild):
        super().__init__()
        self.target_id = target_id
        self.target_user = target_user
        self.reason = reason
        self.guild = guild

    @ui.button(label="Enviar baneo", style=discord.ButtonStyle.danger)
    async def send_ban(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Notificar por DM si está en el servidor
            if self.target_user:
                dm_message = f"Has sido baneado de {self.guild.name}.\nRazón: {self.reason}"
                try:
                    await self.target_user.send(dm_message)
                except Exception:
                    pass
            # Forceban real
            await self.guild.ban(discord.Object(id=int(self.target_id)), reason=self.reason, delete_message_seconds=86400)
            display = getattr(self.target_user, "mention", f"`{self.target_id}`")
            await interaction.response.send_message(f"✅ Usuario {display} baneado.\nRazón: {self.reason}")
        except Exception as err:
            await interaction.response.send_message(f"❌ Error: {err}")

    @ui.button(label="Regenerar razón", style=discord.ButtonStyle.secondary)
    async def regenerate_reason(self, interaction: discord.Interaction, button: ui.Button):
        new_reason = groq_ban_reason(self.reason)
        self.reason = new_reason
        await interaction.response.edit_message(content=f"Razón sugerida:\n{new_reason}", view=self)

def get_user_and_id(ctx, identifier):
    if identifier.isdigit():
        member = ctx.guild.get_member(int(identifier))
        return identifier, member
    if identifier.startswith("<@") and identifier.endswith(">"):
        idnum = identifier.replace("<@", "").replace(">", "")
        member = ctx.guild.get_member(int(idnum))
        return idnum, member
    return identifier, None

@bot.command()
async def ban(ctx, user_ref: str, *, reason: str = None):
    if not any(r.id == ROLE_ALLOWED for r in ctx.author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return
    target_id, target_user = get_user_and_id(ctx, user_ref)
    if not target_id.isdigit():
        await ctx.send("❓ No se pudo identificar el usuario. Usa ID o mención.")
        return
    mot = groq_ban_reason(reason or "")
    view = BanView(target_id, target_user, mot, ctx.guild)
    display = getattr(target_user, "mention", f"`{target_id}`")
    await ctx.send(f"Confirmar baneo a {display}.\nRazón:\n{mot}", view=view)

@bot.event
async def on_ready():
    print(f"{bot.user} está en línea.")

bot.run(os.getenv("DISCORD_TOKEN"))
