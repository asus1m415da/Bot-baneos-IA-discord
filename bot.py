import discord
from discord.ext import commands
import os
import json
import secrets
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

ROLE_ALLOWED = 1329516197175103651

BOT_ID = os.getenv("BOT_ID")
if not BOT_ID:
    BOT_ID = "123456789012345678"  # Reemplaza con el ID de tu bot

bot = commands.Bot(command_prefix="%", intents=intents, self_bot=False)

# Almacena claves generadas
keys = {}

def generate_key():
    return secrets.token_urlsafe(72)[:98]

@bot.command()
async def generar_key(ctx):
    if not any(r.id == ROLE_ALLOWED for r in ctx.author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return
    key = generate_key()
    keys[key] = ctx.author.id
    await ctx.send(f"🔑 Tu clave única es: `{key}`")

@bot.command()
async def ver_users(ctx):
    if not any(r.id == ROLE_ALLOWED for r in ctx.author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return
    users = [bot.get_user(user_id).name for user_id in keys.values()]
    await ctx.send(f"Usuarios que generaron clave: {', '.join(users)}")

@bot.command()
async def ban(ctx, user_ref: str, *, reason: str = None):
    if not any(r.id == ROLE_ALLOWED for r in ctx.author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return
    if user_ref.isdigit():
        member = ctx.guild.get_member(int(user_ref))
    elif user_ref.startswith("<@") and user_ref.endswith(">"):
        idnum = user_ref.replace("<@", "").replace(">", "")
        member = ctx.guild.get_member(int(idnum))
    else:
        await ctx.send("❓ No se pudo identificar el usuario. Usa ID o mención.")
        return
    if not member:
        await ctx.send("❌ El usuario no está en el servidor.")
        return
    try:
        await ctx.guild.ban(member, reason=reason, delete_message_seconds=86400)
        await ctx.send(f"✅ Usuario {member.mention} baneado.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.event
async def on_ready():
    print(f"{bot.user} está en línea.")
    await bot.tree.sync()

def run_bot():
    bot.run(os.getenv("DISCORD_TOKEN"))
