import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Variables de entorno requeridas
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_ID = os.getenv('BOT_ID')

if not DISCORD_TOKEN:
    raise EnvironmentError("❌ DISCORD_TOKEN no encontrado. Define la variable de entorno.")
if not BOT_ID:
    raise EnvironmentError("❌ BOT_ID no encontrado. Define la variable de entorno.")

# Configuración del bot
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

class MiBotBaneos(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.application_id = int(BOT_ID)
    
    async def setup_hook(self):
        # Registrar comandos con el BOT_ID
        await self.tree.sync()
        print(f'✅ Comandos sincronizados con BOT_ID: {self.application_id}')

bot = MiBotBaneos()

@bot.event
async def on_ready():
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(f'🤖 Bot conectado: {bot.user.name}')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'🌐 Servidores: {len(bot.guilds)}')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

@bot.tree.command(name="banear_json", description="🔨 Banea usuarios masivamente desde un archivo JSON")
@app_commands.describe(archivo="📁 Archivo JSON con IDs de usuarios a banear")
@app_commands.checks.has_permissions(ban_members=True)
async def banear_json(interaction: discord.Interaction, archivo: discord.Attachment):
    # Verificar extensión
    if not archivo.filename.endswith('.json'):
        embed = discord.Embed(
            title="❌ Archivo Inválido",
            description="Por favor sube un archivo con extensión **`.json`**",
            color=0xED4245
        )
        embed.set_footer(text="Sistema de Baneos Masivos", icon_url=bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Embed de procesamiento
    embed_procesando = discord.Embed(
        title="⏳ Procesando Archivo",
        description="📂 Analizando JSON y verificando usuarios en el servidor...",
        color=0x5865F2
    )
    embed_procesando.add_field(
        name="📊 Estado",
        value="🔄 Leyendo archivo JSON\n🔍 Identificando usuarios\n⚙️ Preparando baneos",
        inline=False
    )
    if archivo.url:
        embed_procesando.set_thumbnail(url=archivo.url)
    embed_procesando.set_footer(
        text=f"Solicitado por {interaction.user.name}",
        icon_url=interaction.user.display_avatar.url
    )
    embed_procesando.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed_procesando)
    
    try:
        # Leer archivo JSON
        contenido = await archivo.read()
        datos = json.loads(contenido.decode('utf-8'))
        
        # Extraer IDs
        user_ids = []
        if isinstance(datos, list):
            for item in datos:
                if isinstance(item, dict):
                    user_id = item.get('id') or item.get('user_id') or item.get('userId')
                    if user_id:
                        user_ids.append(int(user_id))
                elif isinstance(item, (int, str)):
                    user_ids.append(int(item))
        elif isinstance(datos, dict):
            usuarios = datos.get('users') or datos.get('user_ids') or datos.get('ids') or datos
            if isinstance(usuarios, list):
                for item in usuarios:
                    if isinstance(item, (int, str)):
                        user_ids.append(int(item))
        
        if not user_ids:
            embed_error = discord.Embed(
                title="❌ JSON Vacío o Inválido",
                description="No se encontraron IDs válidos en el archivo.",
                color=0xED4245
            )
            embed_error.add_field(
                name="📝 Formatos Aceptados",
                value="``````\n``````\n``````",
                inline=False
            )
            embed_error.set_footer(text="Sistema de Baneos Masivos")
            await interaction.edit_original_response(embed=embed_error)
            return
        
        # Eliminar duplicados
        user_ids = list(set(user_ids))
        
        # Separar usuarios
        guild = interaction.guild
        miembros_servidor = {member.id for member in guild.members}
        
        usuarios_en_servidor = []
        usuarios_a_banear = []
        
        for user_id in user_ids:
            if user_id in miembros_servidor:
                usuarios_en_servidor.append(user_id)
            else:
                usuarios_a_banear.append(user_id)
        
        # Ejecutar baneos
        baneados_exitosos = []
        errores_baneo = []
        
        for user_id in usuarios_a_banear:
            try:
                await guild.ban(
                    discord.Object(id=user_id),
                    reason=f"Baneo masivo ejecutado por {interaction.user} ({interaction.user.id})"
                )
                baneados_exitosos.append(user_id)
            except discord.Forbidden:
                errores_baneo.append((user_id, "Sin permisos"))
            except discord.HTTPException as e:
                errores_baneo.append((user_id, f"Error HTTP: {e.status}"))
        
        # Determinar color y emoji del resultado
        if baneados_exitosos and not usuarios_en_servidor:
            color_final = 0x57F287  # Verde
            emoji_titulo = "✅"
        elif usuarios_en_servidor and baneados_exitosos:
            color_final = 0xFEE75C  # Amarillo
            emoji_titulo = "⚠️"
        elif errores_baneo:
            color_final = 0xE67E22  # Naranja
            emoji_titulo = "⚡"
        else:
            color_final = 0x5865F2  # Blurple
            emoji_titulo = "📋"
        
        embed_resultado = discord.Embed(
            title=f"{emoji_titulo} Operación de Baneo Completada",
            description="Proceso de baneo masivo ejecutado correctamente.",
            color=color_final,
            timestamp=discord.utils.utcnow()
        )
        
        # Campo de usuarios en el servidor (PROTEGIDOS)
        if usuarios_en_servidor:
            usuarios_texto = ""
            for i, uid in enumerate(usuarios_en_servidor[:8], 1):
                try:
                    member = guild.get_member(uid)
                    if member:
                        usuarios_texto += f"`{i}.` {member.mention} • `{uid}`\n"
                    else:
                        usuarios_texto += f"`{i}.` <@{uid}> • `{uid}`\n"
                except Exception:
                    usuarios_texto += f"`{i}.` <@{uid}> • `{uid}`\n"
            
            if len(usuarios_en_servidor) > 8:
                usuarios_texto += f"\n`...` **+{len(usuarios_en_servidor) - 8} usuarios más**"
            
            embed_resultado.add_field(
                name=f"🛡️ Protegidos en el Servidor • {len(usuarios_en_servidor)}",
                value=usuarios_texto or "`Ninguno`",
                inline=False
            )
        
        # Campo de baneados exitosamente
        if baneados_exitosos:
            baneados_texto = ""
            for i, uid in enumerate(baneados_exitosos[:8], 1):
                baneados_texto += f"`{i}.` ID: `{uid}`\n"
            
            if len(baneados_exitosos) > 8:
                baneados_texto += f"\n`...` **+{len(baneados_exitosos) - 8} usuarios más**"
            
            embed_resultado.add_field(
                name=f"🔨 Baneados Exitosamente • {len(baneados_exitosos)}",
                value=baneados_texto or "`Ninguno`",
                inline=False
            )
        
        # Campo de errores
        if errores_baneo:
            errores_texto = ""
            for i, (uid, error) in enumerate(errores_baneo[:5], 1):
                errores_texto += f"`{i}.` `{uid}` → {error}\n"
            
            if len(errores_baneo) > 5:
                errores_texto += f"\n`...` **+{len(errores_baneo) - 5} errores más**"
            
            embed_resultado.add_field(
                name=f"⚠️ Errores • {len(errores_baneo)}",
                value=errores_texto or "`Ninguno`",
                inline=False
            )
        
        # Estadísticas finales (sin bloques de código)
        estadisticas = (
            f"Total en JSON: {len(user_ids)}\n"
            f"Protegidos:    {len(usuarios_en_servidor)}\n"
            f"Baneados:      {len(baneados_exitosos)}\n"
            f"Errores:       {len(errores_baneo)}"
        )
        
        embed_resultado.add_field(
            name="📊 Estadísticas Finales",
            value=estadisticas,
            inline=False
        )
        
        # Footer y thumbnail
        embed_resultado.set_footer(
            text=f"Ejecutado por {interaction.user.name} • Sistema de Baneos Masivos",
            icon_url=interaction.user.display_avatar.url
        )
        
        # Manejar thumbnail del servidor (puede ser None)
        if guild.icon:
            embed_resultado.set_thumbnail(url=guild.icon.url)
        
        await interaction.edit_original_response(embed=embed_resultado)
        
    except json.JSONDecodeError:
        embed = discord.Embed(
            title="❌ Error de Formato JSON",
            description="El archivo no tiene un formato JSON válido.\n\n**Verifica:**\n• Comas entre elementos\n• Llaves y corchetes cerrados\n• Comillas dobles en strings",
            color=0xED4245
        )
        embed.set_footer(text="Sistema de Baneos Masivos")
        await interaction.edit_original_response(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error Inesperado",
            description=f"{type(e).__name__}: {str(e)}",
            color=0xED4245
        )
        embed.set_footer(text="Sistema de Baneos Masivos")
        await interaction.edit_original_response(embed=embed)

@banear_json.error
async def banear_json_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title="🔒 Permisos Insuficientes",
            description="Necesitas el permiso **`Banear Miembros`** para ejecutar este comando.",
            color=0xED4245
        )
        embed.set_footer(text="Sistema de Baneos Masivos")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Ejecutar bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
