import discord
from discord.ext import commands
import threading
import secrets
import os
import json
from flask import Flask, render_template, request, jsonify

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

ROLE_ALLOWED = 1329516197175103651

BOT_ID = os.getenv("BOT_ID") or "123456789012345678"

bot = commands.Bot(command_prefix="%", intents=intents, self_bot=False)
app = Flask(__name__, template_folder="templates")

# Simple dict for session keys (you can migrate this to a database)
session_keys = {}  # key -> user_id

# ---- DISCORD BOT COMMANDS ----

def generate_key():
    """Genera una clave segura de máximo 98 caracteres."""
    return secrets.token_urlsafe(72)[:98]  

@bot.command()
async def generar_key(ctx):
    if not any(r.id == ROLE_ALLOWED for r in ctx.author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return
    key = generate_key()
    session_keys[key] = ctx.author.id
    await ctx.send(f"🔑 Tu clave única es: `{key}`")

@bot.command()
async def ver_users(ctx):
    if not any(r.id == ROLE_ALLOWED for r in ctx.author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return
    user_list = []
    for key, user_id in session_keys.items():
        user = bot.get_user(user_id)
        if user:
            user_list.append(f"{user.name} (`{key}`)")
        else:
            user_list.append(f"{user_id} (`{key}`)")
    await ctx.send("Usuarios y sus claves generadas:\n" + "\n".join(user_list))

@bot.command()
async def ban(ctx, user_ref: str, *, reason: str = "No reason provided"):
    if not any(r.id == ROLE_ALLOWED for r in ctx.author.roles):
        await ctx.send("⛔ No tienes acceso a este comando.")
        return

    member = None
    if user_ref.isdigit():
        member = ctx.guild.get_member(int(user_ref))
    elif user_ref.startswith("<@") and user_ref.endswith(">"):
        idnum = user_ref.replace("<@", "").replace(">", "")
        member = ctx.guild.get_member(int(idnum))
    if not member:
        await ctx.send("❌ El usuario no está en el servidor.")
        return

    try:
        await ctx.guild.ban(member, reason=reason, delete_message_seconds=86400)
        await ctx.send(f"✅ Usuario {member.mention} baneado de forma manual.\nRazón: {reason}")
    except Exception as e:
        await ctx.send(f"❌ Error al banear: {e}")

# ---- FLASK WEB ROUTES ----

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/banear_json', methods=['POST'])
def api_banear_json():
    data = request.get_json()
    key = data.get("key")
    server_id = int(data.get("server_id"))
    users = data.get("users", [])
    if not key or key not in session_keys:
        return jsonify({"error": "Clave inválida"}), 400

    # No ejecuta el ban directo aquí (no async), pero puedes guardar la petición para procesarla en el bot
    # Opcional: guardar en archivo temporal, cola, base de datos, etc
    # Ejemplo respuesta:
    return jsonify({"message": f"{len(users)} usuarios recibidos para banear en servidor {server_id}."})

@app.route('/api/banear_manual', methods=['POST'])
def api_banear_manual():
    data = request.get_json()
    key = data.get("key")
    server_id = int(data.get("server_id"))
    user = data.get("user")
    if not key or key not in session_keys:
        return jsonify({"error": "Clave inválida"}), 400

    # Igual que arriba, procesar la solicitud asíncronamente en el bot
    return jsonify({"message": f"Usuario {user} reservado para banear en servidor {server_id}."})

# ---- MAIN ENTRY POINT ----

def run_bot():
    bot.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
