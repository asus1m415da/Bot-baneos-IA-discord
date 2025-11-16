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

def groq_ban_reason():
    completion = groq_client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[{"role": "user", "content": "Genera una razón profesional y justificable de porqué banear a un usuario por infiltración/raid en un servidor Discord, justifica objetivamente."}],
        temperature=0.6,
        max_completion_tokens=1024,
        top_p=1,
        stream=False
    )
    return completion.choices[0].message.content.strip()

class BanView(ui.View):
    def __init__(self, user, reason, guild):
        super().__init__()
        self.target = user
        self.reason = reason
        self.guild = guild

    @ui.button(label="Enviar baneo", style=discord.ButtonStyle.danger)
    async def send_ban(self, interaction: discord.Interaction, button: ui.Button):
        try:
            await self.guild.ban(self.target, reason=self.reason, delete_message_days=1)
            await interaction.response.send_message(f"✅ Usuario `{self.target}` baneado.\nRazón: {self.reason}")
        except Exception as err:
            await interaction.response.send_message(f"❌ Error: {err}")

    @ui.button(label="Regenerar razón", style=discord.ButtonStyle.secondary)
    async def regenerate_reason(self, interaction: discord.Interaction, button: ui.Button):
        new_reason = groq_ban_reason()
        self.reason = new_reason
        await interaction.response.edit_message(content=f"Razón generada por IA:\n{new_reason}", view=self)

def get_user(ctx, identifier):
    if identifier.isdigit():
        return ctx.guild.get_member(int(identifier)) or discord.Object(id=int(identifier))
    if identifier.startswith("<@") and identifier.endswith(">"):
        idnum = identifier.replace("<@", "").replace(">", "")
        return ctx.guild.get_member(int(idnum)) or discord.Object(id=int(idnum))
    return None

@bot.command()
async def ban(ctx, user_ref: str, *, reason: str = None):
    author = ctx.author
    if not any(r.id == ROLE_ALLOWED for r in author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return
    user_obj = get_user(ctx, user_ref)
    if user_obj is None:
        await ctx.send("❓ No se pudo identificar el usuario.")
        return
    mot = reason or groq_ban_reason()
    view = BanView(user_obj, mot, ctx.guild)
    await ctx.send(f"Confirmar baneo a `{user_ref}`.\nRazón:\n{mot}", view=view)

@bot.event
async def on_ready():
    print(f"{bot.user} está en línea.")

bot.run(os.getenv("DISCORD_TOKEN"))
