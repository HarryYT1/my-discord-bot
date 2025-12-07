FROM node:18

# FFmpeg kur
RUN apt-get update && apt-get install -y ffmpeg

# Proje dosyaları
WORKDIR /app
COPY . .

# Node kurulum
RUN npm install

CMD ["node", "index.js"]
