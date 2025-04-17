# Verwende ein offizielles Python-Image
FROM python:3.9-slim

# Setze das Arbeitsverzeichnis
WORKDIR /app

# Kopiere die requirements.txt
COPY requirements.txt .

# Installiere die Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere die restlichen Dateien (z.B. dein bot.py)
COPY . .

# Exponiere den Port, den die App verwenden wird
EXPOSE 5000

# Starte den Bot (es kann sein, dass du dies noch anpassen musst, je nach dem, wie dein Bot läuft)
CMD ["python", "bot.py"]
