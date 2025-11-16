# Dockerfile para un bot Discord Python con Groq y deploy Railway
FROM python:3.11-slim

WORKDIR /app
COPY . .

# Instala dependencias
RUN pip install --upgrade pip
RUN pip install discord.py groq

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
