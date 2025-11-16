# Imagen base liviana de Python 3.11
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Copia todos los archivos del proyecto
COPY . .

# Actualiza pip e instala dependencias necesarias
RUN pip install --upgrade pip
RUN pip install discord.py flask gunicorn dotenv

# Mantén los logs visibles en tiempo real
ENV PYTHONUNBUFFERED=1

# Expón el puerto donde correrá Flask (necesario para Railway)
EXPOSE 5000

# Comando de arranque: solo necesitamos un proceso python porque bot.py se encarga de lanzar Flask y el bot
CMD ["python", "bot.py"]
