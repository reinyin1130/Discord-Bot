import discord
from discord import app_commands
from discord.ext import commands


from core.classes import Cog
from classes.music_class import MusicPlayer

# 全局音樂播放器字典
music_players = {}


class Music(Cog):
    """
    音樂命令
    """

    def get_music_player(self, guild_id):
        if guild_id not in music_players:
            music_players[guild_id] = MusicPlayer(self.bot)
        return music_players[guild_id]

    @app_commands.command(name="join", description="讓機器人加入語音頻道")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ 請先加入一個語音頻道！", ephemeral=True
            )
            return

        voice_channel = interaction.user.voice.channel
        player = self.get_music_player(interaction.guild_id)

        try:
            await player.connect(voice_channel)
            await interaction.response.send_message(
                f"✅ 已加入 **{voice_channel.name}**"
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 加入語音頻道時出錯: {e}", ephemeral=True
            )

    @app_commands.command(name="leave", description="讓機器人離開語音頻道")
    async def leave(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.voice_client or not player.voice_client.is_connected():
            await interaction.response.send_message(
                "❌ 機器人不在任何語音頻道中！", ephemeral=True
            )
            return

        try:
            await player.disconnect()
            await interaction.response.send_message("✅ 已離開語音頻道")
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 離開語音頻道時出錯: {e}", ephemeral=True
            )

    @app_commands.command(name="play", description="播放音樂或將音樂加入隊列")
    @app_commands.describe(query="歌曲名稱或YouTube連結")
    async def play(self, interaction: discord.Interaction, query: str):
        # 檢查用戶是否在語音頻道
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ 請先加入一個語音頻道！", ephemeral=True
            )
            return

        player = self.get_music_player(interaction.guild_id)

        # 如果機器人不在語音頻道，加入用戶所在的頻道
        if not player.voice_client or not player.voice_client.is_connected():
            voice_channel = interaction.user.voice.channel
            try:
                await player.connect(voice_channel)
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ 加入語音頻道時出錯: {e}", ephemeral=True
                )
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
            try:
                song = player.queue[-1] if player.playing else player.current_song
                message = f"🎵 已將 **{song['title']}** 加入隊列"
            except IndexError:
                song = player.current_song or {"title": "未知歌曲"}
                message = f"🎵 已將 **{song['title']}** 加入隊列"

        await interaction.followup.send(message)

    @app_commands.command(name="nowplaying", description="顯示當前播放的歌曲")
    async def nowplaying(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.current_song:
            await interaction.response.send_message(
                "❌ 當前沒有播放任何歌曲！", ephemeral=True
            )
            return

        song = player.current_song
        duration = player.format_duration(song["duration"])
        progress = ""

        # 如果正在播放，顯示進度條
        if player.voice_client and player.voice_client.is_playing():
            position = (
                player.voice_client.source.played
                if hasattr(player.voice_client.source, "played")
                else 0
            )
            position_str = player.format_duration(position)

            # 進度條
            progress_percent = (
                min(1.0, max(0.0, position / song["duration"]))
                if song["duration"] > 0
                else 0
            )
            progress_bar_length = 20
            filled_length = int(progress_percent * progress_bar_length)
            progress_bar = (
                "▬" * filled_length
                + "🔘"
                + "▬" * (progress_bar_length - filled_length - 1)
            )
            progress = f"\n\n{progress_bar}\n{position_str} / {duration}"

        embed = discord.Embed(
            title="🎵 正在播放",
            description=f"[{song['title']}]({song['webpage_url']}){progress}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="時長", value=duration, inline=True)
        embed.add_field(name="點播者", value=song["requester"].mention, inline=True)

        if song["thumbnail"]:
            embed.set_thumbnail(url=song["thumbnail"])

        # 添加控制按鈕
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.secondary, emoji="⏮️", custom_id="previous"
            )
        )
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.secondary, emoji="⏯️", custom_id="pause_resume"
            )
        )
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="skip"
            )
        )
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="loop"
            )
        )
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="stop"
            )
        )

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="pause", description="暫停當前播放的歌曲")
    async def pause(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.voice_client or not player.voice_client.is_playing():
            await interaction.response.send_message(
                "❌ 當前沒有播放任何歌曲！", ephemeral=True
            )
            return

        player.voice_client.pause()
        await interaction.response.send_message("⏸️ 已暫停播放")

    @app_commands.command(name="resume", description="繼續播放暫停的歌曲")
    async def resume(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.voice_client or not player.voice_client.is_paused():
            await interaction.response.send_message(
                "❌ 當前沒有暫停的歌曲！", ephemeral=True
            )
            return

        player.voice_client.resume()
        await interaction.response.send_message("▶️ 已繼續播放")

    @app_commands.command(name="skip", description="跳過當前播放的歌曲")
    async def skip(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.voice_client or not player.voice_client.is_playing():
            await interaction.response.send_message(
                "❌ 當前沒有播放任何歌曲！", ephemeral=True
            )
            return

        await player.skip()
        await interaction.response.send_message("⏭️ 已跳過當前歌曲")

    @app_commands.command(name="stop", description="停止播放並清空隊列")
    async def stop(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.voice_client or not (
            player.voice_client.is_playing() or player.voice_client.is_paused()
        ):
            await interaction.response.send_message(
                "❌ 當前沒有播放任何歌曲！", ephemeral=True
            )
            return

        await player.stop()
        await interaction.response.send_message("⏹️ 已停止播放並清空隊列")

    @app_commands.command(name="queue", description="顯示當前播放隊列")
    async def queue(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.queue and not player.current_song:
            await interaction.response.send_message("❌ 隊列是空的！", ephemeral=True)
            return

        embed = discord.Embed(title="🎵 播放隊列", color=discord.Color.green())

        # 當前播放的歌曲
        if player.current_song:
            song = player.current_song
            duration = player.format_duration(song["duration"])
            embed.add_field(
                name="正在播放",
                value=f"[{song['title']}]({song['webpage_url']})\n時長: {duration} | 點播者: {song['requester'].mention}",
                inline=False,
            )

        # 隊列中的歌曲
        if player.queue:
            queue_list = []
            for i, song in enumerate(list(player.queue[:10]), 1):  # 只顯示前10首
                duration = player.format_duration(song["duration"])
                queue_list.append(
                    f"{i}. [{song['title']}]({song['webpage_url']}) ({duration}) | {song['requester'].mention}"
                )

            embed.add_field(
                name=f"待播歌曲 ({len(player.queue)}首)",
                value="\n".join(queue_list),
                inline=False,
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

    @app_commands.command(name="volume", description="調整音量 (0-100)")
    @app_commands.describe(level="音量等級 (0-100)")
    async def volume(self, interaction: discord.Interaction, level: int):
        player = self.get_music_player(interaction.guild_id)

        if level < 0 or level > 100:
            await interaction.response.send_message(
                "❌ 音量必須在0-100之間！", ephemeral=True
            )
            return

        volume_level = level / 100.0

        try:
            await player.set_volume(volume_level)
            await interaction.response.send_message(f"🔊 音量已設定為 **{level}%**")
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 調整音量時出錯: {e}", ephemeral=True
            )

    @app_commands.command(name="loop", description="切換單曲循環模式")
    async def loop(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        player.loop = not player.loop
        if player.loop:
            player.loop_queue = False

        status = "啟用" if player.loop else "停用"
        await interaction.response.send_message(f"🔂 單曲循環模式已 **{status}**")

    @app_commands.command(name="loopqueue", description="切換列表循環模式")
    async def loopqueue(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        player.loop_queue = not player.loop_queue
        if player.loop_queue:
            player.loop = False

        status = "啟用" if player.loop_queue else "停用"
        await interaction.response.send_message(f"🔁 列表循環模式已 **{status}**")

    @app_commands.command(name="shuffle", description="隨機打亂播放隊列")
    async def shuffle(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.queue:
            await interaction.response.send_message("❌ 隊列是空的！", ephemeral=True)
            return

        random.shuffle(player.queue)
        await interaction.response.send_message("🔀 已隨機打亂播放隊列")

    @app_commands.command(name="history", description="顯示最近播放的歌曲")
    async def history(self, interaction: discord.Interaction):
        player = self.get_music_player(interaction.guild_id)

        if not player.history:
            await interaction.response.send_message("❌ 沒有播放歷史！", ephemeral=True)
            return

        embed = discord.Embed(title="⏮️ 播放歷史", color=discord.Color.purple())

        history_list = []
        for i, song in enumerate(player.history, 1):
            duration = player.format_duration(song["duration"])
            history_list.append(
                f"{i}. [{song['title']}]({song['webpage_url']}) ({duration}) | {song['requester'].mention}"
            )

        embed.description = "\n".join(history_list)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
