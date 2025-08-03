import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import random
import json
from datetime import datetime, timedelta
import asyncio
import yt_dlp
import re
from collections import deque
import subprocess

# 載入環境變數
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 設定機器人
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 數據文件設定
USER_DATA_FILE = "user_data.json"
SHOP_ITEMS_FILE = "shop_items.json"
TAROT_CARDS_FILE = "tarot_cards.json"

# 初始化數據
def load_data():
    global user_data, shop_items, tarot_cards
    
    # 用戶數據
    try:
        with open(USER_DATA_FILE, "r") as f:
            user_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}
    
    # 商店物品
    try:
        with open(SHOP_ITEMS_FILE, "r") as f:
            shop_items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 默認商店物品
        shop_items = [
            {"id": "title_1", "name": "初學者稱號", "description": "新手專屬稱號", "price": 100, "type": "title"},
            {"id": "title_2", "name": "黃金會員", "description": "尊貴黃金會員稱號", "price": 500, "type": "title"},
            {"id": "bg_1", "name": "星空背景", "description": "個人資料星空背景", "price": 300, "type": "background"},
            {"id": "role_color", "name": "自訂角色顏色", "description": "解鎖自訂角色顏色權限", "price": 800, "type": "perk"},
            {"id": "double_xp", "name": "雙倍經驗卡", "description": "24小時內獲得雙倍經驗", "price": 200, "type": "boost"},
            {"id": "fortune_boost", "name": "幸運水晶", "description": "提升占卜結果品質", "price": 150, "type": "fortune"}
        ]
        save_shop_items()
    
    # 塔羅牌
    try:
        with open(TAROT_CARDS_FILE, "r") as f:
            tarot_cards = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 默認塔羅牌
        tarot_cards = [
            {"name": "愚者", "meaning": "新的開始、冒險精神", "type": "major", "image": "🃏"},
            {"name": "魔術師", "meaning": "創造力、技能", "type": "major", "image": "🧙"},
            {"name": "女祭司", "meaning": "直覺、神秘知識", "type": "major", "image": "🔮"},
            {"name": "女皇", "meaning": "豐饒、母性", "type": "major", "image": "👑"},
            {"name": "皇帝", "meaning": "權威、結構", "type": "major", "image": "👨‍💼"},
            {"name": "戰車", "meaning": "意志力、勝利", "type": "major", "image": "🛡️"},
            {"name": "力量", "meaning": "勇氣、內在力量", "type": "major", "image": "💪"},
            {"name": "隱者", "meaning": "內省、尋求真理", "type": "major", "image": "🧓"},
            {"name": "命運之輪", "meaning": "命運轉變、契機", "type": "major", "image": "🔄"},
            {"name": "正義", "meaning": "公平、決定", "type": "major", "image": "⚖️"},
            {"name": "倒吊人", "meaning": "犧牲、新視角", "type": "major", "image": "🙃"},
            {"name": "死神", "meaning": "結束、轉變", "type": "major", "image": "💀"},
            {"name": "節制", "meaning": "平衡、調和", "type": "major", "image": "⚗️"},
            {"name": "惡魔", "meaning": "束縛、物質主義", "type": "major", "image": "😈"},
            {"name": "塔", "meaning": "突變、啟示", "type": "major", "image": "⚡"},
            {"name": "星星", "meaning": "希望、靈感", "type": "major", "image": "⭐"},
            {"name": "月亮", "meaning": "幻覺、潛意識", "type": "major", "image": "🌙"},
            {"name": "太陽", "meaning": "成功、喜悅", "type": "major", "image": "☀️"},
            {"name": "審判", "meaning": "覺醒、重生", "type": "major", "image": "👼"},
            {"name": "世界", "meaning": "完成、成就", "type": "major", "image": "🌍"},
            {"name": "寶劍Ace", "meaning": "新的想法、突破", "type": "minor", "image": "⚔️"},
            {"name": "權杖Ace", "meaning": "新的開始、能量", "type": "minor", "image": "🔥"},
            {"name": "聖杯Ace", "meaning": "新的情感、直覺", "type": "minor", "image": "💧"},
            {"name": "錢幣Ace", "meaning": "新的財富、機會", "type": "minor", "image": "💰"}
        ]
        save_tarot_cards()

def save_user_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

def save_shop_items():
    with open(SHOP_ITEMS_FILE, "w") as f:
        json.dump(shop_items, f)

def save_tarot_cards():
    with open(TAROT_CARDS_FILE, "w") as f:
        json.dump(tarot_cards, f)

# 等級系統設定
LEVEL_MULTIPLIER = 25  # 每級所需經驗值倍數

# 加載數據
load_data()

# ========================
# 音樂播放系統
# ========================

# 音樂播放器類
class MusicPlayer:
    def __init__(self):
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
        if not re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+', query):
            query = f"ytsearch:{query}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = await bot.loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                
                if 'entries' in info:
                    # 播放列表或多個結果
                    entries = info['entries']
                    for entry in entries[:5]:  # 限制一次添加5首
                        song = {
                            'title': entry.get('title', '未知標題'),
                            'url': entry.get('url'),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                            'requester': requester,
                            'webpage_url': entry.get('webpage_url', '')
                        }
                        self.queue.append(song)
                    return len(entries)
                else:
                    # 單個結果
                    song = {
                        'title': info.get('title', '未知標題'),
                        'url': info.get('url'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'requester': requester,
                        'webpage_url': info.get('webpage_url', '')
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
            'options': '-vn',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }
        
        try:
            audio_source = discord.FFmpegPCMAudio(
                self.current_song['url'],
                **ffmpeg_options
            )
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=self.volume)
            
            self.voice_client.play(audio_source, after=self._play_next)
            self.playing = True
            return True
        except Exception as e:
            print(f"播放音樂時出錯: {e}")
            return False
    
    def _play_next(self, error=None):
        if error:
            print(f"播放器錯誤: {error}")
        
        self.playing = False
        
        if self.loop:
            self.queue.appendleft(self.current_song)
        
        if self.loop_queue and self.current_song:
            self.queue.append(self.current_song)
        
        if self.play_next_song_task and not self.play_next_song_task.done():
            self.play_next_song_task.cancel()
        
        self.play_next_song_task = asyncio.run_coroutine_threadsafe(self.play_next_song(), bot.loop)
    
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

# 全局音樂播放器字典
music_players = {}

def get_music_player(guild_id):
    if guild_id not in music_players:
        music_players[guild_id] = MusicPlayer()
    return music_players[guild_id]

# ========================
# 音樂命令
# ========================

@bot.tree.command(name="join", description="讓機器人加入語音頻道")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ 請先加入一個語音頻道！", ephemeral=True)
        return
    
    voice_channel = interaction.user.voice.channel
    player = get_music_player(interaction.guild_id)
    
    try:
        await player.connect(voice_channel)
        await interaction.response.send_message(f"✅ 已加入 **{voice_channel.name}**")
    except Exception as e:
        await interaction.response.send_message(f"❌ 加入語音頻道時出錯: {e}", ephemeral=True)

@bot.tree.command(name="leave", description="讓機器人離開語音頻道")
async def leave(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.voice_client or not player.voice_client.is_connected():
        await interaction.response.send_message("❌ 機器人不在任何語音頻道中！", ephemeral=True)
        return
    
    try:
        await player.disconnect()
        await interaction.response.send_message("✅ 已離開語音頻道")
    except Exception as e:
        await interaction.response.send_message(f"❌ 離開語音頻道時出錯: {e}", ephemeral=True)

@bot.tree.command(name="play", description="播放音樂或將音樂加入隊列")
@app_commands.describe(query="歌曲名稱或YouTube連結")
async def play(interaction: discord.Interaction, query: str):
    # 檢查用戶是否在語音頻道
    if not interaction.user.voice:
        await interaction.response.send_message("❌ 請先加入一個語音頻道！", ephemeral=True)
        return
    
    player = get_music_player(interaction.guild_id)
    
    # 如果機器人不在語音頻道，加入用戶所在的頻道
    if not player.voice_client or not player.voice_client.is_connected():
        voice_channel = interaction.user.voice.channel
        try:
            await player.connect(voice_channel)
        except Exception as e:
            await interaction.response.send_message(f"❌ 加入語音頻道時出錯: {e}", ephemeral=True)
            return
    
    await interaction.response.defer()
    
    # 添加歌曲到隊列
    added_count = await player.add_song(query, interaction.user)
    
    if added_count == 0:
        await interaction.followup.send("❌ 找不到歌曲！")
        return
    
    # 如果當前沒有播放歌曲，開始播放
    if not player.playing:
        success = await player.play()
        if not success:
            await interaction.followup.send("❌ 播放音樂時出錯！")
            return
    
    # 創建回應訊息
    if added_count > 1:
        message = f"✅ 已將 **{added_count}首歌曲** 加入隊列"
    else:
        song = player.queue[-1] if player.playing else player.current_song
        message = f"🎵 已將 **{song['title']}** 加入隊列"
    
    await interaction.followup.send(message)

@bot.tree.command(name="nowplaying", description="顯示當前播放的歌曲")
async def nowplaying(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.current_song:
        await interaction.response.send_message("❌ 當前沒有播放任何歌曲！", ephemeral=True)
        return
    
    song = player.current_song
    duration = player.format_duration(song['duration'])
    progress = ""
    
    # 如果正在播放，顯示進度條
    if player.voice_client and player.voice_client.is_playing():
        position = player.voice_client.source.played if hasattr(player.voice_client.source, 'played') else 0
        position_str = player.format_duration(position)
        
        # 進度條
        progress_percent = min(1.0, max(0.0, position / song['duration'])) if song['duration'] > 0 else 0
        progress_bar_length = 20
        filled_length = int(progress_percent * progress_bar_length)
        progress_bar = "▬" * filled_length + "🔘" + "▬" * (progress_bar_length - filled_length - 1)
        progress = f"\n\n{progress_bar}\n{position_str} / {duration}"
    
    embed = discord.Embed(
        title="🎵 正在播放",
        description=f"[{song['title']}]({song['webpage_url']}){progress}",
        color=discord.Color.blue()
    )
    embed.add_field(name="時長", value=duration, inline=True)
    embed.add_field(name="點播者", value=song['requester'].mention, inline=True)
    
    if song['thumbnail']:
        embed.set_thumbnail(url=song['thumbnail'])
    
    # 添加控制按鈕
    view = discord.ui.View()
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji="⏮️", custom_id="previous"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji="⏯️", custom_id="pause_resume"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="skip"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="loop"))
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="stop"))
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="pause", description="暫停當前播放的歌曲")
async def pause(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.voice_client or not player.voice_client.is_playing():
        await interaction.response.send_message("❌ 當前沒有播放任何歌曲！", ephemeral=True)
        return
    
    player.voice_client.pause()
    await interaction.response.send_message("⏸️ 已暫停播放")

@bot.tree.command(name="resume", description="繼續播放暫停的歌曲")
async def resume(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.voice_client or not player.voice_client.is_paused():
        await interaction.response.send_message("❌ 當前沒有暫停的歌曲！", ephemeral=True)
        return
    
    player.voice_client.resume()
    await interaction.response.send_message("▶️ 已繼續播放")

@bot.tree.command(name="skip", description="跳過當前播放的歌曲")
async def skip(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.voice_client or not player.voice_client.is_playing():
        await interaction.response.send_message("❌ 當前沒有播放任何歌曲！", ephemeral=True)
        return
    
    await player.skip()
    await interaction.response.send_message("⏭️ 已跳過當前歌曲")

@bot.tree.command(name="stop", description="停止播放並清空隊列")
async def stop(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.voice_client or not (player.voice_client.is_playing() or player.voice_client.is_paused()):
        await interaction.response.send_message("❌ 當前沒有播放任何歌曲！", ephemeral=True)
        return
    
    await player.stop()
    await interaction.response.send_message("⏹️ 已停止播放並清空隊列")

@bot.tree.command(name="queue", description="顯示當前播放隊列")
async def queue(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.queue and not player.current_song:
        await interaction.response.send_message("❌ 隊列是空的！", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎵 播放隊列",
        color=discord.Color.green()
    )
    
    # 當前播放的歌曲
    if player.current_song:
        song = player.current_song
        duration = player.format_duration(song['duration'])
        embed.add_field(
            name="正在播放",
            value=f"[{song['title']}]({song['webpage_url']})\n時長: {duration} | 點播者: {song['requester'].mention}",
            inline=False
        )
    
    # 隊列中的歌曲
    if player.queue:
        queue_list = []
        for i, song in enumerate(player.queue[:10], 1):  # 只顯示前10首
            duration = player.format_duration(song['duration'])
            queue_list.append(f"{i}. [{song['title']}]({song['webpage_url']}) ({duration}) | {song['requester'].mention}")
        
        embed.add_field(
            name=f"待播歌曲 ({len(player.queue)}首)",
            value="\n".join(queue_list),
            inline=False
        )
    
    # 播放模式
    loop_status = ""
    if player.loop:
        loop_status = "🔂 單曲循環"
    elif player.loop_queue:
        loop_status = "🔁 列表循環"
    else:
        loop_status = "➡️ 無循環"
    
    embed.add_field(name="播放模式", value=loop_status, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="volume", description="調整音量 (0-100)")
@app_commands.describe(level="音量等級 (0-100)")
async def volume(interaction: discord.Interaction, level: int):
    player = get_music_player(interaction.guild_id)
    
    if level < 0 or level > 100:
        await interaction.response.send_message("❌ 音量必須在0-100之間！", ephemeral=True)
        return
    
    volume_level = level / 100.0
    
    try:
        await player.set_volume(volume_level)
        await interaction.response.send_message(f"🔊 音量已設定為 **{level}%**")
    except Exception as e:
        await interaction.response.send_message(f"❌ 調整音量時出錯: {e}", ephemeral=True)

@bot.tree.command(name="loop", description="切換單曲循環模式")
async def loop(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    player.loop = not player.loop
    if player.loop:
        player.loop_queue = False
    
    status = "啟用" if player.loop else "停用"
    await interaction.response.send_message(f"🔂 單曲循環模式已 **{status}**")

@bot.tree.command(name="loopqueue", description="切換列表循環模式")
async def loopqueue(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    player.loop_queue = not player.loop_queue
    if player.loop_queue:
        player.loop = False
    
    status = "啟用" if player.loop_queue else "停用"
    await interaction.response.send_message(f"🔁 列表循環模式已 **{status}**")

@bot.tree.command(name="shuffle", description="隨機打亂播放隊列")
async def shuffle(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.queue:
        await interaction.response.send_message("❌ 隊列是空的！", ephemeral=True)
        return
    
    random.shuffle(player.queue)
    await interaction.response.send_message("🔀 已隨機打亂播放隊列")

@bot.tree.command(name="history", description="顯示最近播放的歌曲")
async def history(interaction: discord.Interaction):
    player = get_music_player(interaction.guild_id)
    
    if not player.history:
        await interaction.response.send_message("❌ 沒有播放歷史！", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="⏮️ 播放歷史",
        color=discord.Color.purple()
    )
    
    history_list = []
    for i, song in enumerate(player.history, 1):
        duration = player.format_duration(song['duration'])
        history_list.append(f"{i}. [{song['title']}]({song['webpage_url']}) ({duration}) | {song['requester'].mention}")
    
    embed.description = "\n".join(history_list)
    await interaction.response.send_message(embed=embed)

# ========================
# 等級系統 - 用戶發言時觸發
# ========================

@bot.event
async def on_message(message):
    # 忽略機器人自己的消息
    if message.author.bot:
        return
    
    user_id = str(message.author.id)
    
    # 初始化用戶數據
    if user_id not in user_data:
        user_data[user_id] = {
            "exp": 0,
            "level": 1,
            "last_message": 0,
            "coins": 0,
            "inventory": {},
            "title": "",
            "background": "",
            "last_fortune": 0,
            "boosts": {}
        }
    
    user = user_data[user_id]
    
    # 防止刷消息 (每60秒獲得一次經驗)
    current_time = datetime.now().timestamp()
    if current_time - user["last_message"] > 60:
        # 計算經驗加成
        exp_multiplier = 1.0
        if "double_xp" in user["boosts"]:
            if current_time < user["boosts"]["double_xp"]:
                exp_multiplier = 2.0
        
        # 隨機獲得經驗
        exp_gained = random.randint(5, 15) * exp_multiplier
        user["exp"] += exp_gained
        user["coins"] += random.randint(1, 3)
        user["last_message"] = current_time
        
        # 檢查升級
        current_level = user["level"]
        exp_needed = current_level * LEVEL_MULTIPLIER
        
        if user["exp"] >= exp_needed:
            user["level"] += 1
            user["coins"] += current_level * 10  # 升級獎勵金幣
            
            # 發送升級通知
            embed = discord.Embed(
                title="🎉 升級了！",
                description=f"{message.author.mention} 升到了 **{user['level']}級**！",
                color=discord.Color.gold()
            )
            embed.add_field(name="金幣獎勵", value=f"🪙 {current_level * 10} 金幣")
            await message.channel.send(embed=embed)
        
        # 保存數據
        save_user_data()
    
    # 處理命令
    await bot.process_commands(message)

# 啟動事件
@bot.event
async def on_ready():
    print(f"登入身份：{bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"已同步 {len(synced)} 個斜線命令")
    except Exception as e:
        print(f"同步錯誤: {e}")
    
    # 啟動狀態循環
    change_status.start()

# 狀態循環任務
@tasks.loop(minutes=5)
async def change_status():
    statuses = [
        f"/help | {len(bot.guilds)} 個伺服器",
        f"等級系統 | {len(user_data)} 位用戶",
        "小遊戲 | /game",
        "占卜 | /fortune",
        "商店 | /shop",
        "音樂 | /play"
    ]
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))

# ========================
# 等級系統命令
# ========================

@bot.tree.command(name="level", description="查看你的等級和經驗值")
async def level(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in user_data:
        await interaction.response.send_message("你還沒有任何等級數據！開始聊天來獲得經驗值吧！", ephemeral=True)
        return
    
    data = user_data[user_id]
    exp_needed = data["level"] * LEVEL_MULTIPLIER
    progress = (data["exp"] / exp_needed) * 100
    
    embed = discord.Embed(
        title=f"{interaction.user.display_name} 的等級",
        color=discord.Color.blue()
    )
    
    # 添加稱號和背景
    if data.get("title"):
        embed.title = f"{data['title']} {embed.title}"
    if data.get("background"):
        embed.description = f"個人背景: {data['background']}"
    
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="等級", value=f"**{data['level']}**", inline=True)
    embed.add_field(name="經驗值", value=f"{int(data['exp'])}/{exp_needed}", inline=True)
    embed.add_field(name="金幣", value=f"🪙 {data['coins']}", inline=True)
    embed.add_field(name="進度", value=f"`{'█' * int(progress/10)}{'░' * (10 - int(progress/10))}` {progress:.1f}%", inline=False)
    
    # 顯示加成效果
    boosts = []
    if "double_xp" in data.get("boosts", {}):
        if datetime.now().timestamp() < data["boosts"]["double_xp"]:
            time_left = int((data["boosts"]["double_xp"] - datetime.now().timestamp()) / 60)
            boosts.append(f"雙倍經驗 ({time_left}分鐘)")
    
    if boosts:
        embed.add_field(name="加成效果", value="\n".join(boosts), inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="查看伺服器等級排行榜")
async def leaderboard(interaction: discord.Interaction):
    # 獲取伺服器成員ID
    member_ids = [str(member.id) for member in interaction.guild.members]
    
    # 篩選出在伺服器中的用戶數據
    server_users = {uid: data for uid, data in user_data.items() if uid in member_ids}
    
    if not server_users:
        await interaction.response.send_message("還沒有任何等級數據！", ephemeral=True)
        return
    
    # 排序取前10名
    top_users = sorted(server_users.items(), key=lambda x: x[1]["level"], reverse=True)[:10]
    
    embed = discord.Embed(
        title="🏆 等級排行榜",
        description=f"**{interaction.guild.name}** 的頂尖玩家",
        color=discord.Color.gold()
    )
    
    for i, (user_id, data) in enumerate(top_users):
        member = interaction.guild.get_member(int(user_id))
        if member:
            title = data.get("title", "")
            embed.add_field(
                name=f"{i+1}. {title}{member.display_name}" if title else f"{i+1}. {member.display_name}",
                value=f"等級: {data['level']} | 經驗: {int(data['exp'])} | 金幣: {data['coins']}",
                inline=False
            )
    
    embed.set_footer(text=f"總共 {len(server_users)} 位用戶參與")
    await interaction.response.send_message(embed=embed)

# ========================
# 小遊戲系統
# ========================

# 猜數字遊戲
@bot.tree.command(name="guess", description="猜數字遊戲 (1-100)")
async def guess(interaction: discord.Interaction):
    number = random.randint(1, 100)
    
    embed = discord.Embed(
        title="🎮 猜數字遊戲",
        description="我已經想好了一個 1-100 之間的數字！你有 5 次機會猜中它！",
        color=discord.Color.green()
    )
    embed.set_footer(text="輸入 /g [數字] 來猜測")
    
    # 存儲遊戲數據
    bot.games = getattr(bot, "games", {})
    bot.games[interaction.user.id] = {
        "number": number,
        "attempts": 5,
        "won": False
    }
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="g", description="猜數字")
@app_commands.describe(number="你猜的數字 (1-100)")
async def guess_number(interaction: discord.Interaction, number: int):
    user_id = interaction.user.id
    games = getattr(bot, "games", {})
    
    if user_id not in games:
        await interaction.response.send_message("你還沒有開始遊戲！使用 /guess 開始新遊戲。", ephemeral=True)
        return
    
    game = games[user_id]
    
    if game["won"] or game["attempts"] <= 0:
        await interaction.response.send_message("遊戲已經結束！使用 /guess 開始新遊戲。", ephemeral=True)
        return
    
    # 減少嘗試次數
    game["attempts"] -= 1
    
    # 檢查猜測
    if number == game["number"]:
        game["won"] = True
        reward = random.randint(20, 50)
        
        # 更新用戶金幣
        user_id_str = str(user_id)
        if user_id_str in user_data:
            user_data[user_id_str]["coins"] += reward
            save_user_data()
        
        embed = discord.Embed(
            title="🎉 恭喜！",
            description=f"你猜對了！數字就是 **{game['number']}**！",
            color=discord.Color.gold()
        )
        embed.add_field(name="獎勵", value=f"🪙 +{reward} 金幣")
        await interaction.response.send_message(embed=embed)
        del games[user_id]
        return
    
    # 提示大小
    hint = "太小了" if number < game["number"] else "太大了"
    
    # 檢查遊戲是否結束
    if game["attempts"] <= 0:
        embed = discord.Embed(
            title="遊戲結束",
            description=f"很遺憾，你沒能猜中數字！正確數字是 **{game['number']}**",
            color=discord.Color.red()
        )
        del games[user_id]
    else:
        embed = discord.Embed(
            title="繼續猜！",
            description=f"你的猜測 **{number}** {hint}！",
            color=discord.Color.orange()
        )
        embed.add_field(name="剩餘嘗試次數", value=f"**{game['attempts']}** 次")
    
    await interaction.response.send_message(embed=embed)

# 老虎機遊戲
@bot.tree.command(name="slots", description="老虎機小遊戲 (花費 10 金幣)")
async def slots(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in user_data or user_data[user_id]["coins"] < 10:
        await interaction.response.send_message("金幣不足或沒有帳戶！最少需要 10 金幣才能玩。", ephemeral=True)
        return
    
    # 扣除金幣
    user_data[user_id]["coins"] -= 10
    save_user_data()
    
    # 生成老虎機結果
    symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "⭐", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    
    # 檢查勝利條件
    if result[0] == result[1] == result[2]:
        win_amount = 100
        win_text = "大獎！"
    elif result[0] == result[1] or result[1] == result[2]:
        win_amount = 30
        win_text = "連線獎！"
    else:
        win_amount = 0
        win_text = "沒中獎"
    
    # 發送結果
    embed = discord.Embed(
        title="🎰 老虎機",
        description=f"**{result[0]} | {result[1]} | {result[2]}**",
        color=discord.Color.purple()
    )
    embed.add_field(name="結果", value=win_text)
    
    if win_amount > 0:
        user_data[user_id]["coins"] += win_amount
        save_user_data()
        embed.add_field(name="獎金", value=f"🪙 +{win_amount} 金幣")
    else:
        embed.add_field(name="下次運氣更好！", value="再試一次吧！")
    
    embed.set_footer(text=f"餘額: {user_data[user_id]['coins']} 金幣")
    await interaction.response.send_message(embed=embed)

# 擲骰子遊戲
@bot.tree.command(name="dice", description="擲骰子遊戲 (花費 5 金幣)")
async def dice(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in user_data or user_data[user_id]["coins"] < 5:
        await interaction.response.send_message("金幣不足或沒有帳戶！最少需要 5 金幣才能玩。", ephemeral=True)
        return
    
    # 扣除金幣
    user_data[user_id]["coins"] -= 5
    save_user_data()
    
    # 生成骰子結果
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2
    
    # 計算獎勵
    win_amount = 0
    if total == 7:
        win_amount = 20
        win_text = "幸運7！"
    elif total >= 10:
        win_amount = 10
        win_text = "高點數！"
    elif total <= 4:
        win_amount = 10
        win_text = "低點數！"
    else:
        win_text = "普通點數"
    
    # 發送結果
    embed = discord.Embed(
        title="🎲 擲骰子遊戲",
        description=f"你擲出了：**{dice1}** 和 **{dice2}** (總和: {total})",
        color=discord.Color.blue()
    )
    embed.add_field(name="結果", value=win_text)
    
    if win_amount > 0:
        user_data[user_id]["coins"] += win_amount
        save_user_data()
        embed.add_field(name="獎金", value=f"🪙 +{win_amount} 金幣")
    
    embed.set_footer(text=f"餘額: {user_data[user_id]['coins']} 金幣")
    await interaction.response.send_message(embed=embed)

# 21點遊戲
@bot.tree.command(name="blackjack", description="21點遊戲 (花費 15 金幣)")
async def blackjack(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in user_data or user_data[user_id]["coins"] < 15:
        await interaction.response.send_message("金幣不足或沒有帳戶！最少需要 15 金幣才能玩。", ephemeral=True)
        return
    
    # 扣除金幣
    user_data[user_id]["coins"] -= 15
    save_user_data()
    
    # 初始化遊戲
    deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
    random.shuffle(deck)
    
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    # 存儲遊戲狀態
    bot.games = getattr(bot, "games", {})
    bot.games[interaction.user.id] = {
        "deck": deck,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "status": "playing"
    }
    
    # 顯示初始手牌
    embed = discord.Embed(
        title="🃏 21點遊戲",
        description="輸入 `/hit` 要牌 或 `/stand` 停牌",
        color=discord.Color.dark_green()
    )
    embed.add_field(name="你的手牌", value=f"{format_hand(player_hand)} (總和: {calculate_hand(player_hand)})", inline=False)
    embed.add_field(name="莊家的手牌", value=f"{dealer_hand[0]} ?", inline=False)
    
    await interaction.response.send_message(embed=embed)

def calculate_hand(hand):
    total = sum(hand)
    # 處理Ace
    aces = hand.count(11)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

def format_hand(hand):
    return " ".join(str(card) for card in hand)

@bot.tree.command(name="hit", description="21點要牌")
async def hit(interaction: discord.Interaction):
    user_id = interaction.user.id
    games = getattr(bot, "games", {})
    
    if user_id not in games or games[user_id]["status"] != "playing":
        await interaction.response.send_message("你沒有進行中的21點遊戲！使用 /blackjack 開始新遊戲。", ephemeral=True)
        return
    
    game = games[user_id]
    game["player_hand"].append(game["deck"].pop())
    player_total = calculate_hand(game["player_hand"])
    
    # 檢查是否爆牌
    if player_total > 21:
        game["status"] = "busted"
        result = "爆牌！你輸了"
        color = discord.Color.red()
        win_amount = 0
    else:
        result = "繼續遊戲中..."
        color = discord.Color.green()
        win_amount = None
    
    embed = discord.Embed(
        title="🃏 21點遊戲 - 要牌",
        color=color
    )
    embed.add_field(name="你的手牌", value=f"{format_hand(game['player_hand'])} (總和: {player_total})", inline=False)
    embed.add_field(name="莊家的手牌", value=f"{game['dealer_hand'][0]} ?", inline=False)
    embed.add_field(name="結果", value=result, inline=False)
    
    # 處理遊戲結束
    if game["status"] == "busted":
        # 莊家亮牌
        dealer_total = calculate_hand(game["dealer_hand"])
        embed.add_field(name="莊家的手牌", value=f"{format_hand(game['dealer_hand'])} (總和: {dealer_total})", inline=False)
        
        # 保存結果
        save_user_data()
        del games[user_id]
    else:
        embed.set_footer(text="輸入 /hit 要牌 或 /stand 停牌")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stand", description="21點停牌")
async def stand(interaction: discord.Interaction):
    user_id = interaction.user.id
    games = getattr(bot, "games", {})
    
    if user_id not in games or games[user_id]["status"] != "playing":
        await interaction.response.send_message("你沒有進行中的21點遊戲！使用 /blackjack 開始新遊戲。", ephemeral=True)
        return
    
    game = games[user_id]
    player_total = calculate_hand(game["player_hand"])
    dealer_total = calculate_hand(game["dealer_hand"])
    
    # 莊家抽牌直到17點或以上
    while dealer_total < 17:
        game["dealer_hand"].append(game["deck"].pop())
        dealer_total = calculate_hand(game["dealer_hand"])
    
    # 判斷勝負
    if dealer_total > 21:
        result = "莊家爆牌！你贏了！"
        win_amount = 30
        color = discord.Color.gold()
    elif dealer_total > player_total:
        result = "莊家贏了！"
        win_amount = 0
        color = discord.Color.red()
    elif dealer_total < player_total:
        result = "你贏了！"
        win_amount = 30
        color = discord.Color.gold()
    else:
        result = "平手！"
        win_amount = 15
        color = discord.Color.blue()
    
    # 更新金幣
    user_id_str = str(user_id)
    if user_id_str in user_data:
        user_data[user_id_str]["coins"] += win_amount
        save_user_data()
    
    # 創建結果嵌入
    embed = discord.Embed(
        title="🃏 21點遊戲 - 結果",
        color=color
    )
    embed.add_field(name="你的手牌", value=f"{format_hand(game['player_hand'])} (總和: {player_total})", inline=False)
    embed.add_field(name="莊家的手牌", value=f"{format_hand(game['dealer_hand'])} (總和: {dealer_total})", inline=False)
    embed.add_field(name="結果", value=result, inline=False)
    
    if win_amount > 0:
        embed.add_field(name="獎金", value=f"🪙 +{win_amount} 金幣")
    
    # 刪除遊戲狀態
    del games[user_id]
    
    await interaction.response.send_message(embed=embed)

# ========================
# 占卜系統
# ========================

@bot.tree.command(name="fortune", description="每日塔羅牌占卜")
async def fortune(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    # 初始化用戶數據
    if user_id not in user_data:
        user_data[user_id] = {
            "exp": 0,
            "level": 1,
            "last_message": 0,
            "coins": 0,
            "inventory": {},
            "title": "",
            "background": "",
            "last_fortune": 0,
            "boosts": {}
        }
    
    user = user_data[user_id]
    current_time = datetime.now().timestamp()
    
    # 檢查冷卻時間 (24小時)
    if current_time - user["last_fortune"] < 86400:
        remaining = int(86400 - (current_time - user["last_fortune"]))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await interaction.response.send_message(
            f"每日占卜冷卻中！請等待 {hours}小時 {minutes}分鐘 後再試。",
            ephemeral=True
        )
        return
    
    # 更新最後占卜時間
    user["last_fortune"] = current_time
    
    # 檢查是否有幸運加成
    fortune_boost = "fortune_boost" in user.get("inventory", {})
    
    # 抽取塔羅牌
    cards = []
    meanings = []
    
    # 抽取3張牌
    for _ in range(3):
        card = random.choice(tarot_cards)
        cards.append(card)
        
        # 有加成時增加正面解讀機率
        if fortune_boost and random.random() > 0.3:
            meaning = card["meaning"] + " (正面)"
        else:
            # 隨機正負面解讀
            if random.random() > 0.5:
                meaning = card["meaning"] + " (正面)"
            else:
                meaning = card["meaning"] + " (負面)"
        
        meanings.append(meaning)
    
    # 創建占卜結果
    embed = discord.Embed(
        title="🔮 塔羅牌占卜結果",
        description=f"為 {interaction.user.display_name} 的今日運勢",
        color=discord.Color.purple()
    )
    
    # 添加牌面
    card_display = " ".join(card["image"] for card in cards)
    embed.add_field(name="抽到的牌", value=card_display, inline=False)
    
    # 添加解讀
    for i, meaning in enumerate(meanings):
        embed.add_field(name=f"牌 {i+1} - {cards[i]['name']}", value=meaning, inline=False)
    
    # 整體運勢
    positive_count = sum(1 for m in meanings if "正面" in m)
    if positive_count == 3:
        overall = "大吉！今天事事順利！"
    elif positive_count == 2:
        overall = "吉！今天運氣不錯！"
    elif positive_count == 1:
        overall = "平！保持平常心面對。"
    else:
        overall = "凶！今天需謹慎行事。"
    
    embed.add_field(name="整體運勢", value=overall, inline=False)
    
    # 獎勵金幣
    reward = random.randint(5, 15)
    user["coins"] += reward
    save_user_data()
    
    embed.set_footer(text=f"獲得每日獎勵: 🪙 {reward} 金幣")
    
    # 消耗幸運加成
    if fortune_boost:
        user["inventory"]["fortune_boost"] -= 1
        if user["inventory"]["fortune_boost"] <= 0:
            del user["inventory"]["fortune_boost"]
        save_user_data()
        embed.add_field(name="幸運水晶", value="已消耗一個幸運水晶提升占卜品質", inline=False)
    
    await interaction.response.send_message(embed=embed)

# ========================
# 商店系統
# ========================

@bot.tree.command(name="shop", description="查看商店物品")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 商店",
        description="使用 /buy [物品ID] 購買物品",
        color=discord.Color.blue()
    )
    
    # 添加物品到商店
    for item in shop_items:
        embed.add_field(
            name=f"{item['name']} (ID: {item['id']})",
            value=f"{item['description']}\n價格: 🪙 {item['price']}",
            inline=False
        )
    
    # 顯示用戶金幣餘額
    user_id = str(interaction.user.id)
    coins = user_data[user_id]["coins"] if user_id in user_data else 0
    embed.set_footer(text=f"你的金幣: 🪙 {coins}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="buy", description="購買商店物品")
@app_commands.describe(item_id="要購買的物品ID")
async def buy(interaction: discord.Interaction, item_id: str):
    user_id = str(interaction.user.id)
    
    # 檢查用戶是否存在
    if user_id not in user_data:
        await interaction.response.send_message("你還沒有帳戶！請先發送一些訊息。", ephemeral=True)
        return
    
    user = user_data[user_id]
    
    # 查找物品
    item = next((i for i in shop_items if i["id"] == item_id), None)
    
    if not item:
        await interaction.response.send_message("找不到該物品！請檢查物品ID。", ephemeral=True)
        return
    
    # 檢查金幣是否足夠
    if user["coins"] < item["price"]:
        await interaction.response.send_message(f"金幣不足！需要 🪙 {item['price']}，你只有 🪙 {user['coins']}。", ephemeral=True)
        return
    
    # 購買物品
    user["coins"] -= item["price"]
    
    # 處理不同類型物品
    if item["type"] == "title":
        user["title"] = item["name"]
        result = f"你現在擁有稱號: **{item['name']}**"
    elif item["type"] == "background":
        user["background"] = item["name"]
        result = f"你現在擁有個人背景: **{item['name']}**"
    elif item["type"] == "boost":
        # 雙倍經驗卡
        if item["id"] == "double_xp":
            expire_time = datetime.now().timestamp() + 86400  # 24小時後過期
            user["boosts"]["double_xp"] = expire_time
            result = "你獲得了24小時雙倍經驗加成！"
    elif item["type"] == "perk":
        # 自訂角色顏色
        if item["id"] == "role_color":
            result = "你已解鎖自訂角色顏色權限！請聯繫管理員設定。"
    else:
        # 一般物品
        if item["id"] not in user["inventory"]:
            user["inventory"][item["id"]] = 0
        user["inventory"][item["id"]] += 1
        result = f"你購買了 {item['name']} x1"
    
    # 保存數據
    save_user_data()
    
    embed = discord.Embed(
        title="🛒 購買成功",
        description=result,
        color=discord.Color.green()
    )
    embed.add_field(name="物品", value=item["name"])
    embed.add_field(name="花費", value=f"🪙 {item['price']}")
    embed.add_field(name="餘額", value=f"🪙 {user['coins']}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventory", description="查看你的背包")
async def inventory(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in user_data or not user_data[user_id].get("inventory"):
        await interaction.response.send_message("你的背包是空的！", ephemeral=True)
        return
    
    user = user_data[user_id]
    inventory = user["inventory"]
    
    embed = discord.Embed(
        title="🎒 背包",
        description="你擁有的物品",
        color=discord.Color.blue()
    )
    
    # 添加物品
    for item_id, quantity in inventory.items():
        item = next((i for i in shop_items if i["id"] == item_id), None)
        if item:
            embed.add_field(name=f"{item['name']} x{quantity}", value=item["description"], inline=False)
    
    # 添加稱號和背景
    if user.get("title"):
        embed.add_field(name="稱號", value=user["title"], inline=False)
    if user.get("background"):
        embed.add_field(name="個人背景", value=user["background"], inline=False)
    
    await interaction.response.send_message(embed=embed)

# ========================
# 管理命令
# ========================

@bot.tree.command(name="clear", description="清除指定數量的訊息")
@app_commands.describe(amount="要清除的訊息數量 (1-100)")
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 10):
    # 限制清除數量
    amount = min(max(amount, 1), 100)
    
    # 清除訊息
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    
    # 發送結果
    await interaction.followup.send(f"已清除 {len(deleted)} 條訊息！", ephemeral=True)

@bot.tree.command(name="mute", description="禁言指定成員")
@app_commands.describe(
    member="要禁言的成員", 
    duration="禁言時長 (分鐘)", 
    reason="禁言原因"
)
@app_commands.default_permissions(moderate_members=True)
async def mute(
    interaction: discord.Interaction, 
    member: discord.Member, 
    duration: int = 10, 
    reason: str = "違反伺服器規則"
):
    # 限制禁言時間
    duration = min(max(duration, 1), 1440)  # 1分鐘到24小時
    
    # 執行禁言
    await member.timeout(timedelta(minutes=duration), reason=reason)
    
    embed = discord.Embed(
        title="⛔ 成員已被禁言",
        color=discord.Color.red()
    )
    embed.add_field(name="成員", value=member.mention, inline=True)
    embed.add_field(name="時長", value=f"{duration} 分鐘", inline=True)
    embed.add_field(name="原因", value=reason, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unmute", description="解除成員禁言")
@app_commands.describe(member="要解除禁言的成員")
@app_commands.default_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    # 解除禁言
    await member.timeout(None)
    
    embed = discord.Embed(
        title="✅ 成員禁言已解除",
        description=f"{member.mention} 的禁言已被解除",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kick", description="踢出成員")
@app_commands.describe(member="要踢出的成員", reason="原因")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "違反伺服器規則"):
    # 踢出成員
    await member.kick(reason=reason)
    
    embed = discord.Embed(
        title="👢 成員已被踢出",
        color=discord.Color.orange()
    )
    embed.add_field(name="成員", value=member.mention, inline=True)
    embed.add_field(name="原因", value=reason, inline=True)
    
    await interaction.response.send_message(embed=embed)

# ========================
# 其他實用命令
# ========================

@bot.tree.command(name="help", description="顯示機器人幫助信息")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 機器人幫助菜單",
        description="以下是我可以執行的命令：",
        color=discord.Color.blue()
    )
    
    # 等級系統
    embed.add_field(
        name="🎚️ 等級系統",
        value="`/level` - 查看你的等級\n`/leaderboard` - 等級排行榜",
        inline=False
    )
    
    # 小遊戲
    embed.add_field(
        name="🎮 小遊戲",
        value="`/guess` - 猜數字遊戲\n`/g` - 猜數字\n`/slots` - 老虎機遊戲\n`/dice` - 擲骰子遊戲\n`/blackjack` - 21點遊戲",
        inline=False
    )
    
    # 占卜系統
    embed.add_field(
        name="🔮 占卜系統",
        value="`/fortune` - 每日塔羅牌占卜",
        inline=False
    )
    
    # 商店系統
    embed.add_field(
        name="🛒 商店系統",
        value="`/shop` - 查看商店\n`/buy` - 購買物品\n`/inventory` - 查看背包",
        inline=False
    )
    
    # 音樂系統
    embed.add_field(
        name="🎵 音樂系統",
        value=(
            "`/join` - 加入語音頻道\n"
            "`/leave` - 離開語音頻道\n"
            "`/play` - 播放音樂\n"
            "`/nowplaying` - 顯示當前播放\n"
            "`/pause` - 暫停播放\n"
            "`/resume` - 繼續播放\n"
            "`/skip` - 跳過歌曲\n"
            "`/stop` - 停止播放\n"
            "`/queue` - 顯示隊列\n"
            "`/volume` - 調整音量\n"
            "`/loop` - 單曲循環\n"
            "`/loopqueue` - 列表循環\n"
            "`/shuffle` - 打亂隊列\n"
            "`/history` - 播放歷史"
        ),
        inline=False
    )
    
    # 管理命令
    if interaction.user.guild_permissions.manage_messages:
        embed.add_field(
            name="🛠️ 管理命令",
            value="`/clear` - 清除訊息\n`/mute` - 禁言成員\n`/unmute` - 解除禁言\n`/kick` - 踢出成員",
            inline=False
        )
    
    embed.set_footer(text="機器人持續更新中！")
    await interaction.response.send_message(embed=embed)

# 運行機器人
if __name__ == "__main__":
    # 檢查FFmpeg是否可用
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("FFmpeg 已安裝，音樂功能可用")
    except FileNotFoundError:
        print("警告: FFmpeg 未安裝，音樂功能可能無法正常運作")
    
    # 安裝yt-dlp（如果尚未安裝）
    try:
        import yt_dlp
        print("yt-dlp 已安裝")
    except ImportError:
        print("安裝 yt-dlp...")
        try:
            subprocess.run(["pip", "install", "yt-dlp"], check=True)
            print("yt-dlp 安裝成功")
        except Exception as e:
            print(f"安裝 yt-dlp 失敗: {e}")
    
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("錯誤：找不到 Discord Token！請確認 .env 文件設置。")