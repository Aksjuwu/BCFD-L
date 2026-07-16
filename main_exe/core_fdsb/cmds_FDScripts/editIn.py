# cmds_FDScripts/editIn.py
import asyncio
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error


def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    return ""

async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) < 2:
        await _send_error(ch, FDLogicError(
            "`$editIn` requires at least 2 arguments: `$editIn[time; newMessage]`"
        ))
        return

    time_str = args[0].strip().lower()
    
    new_message = args[1].strip()

    if not time_str:
        await _send_error(ch, FDLogicError("`$editIn` — Time argument cannot be empty."))
        return

    unit = time_str[-1]
    val_str = time_str[:-1]

    if unit not in ('s', 'm', 'h', 'd') or not val_str.isdigit():
        await _send_error(ch, FDLogicError(
            f"`$editIn` — Invalid time format '{time_str}'. Use numbers followed by s, m, h, or d (e.g., 5s, 10m)."
        ))
        return

    val = int(val_str)
    if unit == 's':
        seconds = val
    elif unit == 'm':
        seconds = val * 60
    elif unit == 'h':
        seconds = val * 3600
    elif unit == 'd':
        seconds = val * 86400

    target_msg = getattr(ctx, "last_bot_message", None)
    
    if target_msg is None:
        await _send_error(ch, FDLogicError(
            "`$editIn` — No previous bot message found. You must send a message before using this command."
        ))
        return

    await asyncio.sleep(seconds)

    try:
        await target_msg.edit(content=new_message)
    except discord.NotFound:
        pass 
    except discord.Forbidden:
        pass 
    except discord.HTTPException:
        pass 

    ctx.log_event(f"editIn → Edited message ID: {target_msg.id} after {seconds}s")