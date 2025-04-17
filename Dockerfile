# Verwenden Sie ein Python-Image
FROM python:3.9-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Installieren der Abhängigkeiten
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den gesamten Code
COPY . /app/

# Setzen des Umgebungsvariablen für den Port
ENV PORT 5000

# Exponieren des Ports
EXPOSE 5000

# Flask-App starten
CMD ["python", "bot.py"]
