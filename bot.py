import discord
from discord.ext import commands
import os
import json
import secrets
import asyncio
from flask import Flask, render_template_string, request, jsonify

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

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Banear Usuarios</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .header select {
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: #007bff;
            color: #fff;
        }
        .options {
            display: flex;
            gap: 20px;
        }
        .option {
            flex: 1;
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
        }
        .option h2 {
            margin-top: 0;
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
        }
        input[type="text"], select, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #007bff;
            color: #fff;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Dashboard de Banear Usuarios</h1>
            <select id="server">
                <option value="1">Servidor 1</option>
                <option value="2">Servidor 2</option>
            </select>
        </div>
        <div class="options">
            <div class="option">
                <h2>Cargar JSON para Banear</h2>
                <div class="form-group">
                    <label for="json">Sube el archivo JSON:</label>
                    <input type="file" id="json" accept=".json">
                </div>
                <button onclick="banearJson()">Banear</button>
            </div>
            <div class="option">
                <h2>Banear Manualmente</h2>
                <div class="form-group">
                    <label for="user">Banear por ID o @usuario:</label>
                    <input type="text" id="user" placeholder="Ingresa ID o @usuario">
                </div>
                <button onclick="banearManual()">Banear</button>
            </div>
        </div>
    </div>
    <script>
        function banearJson() {
            const jsonFile = document.getElementById('json').files[0];
            if (!jsonFile) {
                alert('Por favor, sube un archivo JSON.');
                return;
            }
            // Aquí iría la lógica para enviar la solicitud al bot
            alert('Solicitud enviada. El bot procesará tu petición.');
        }

        function banearManual() {
            const user = document.getElementById('user').value;
            if (!user) {
                alert('Por favor, ingresa un ID o @usuario.');
                return;
            }
            // Aquí iría la lógica para enviar la solicitud al bot
            alert('Solicitud enviada. El bot procesará tu petición.');
        }
    </script>
</body>
</html>
    ''')

@app.route('/banear', methods=['POST'])
def banear():
    data = request.json
    key = data.get('key')
    server = data.get('server')
    users = data.get('users')
    if key not in keys:
        return jsonify({'error': 'Clave inválida'}), 400
    # Aquí iría la lógica para banear usuarios
    return jsonify({'message': 'Usuarios baneados'})

@app.route('/banear_manual', methods=['POST'])
def banear_manual():
    data = request.json
    key = data.get('key')
    server = data.get('server')
    user = data.get('user')
    if key not in keys:
        return jsonify({'error': 'Clave inválida'}), 400
    # Aquí iría la lógica para banear manualmente
    return jsonify({'message': 'Usuario baneado'})

def run_bot():
    bot.run(os.getenv("DISCORD_TOKEN"))

if __name__ == '__main__':
    # Inicia el bot en un hilo separado
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    # Inicia la aplicación Flask
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
