import discord
import os
from discord.ext import commands
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
LEADER_ROLE_NAME = "cc"
MANAGER_ROLE_NAME = "Quản Lý"

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==================================================
# MÀU SẮC EMBED
# ==================================================
COLOR_SUCCESS = 0x2ECC71
COLOR_ERROR   = 0xE74C3C
COLOR_INFO    = 0x3498DB
COLOR_WARN    = 0xF39C12

def footer(embed: discord.Embed, ctx):
    embed.set_footer(
        text=f"Thực hiện bởi {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url
    )
    embed.timestamp = datetime.now()
    return embed

# ==================================================
# KIỂM TRA ROLE — cc hoặc Quản Lý
# ==================================================
def is_leader():
    async def predicate(ctx):
        allowed = {LEADER_ROLE_NAME, MANAGER_ROLE_NAME}
        return any(role.name in allowed for role in ctx.author.roles)
    return commands.check(predicate)

# ==================================================
# LỆNH !veroom
# ==================================================
@bot.command()
@is_leader()
async def veroom(ctx):
    member = ctx.author
    nickname = member.nick or member.name

    if "|" not in nickname:
        embed = discord.Embed(
            title="❌ Lỗi định dạng tên",
            description="Tên của bạn không đúng định dạng `CREW | Tên`.",
            color=COLOR_ERROR
        )
        footer(embed, ctx)
        await ctx.send(embed=embed)
        return

    crew = nickname.split("|")[0].strip()
    target_channel = discord.utils.get(ctx.guild.voice_channels, name=crew)

    if not target_channel:
        embed = discord.Embed(
            title="❌ Không tìm thấy kênh",
            description=f"Không tìm thấy kênh thoại tên **{crew}**.",
            color=COLOR_ERROR
        )
        footer(embed, ctx)
        await ctx.send(embed=embed)
        return

    moved_members = []
    for m in ctx.guild.members:
        nick = m.nick or m.name
        if nick.startswith(crew) and m.voice and m.voice.channel and m.voice.channel != target_channel:
            try:
                from_channel = m.voice.channel.name
                await m.move_to(target_channel)
                moved_members.append((m.display_name, from_channel))
            except:
                pass

    embed = discord.Embed(title=f"🔊 Tập hợp crew {crew}", color=COLOR_SUCCESS)
    embed.add_field(name="Kênh đích", value=f"🔈 {target_channel.name}", inline=True)
    embed.add_field(name="Số người kéo", value=f"**{len(moved_members)}** thành viên", inline=True)
    footer(embed, ctx)
    await ctx.send(embed=embed)

# ==================================================
# LỆNH !allroom
# ==================================================
@bot.command()
@is_leader()
async def allroom(ctx):
    target_channel = None
    for vc in ctx.guild.voice_channels:
        if vc.name.lower().replace(" ", "") == "allroom":
            target_channel = vc
            break

    if not target_channel:
        embed = discord.Embed(
            title="❌ Không tìm thấy kênh",
            description="Không tìm thấy kênh thoại **All Room**.",
            color=COLOR_ERROR
        )
        footer(embed, ctx)
        await ctx.send(embed=embed)
        return

    moved_members = []
    for m in ctx.guild.members:
        if m.voice and m.voice.channel and m.voice.channel != target_channel:
            try:
                await m.move_to(target_channel)
                moved_members.append(m.display_name)
            except:
                pass

    embed = discord.Embed(title="🌐 Tập hợp", color=COLOR_INFO)
    embed.add_field(name="Kênh đích", value=f"🔈 {target_channel.name}", inline=True)
    embed.add_field(name="Số người kéo", value=f"**{len(moved_members)}** thành viên", inline=True)
    footer(embed, ctx)
    await ctx.send(embed=embed)

# ==================================================
# HÀM LẤY TÊN NHÂN VẬT INGAME (GTA5VN)
# ==================================================
def get_ingame_name(member: discord.Member) -> str:
    for activity in member.activities:
        if isinstance(activity, (discord.CustomActivity, discord.Spotify)):
            continue

        for field in ['state', 'details']:
            value = getattr(activity, field, None)
            if value and "|" in value:
                after_pipe = value.split("|", 1)[1].strip()
                name_parts = []
                for word in after_pipe.split():
                    if word.lower() == "đang":
                        break
                    name_parts.append(word)
                if name_parts:
                    return " ".join(name_parts)

        if hasattr(activity, 'name') and activity.name:
            return activity.name

    return None

# ==================================================
# LỆNH !debugcheck
# ==================================================
@bot.command()
@is_leader()
async def debugcheck(ctx):
    if not ctx.author.voice:
        await ctx.send("Bạn phải ở trong voice channel.")
        return
    channel = ctx.author.voice.channel
    msg = ""
    for member in channel.members:
        if member.bot:
            continue
        msg += f"\n**{member.display_name}**:\n"
        for act in member.activities:
            msg += f"  - type={type(act).__name__}, name={getattr(act,'name',None)}, details={getattr(act,'details',None)}\n"
    await ctx.send(msg[:2000] or "Không có activity nào.")

# ==================================================
# LỆNH !check
# ==================================================
@bot.command()
@is_leader()
async def check(ctx):
    if not ctx.author.voice:
        embed = discord.Embed(
            title="❌ Chưa vào kênh thoại",
            description="Bạn phải ở trong voice channel để dùng lệnh này.",
            color=COLOR_ERROR
        )
        footer(embed, ctx)
        await ctx.send(embed=embed)
        return

    channel = ctx.author.voice.channel
    has_game = []
    no_game = []

    for member in channel.members:
        if member.bot:
            continue
        ingame = get_ingame_name(member)
        if ingame:
            has_game.append(f"• **{member.display_name}** → `{ingame}`")
        else:
            no_game.append(f"• {member.display_name}")

    embed = discord.Embed(title=f"🎮 Check Room — {channel.name}", color=COLOR_INFO)

    if has_game:
        embed.add_field(name=f"✅ Đang chơi ({len(has_game)} người)", value="\n".join(has_game), inline=False)
    if no_game:
        embed.add_field(name=f"⚠️ Không bật hoạt động ({len(no_game)} người)", value="\n".join(no_game), inline=False)
    if not has_game and not no_game:
        embed.description = "Không có thành viên nào trong kênh."

    footer(embed, ctx)
    await ctx.send(embed=embed)

# ==================================================
# LỆNH !room
# ==================================================
@bot.command()
@is_leader()
async def room(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        embed = discord.Embed(
            title="❌ Chưa vào kênh thoại",
            description="Bạn phải đang ở trong một voice channel để dùng lệnh này.",
            color=COLOR_ERROR
        )
        footer(embed, ctx)
        await ctx.send(embed=embed)
        return

    target_channel = ctx.author.voice.channel
    moved_members = []

    for m in ctx.guild.members:
        if m.voice and m.voice.channel and m.voice.channel != target_channel:
            try:
                await m.move_to(target_channel)
                moved_members.append(m.display_name)
            except:
                pass

    embed = discord.Embed(title=f"📥 Tập hợp về kênh {target_channel.name}", color=COLOR_SUCCESS)
    embed.add_field(name="Kênh đích", value=f"🔈 {target_channel.name}", inline=True)
    embed.add_field(name="Số người kéo", value=f"**{len(moved_members)}** thành viên", inline=True)
    footer(embed, ctx)
    await ctx.send(embed=embed)

# ==================================================
# LỆNH !kickroom
# ==================================================
@bot.command()
@is_leader()
async def kickroom(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        embed = discord.Embed(
            title="❌ Chưa vào kênh thoại",
            description="Bạn phải ở trong voice channel để dùng lệnh này.",
            color=COLOR_ERROR
        )
        footer(embed, ctx)
        await ctx.send(embed=embed)
        return

    channel = ctx.author.voice.channel
    kicked = []

    for member in channel.members:
        if member.bot:
            continue
        ingame = None
        for activity in member.activities:
            if activity.type == discord.ActivityType.playing:
                ingame = activity.name
        if not ingame:
            try:
                await member.move_to(None)
                kicked.append(member.mention)
            except:
                pass

    if kicked:
        embed = discord.Embed(title="👢 Kick thành viên nghi ngờ spy", color=COLOR_WARN)
        embed.add_field(
            name=f"Đã kick {len(kicked)} người",
            value="\n".join(f"• {mention}" for mention in kicked),
            inline=False
        )
    else:
        embed = discord.Embed(
            title="✅ Không có spy",
            description="Tất cả mọi người đều đang bật hoạt động game.",
            color=COLOR_SUCCESS
        )

    footer(embed, ctx)
    await ctx.send(embed=embed)

# ==================================================
# LỖI PERMISSION
# ==================================================
@veroom.error
@allroom.error
@check.error
@kickroom.error
@room.error
@debugcheck.error
async def permission_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        embed = discord.Embed(
            title="🚫 Không có quyền",
            description="Bạn không có quyền dùng lệnh này.",
            color=COLOR_ERROR
        )
        footer(embed, ctx)
        await ctx.send(embed=embed)

bot.run(TOKEN)
