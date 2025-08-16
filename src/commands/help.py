import discord
from discord import app_commands
from discord.ext import commands

from core.classes import Cog


class Help(Cog):
    @app_commands.command(name="help", description="顯示機器人幫助信息")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 機器人幫助菜單",
            description="以下是我可以執行的命令：",
            color=discord.Color.blue(),
        )

        # 等級系統
        embed.add_field(
            name="🎚️ 等級系統",
            value="`/level` - 查看你的等級\n`/leaderboard` - 等級排行榜",
            inline=False,
        )

        # 小遊戲
        embed.add_field(
            name="🎮 小遊戲",
            value="`/guess` - 猜數字遊戲\n`/g` - 猜數字\n`/slots` - 老虎機遊戲\n`/dice` - 擲骰子遊戲\n`/blackjack` - 21點遊戲",
            inline=False,
        )

        # 占卜系統
        embed.add_field(
            name="🔮 占卜系統", value="`/fortune` - 每日塔羅牌占卜", inline=False
        )

        # 商店系統
        embed.add_field(
            name="🛒 商店系統",
            value="`/shop` - 查看商店\n`/buy` - 購買物品\n`/inventory` - 查看背包",
            inline=False,
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
            inline=False,
        )

        # 管理命令
        if interaction.user.guild_permissions.manage_messages:
            embed.add_field(
                name="🛠️ 管理命令",
                value="`/clear` - 清除訊息\n`/mute` - 禁言成員\n`/unmute` - 解除禁言\n`/kick` - 踢出成員",
                inline=False,
            )

        embed.set_footer(text="機器人持續更新中！")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
