# cmds_FDScripts/splitIn.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) < 2:
        await _send_error(ch, FDLogicError(
            "`$splitIn` requires two arguments: `$splitIn[text; delimiter]`"
        ))
        return

    text      = ctx.resolve(args[0])
    delimiter = ctx.resolve(args[1])

    if not delimiter:
        await _send_error(ch, FDLogicError(
            "`$splitIn` — delimiter cannot be empty"
        ))
        return

    parts = [part.strip() for part in text.split(delimiter)]

    ctx.split_result = parts

    ctx.log_event(f"splitIn → split into {len(parts)} part(s) using delimiter `{delimiter}`")