import asyncio
import discord
import asyncio
# Eski/Hatalı youtube_dl yerine, aktif olarak güncellenen yt_dlp kullanılıyor.
import yt_dlp 
from discord.ext import commands
import os

# Ortam değişkeninden YT_API_KEY'i al
YT_API_KEY = os.getenv("YT_API_KEY") 

# YTDL (yt-dlp) ayarları
# --youtube-skip-dash-manifest ayarı, bazı akış hatalarını önleyebilir
ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "youtube_include_dash_manifest": False, # DASH manifest hatalarını önlemek için
    "source_address": "0.0.0.0", # Railway gibi Docker ortamlarında IP hatasını önlemek için

    # 🔑 YouTube API Anahtarını Ekleme (Ortam değişkeninizden alınıyor)
    # Bu genellikle sadece arama kotasını artırmak için kullanılır, indirme için zorunlu değildir.
    "extractor_args": {
        "youtube": {
            "key": YT_API_KEY 
        }
    } if YT_API_KEY else {} 
}

ffmpeg_options = {
    "options": "-vn -loglevel quiet" # Daha sessiz FFmpeg çalıştırmak için
}

# ytdl değişkeni, artık yt_dlp.YoutubeDL sınıfından oluşturuluyor
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        # ytdl objesini lambda fonksiyonu içinde kullan
        # İşlem, ana döngüyü bloklamamak için executor'da çalıştırılır
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            data = data["entries"][0]

        # Stream durumuna göre dosya adını veya URL'yi belirle
        filename = data["url"] if stream else ytdl.prepare_filename(data)
        
        # FFmpegPCMAudio ile oynatıcıyı başlat
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

