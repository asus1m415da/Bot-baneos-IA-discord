# ⚡ Discord Ban IA Bot

¡Automatiza y profesionaliza la moderación de tu servidor Discord usando inteligencia artificial!
Este bot permite banear usuarios por ID o @usuario, genera motivos inteligentes vía Groq AI y utiliza botones para confirmar o regenerar la acción.

***

## ✨ Características

- **Ban Inteligente:** Usa IA (`moonshotai/kimi-k2-instruct-0905` de Groq) para sugerir razones profesionales y justificadas de baneo.
- **Forceban:** Puedes banear tanto a miembros presentes como a los que ya no están en el servidor (solo con ID).
- **Botones Interactivos:** Confirma el baneo o regenera la razón de manera fácil con botones de Discord.
- **Seguridad:** Solo pueden usar el comando usuarios con el rol configurado por ID.
- **Deploy instantáneo:** Dockerfile optimizado para Railway.

***

## 🚀 Cómo usar

1. **Clona este repositorio y sube los archivos a Railway.**
2. **Configura tus variables de entorno:**
    - `DISCORD_TOKEN`: El token de tu bot.
    - `GROQ_API_KEY`: Tu clave API de Groq.
3. **Deploy en Railway. ¡Listo!**

***

## 🛡️ Permisos necesarios

- Permiso para banear miembros.
- Permiso para leer roles y mensajes.

***

## 📋 Comandos principales

```shell
%ban 123456789012345678 usuario infiltrado de servidor raid
%ban @usuario sospechoso actividad de raid
```

- Puedes mencionar o usar el ID.
- Si omites el motivo, la IA lo generará automáticamente.
- Tras el comando, se mostrarán botones para confirmar o regenerar el motivo antes del ban.

***

## 🛠️ Estructura rápida

- `bot.py` — Código fuente principal del bot.
- `Dockerfile` — Para deployment instantáneo en Railway.

***

## 📦 Deploy rápido en Railway

1. Sube todos los archivos (`bot.py`, `Dockerfile`).
2. Agrega las variables de entorno en el panel de Railway.
3. ¡Haz click en “Deploy”!

***

## 💡 Créditos

- Bot desarrollado en Python con [discord.py](https://discordpy.readthedocs.io/) y Groq API.
- Inspirado en mejores prácticas de moderación y despliegue cloud en Railway.

