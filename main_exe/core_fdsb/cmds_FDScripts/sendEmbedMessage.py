# cmds_FDScripts/sendEmbedMessage.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDLogicError, FDRuntimeError, FDEnvironmentError,
    _send_error, _parse_color, _truncate,
)


def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    return ""


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) < 5 or not args[4].strip():
        await _send_error(ch, FDLogicError(
            "`$sendEmbedMessage` requires 5 mandatory arguments:\n"
            "`$sendEmbedMessage[channelID; title; description; color; footer]`"
        ))
        return

    ch_id_str = args[0].strip()
    try:
        ch_id = int(ch_id_str)
    except ValueError:
        await _send_error(ch, FDLogicError(
            f"`$sendEmbedMessage` — invalid channel ID: `{ch_id_str}`"
        ))
        return

    target_ch = ctx.bot.get_channel(ch_id)
    if not target_ch:
        await _send_error(ch, FDEnvironmentError(
            f"`$sendEmbedMessage` — channel `{ch_id_str}` not found or bot has no access"
        ))
        return

    embed = discord.Embed(
        title=args[1],
        description=args[2],
        color=_parse_color(args[3]),
    )
    if args[4].strip():
        embed.set_footer(text=args[4])

    try:
        ctx.stop_typing()
        sent = await target_ch.send(embed=embed)
        ctx.last_bot_message = sent
        ctx.log_event(f"sendEmbedMessage [{_truncate(args[1])}] → sent to channel {ch_id_str}")
    except discord.Forbidden:
        await _send_error(ch, FDEnvironmentError(
            f"`$sendEmbedMessage` — bot lacks permission to send in channel `{ch_id_str}`"
        ))
    except discord.HTTPException as e:
        await _send_error(ch, FDRuntimeError(
            f"`$sendEmbedMessage` — failed to send: `{e.text}`"
        ))