FROM python:3.11-slim

# FFmpeg kur (müzik için şart!)
RUN apt-get update && apt-get install -y ffmpeg

# Çalışma klasörü
WORKDIR /app

# Gereken Python paketlerini yükle
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Tüm kodları kopyala
COPY . .

# Botu başlat
CMD ["python", "bot.py"]
