import discord
from discord import app_commands
from discord.ext import commands

import re
import asyncio
from collections import deque
import yt_dlp

from core.classes import Cog


class MusicPlayer:
    """
    音樂播放系統
    """

    def __init__(self, bot):
        self.bot = bot

        self.queue = deque()
        self.current_song = None
        self.voice_client = None
        self.loop = False
        self.loop_queue = False
        self.volume = 0.5
        self.playing = False
        self.now_playing_message = None
        self.play_next_song_task = None
        self.history = deque(maxlen=10)

    async def connect(self, voice_channel):
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.move_to(voice_channel)
        else:
            self.voice_client = await voice_channel.connect()

    async def disconnect(self):
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            self.queue.clear()
            self.current_song = None
            self.playing = False

    async def add_song(self, query, requester):
        # 檢查是否是YouTube URL
        if not re.match(r"(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+", query):
            query = f"ytsearch:{query}"

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = await self.bot.loop.run_in_executor(
                    None, lambda: ydl.extract_info(query, download=False)
                )

                if "entries" in info:
                    # 播放列表或多個結果
                    entries = info["entries"]
                    for entry in entries[:5]:  # 限制一次添加5首
                        song = {
                            "title": entry.get("title", "未知標題"),
                            "url": entry.get("url"),
                            "duration": entry.get("duration", 0),
                            "thumbnail": entry.get("thumbnail", ""),
                            "requester": requester,
                            "webpage_url": entry.get("webpage_url", ""),
                        }
                        self.queue.append(song)
                    return len(entries)
                else:
                    # 單個結果
                    song = {
                        "title": info.get("title", "未知標題"),
                        "url": info.get("url"),
                        "duration": info.get("duration", 0),
                        "thumbnail": info.get("thumbnail", ""),
                        "requester": requester,
                        "webpage_url": info.get("webpage_url", ""),
                    }
                    self.queue.append(song)
                    return 1
            except Exception as e:
                print(f"獲取音樂資訊時出錯: {e}")
                return 0

    async def play(self):
        if not self.voice_client or not self.voice_client.is_connected():
            return

        if self.playing:
            return

        if not self.queue:
            return

        self.current_song = self.queue.popleft()
        self.history.appendleft(self.current_song)

        # FFmpeg選項
        ffmpeg_options = {
            "options": "-vn",
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        }

        try:
            audio_source = discord.FFmpegPCMAudio(
                self.current_song["url"], **ffmpeg_options
            )
            audio_source = discord.PCMVolumeTransformer(
                audio_source, volume=self.volume
            )

            self.voice_client.play(audio_source, after=self._play_next)
            self.playing = True
            return True
        except Exception as e:
            print(f"播放音樂時出錯: {e}")
            return False

    def _play_next(self, error=None):
        if error:
            print(f"播放器錯誤: {error}")
            if self.voice_client and self.voice_client.is_connected():
                self.voice_client.stop()

        self.playing = False

        if self.loop:
            self.queue.appendleft(self.current_song)

        if self.loop_queue and self.current_song:
            self.queue.append(self.current_song)

        if self.play_next_song_task and not self.play_next_song_task.done():
            self.play_next_song_task.cancel()

        self.play_next_song_task = asyncio.run_coroutine_threadsafe(
            self.play_next_song(), self.bot.loop
        )

    async def play_next_song(self):
        await asyncio.sleep(1)  # 短暫延遲
        await self.play()

    async def stop(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            self.playing = False
            self.queue.clear()
            self.current_song = None

    async def skip(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            self.playing = False

    async def set_volume(self, volume):
        self.volume = max(0.0, min(volume, 1.0))
        if self.voice_client and self.voice_client.source:
            self.voice_client.source.volume = self.volume

    def format_duration(self, seconds):
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
