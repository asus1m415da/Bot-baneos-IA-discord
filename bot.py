import discord
from discord.ext import commands
from discord import ui
from groq import Groq
import os
import json

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

ROLE_ALLOWED = 1329516197175103651

# Solicita el bot_id al iniciar
BOT_ID = input("Ingresa el ID del bot: ").strip()
if not BOT_ID.isdigit():
    raise ValueError("El ID del bot debe ser un número.")

bot = commands.Bot(command_prefix="%", intents=intents, self_bot=False)
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
    if ia_reason.lower().strip() == user_input.lower().strip():
        ia_reason = "Incumplimiento de normas comunitarias detectado y comportamiento que sugiere riesgo para la seguridad del servidor."
    return ia_reason

class BanMultipleView(ui.View):
    def __init__(self, users, guild, reason):
        super().__init__()
        self.users = users
        self.guild = guild
        self.reason = reason

    @ui.button(label="🚫 Banear usuarios", style=discord.ButtonStyle.danger)
    async def ban_users(self, interaction: discord.Interaction, button: ui.Button):
        banned = []
        for user_id, username in self.users:
            try:
                member = self.guild.get_member(int(user_id))
                if member:
                    await self.guild.ban(member, reason=self.reason, delete_message_seconds=86400)
                    banned.append(f"{username} ({user_id})")
            except Exception as e:
                print(f"Error al banear {username} ({user_id}): {e}")
        await interaction.response.send_message(f"✅ Usuarios baneados: {', '.join(banned)}")

    @ui.button(label="🎭 No banear a los usuarios que están aquí", style=discord.ButtonStyle.secondary)
    async def skip_present(self, interaction: discord.Interaction, button: ui.Button):
        filtered = []
        for user_id, username in self.users:
            member = self.guild.get_member(int(user_id))
            if not member:
                filtered.append(f"{username} ({user_id})")
        if filtered:
            await interaction.response.send_message(f"✅ Usuarios no baneados (no estaban en el servidor): {', '.join(filtered)}")
        else:
            await interaction.response.send_message("✅ No hay usuarios en el archivo que no estén en el servidor.")

@bot.command()
async def banear_multiple(ctx, attachment: discord.Attachment):
    if not any(r.id == ROLE_ALLOWED for r in ctx.author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return

    if not attachment.filename.endswith('.json'):
        await ctx.send("❌ Solo se aceptan archivos JSON.")
        return

    try:
        content = await attachment.read()
        data = json.loads(content)
        users = [(user['id'], user['username']) for user in data if 'id' in user and 'username' in user]
        if not users:
            await ctx.send("❌ No se encontraron usuarios en el archivo.")
            return

        present = []
        not_present = []
        for user_id, username in users:
            member = ctx.guild.get_member(int(user_id))
            if member:
                present.append(f"{username} ({user_id}) ⚠️ está en el servidor")
            else:
                not_present.append(f"{username} ({user_id})")

        embed = discord.Embed(
            title="⚠️ Usuarios a banear",
            description="Los siguientes usuarios serán baneados:",
            color=discord.Color.orange()
        )
        if present:
            embed.add_field(name="⚠️ Están en el servidor", value="\n".join(present), inline=False)
        if not_present:
            embed.add_field(name="✅ No están en el servidor", value="\n".join(not_present), inline=False)

        view = BanMultipleView(users, ctx.guild, groq_ban_reason(""))
        await ctx.send(embed=embed, view=view)
    except Exception as e:
        await ctx.send(f"❌ Error al procesar el archivo: {e}")

@bot.event
async def on_ready():
    print(f"{bot.user} está en línea.")
    # Actualiza los comandos
    await bot.tree.sync()

bot.run(os.getenv("DISCORD_TOKEN"))
