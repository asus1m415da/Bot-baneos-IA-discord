# Dockerfile para un bot Discord Python con Groq, Flask y deploy Railway
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos necesarios
COPY . .

# Instala dependencias
RUN pip install --upgrade pip
RUN pip install discord.py groq flask gunicorn

# Establece variables de entorno
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=bot.py
ENV FLASK_ENV=production

# Expone el puerto para Flask
EXPOSE 5000

# Comando para iniciar el bot y Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "bot:app"]
