import discord
from discord.ext import commands
import threading
import secrets
import os
import json
import queue
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

ROLE_ALLOWED = 1329516197175103651

BOT_ID = os.getenv("BOT_ID") or "123456789012345678"

bot = commands.Bot(command_prefix="%", intents=intents, self_bot=False)
app = Flask(__name__, template_folder="templates")
app.secret_key = secrets.token_urlsafe(32)  # Necesario para sesiones

session_keys = {}  # key -> user_id
ban_queue = queue.Queue()

def generate_key():
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

# --- FLASK WEB API PARA GUI ---

@app.route('/')
def index():
    key = request.args.get('key')
    if not key or key not in session_keys:
        return redirect(url_for('login'))
    session['key'] = key
    return render_template("index.html")

@app.route('/login')
def login():
    return '''
    <h2>Ingresa tu clave para acceder</h2>
    <form action="/check_key" method="POST">
        <input type="text" name="key" placeholder="Ingresa tu clave" required>
        <button type="submit">Acceder</button>
    </form>
    '''

@app.route('/check_key', methods=['POST'])
def check_key():
    key = request.form.get('key')
    if key in session_keys:
        session['key'] = key
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/api/servidores', methods=['GET'])
def api_servidores():
    if 'key' not in session or session['key'] not in session_keys:
        return jsonify({"error": "Acceso denegado"}), 401
    servidores = [
        {"id": str(guild.id), "name": guild.name}
        for guild in bot.guilds
    ]
    return jsonify(servidores)

@app.route('/api/verificar_usuarios', methods=['POST'])
def api_verificar_usuarios():
    if 'key' not in session or session['key'] not in session_keys:
        return jsonify({"error": "Acceso denegado"}), 401
    data = request.get_json()
    server_id = int(data.get("server_id"))
    users = data.get("users", [])

    guild = discord.utils.get(bot.guilds, id=server_id)
    if not guild:
        return jsonify({"error": "Servidor no encontrado"}), 404

    result = []
    for user in users:
        user_id = int(user.get("id"))
        username = user.get("username")
        member = guild.get_member(user_id)
        if member:
            result.append({"username": username, "id": user_id, "status": "presente"})
        else:
            result.append({"username": username, "id": user_id, "status": "no presente"})

    return jsonify(result)

@app.route('/api/banear_json', methods=['POST'])
def api_banear_json():
    if 'key' not in session or session['key'] not in session_keys:
        return jsonify({"error": "Acceso denegado"}), 401
    data = request.get_json()
    server_id = int(data.get("server_id"))
    users = data.get("users", [])
    reason = data.get("reason", "Ban desde dashboard")

    guild = discord.utils.get(bot.guilds, id=server_id)
    if not guild:
        return jsonify({"error": "Servidor no encontrado"}), 404

    result = []
    for user in users:
        user_id = int(user.get("id"))
        username = user.get("username")
        ban_queue.put({"guild_id": server_id, "user_id": user_id, "reason": reason})
        result.append(username)

    return jsonify({"message": f"{len(result)} usuarios enviados para banear.", "banned": result})

@app.route('/api/banear_manual', methods=['POST'])
def api_banear_manual():
    if 'key' not in session or session['key'] not in session_keys:
        return jsonify({"error": "Acceso denegado"}), 401
    data = request.get_json()
    server_id = int(data.get("server_id"))
    user_ref = data.get("user")
    reason = data.get("reason", "Ban manual desde dashboard")

    user_id = None
    if user_ref.isdigit():
        user_id = int(user_ref)
    elif user_ref and user_ref.startswith("<@") and user_ref.endswith(">"):
        idnum = user_ref.replace("<@", "").replace(">", "")
        if idnum.isdigit():
            user_id = int(idnum)

    if not user_id:
        return jsonify({"error": "ID de usuario inválido"}), 400

    ban_queue.put({"guild_id": server_id, "user_id": user_id, "reason": reason})
    return jsonify({"message": f"Usuario {user_ref} enviado para banear."})

# --- Tarea asíncrona de procesamiento de baneo ---
import asyncio

async def process_bans():
    await bot.wait_until_ready()
    while True:
        try:
            task = ban_queue.get(block=False)
        except queue.Empty:
            await asyncio.sleep(3)
            continue

        guild = discord.utils.get(bot.guilds, id=task["guild_id"])
        if not guild:
            continue

        member = guild.get_member(task["user_id"])
        if member:
            try:
                await guild.ban(member, reason=task["reason"], delete_message_seconds=86400)
                print(f"Usuario {member.name} ({member.id}) baneado en {guild.name}")
            except Exception as e:
                print(f"Error banear {task['user_id']} en {guild.name}: {e}")
        else:
            try:
                await guild.ban(discord.Object(id=task["user_id"]), reason=task["reason"], delete_message_seconds=86400)
                print(f"Usuario {task['user_id']} forcebaneado en {guild.name}")
            except Exception as e:
                print(f"Error forceban {task['user_id']} en {guild.name}: {e}")

        ban_queue.task_done()

@bot.event
async def on_ready():
    print(f"{bot.user} está en línea.")
    bot.loop.create_task(process_bans())

def run_bot():
    bot.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
