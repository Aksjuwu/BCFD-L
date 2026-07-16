# cmds_FDScripts/description.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error, _truncate


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 1:
        resolved_text = ctx.resolve(args[0])
        ctx.embed_builder.description = resolved_text
        ctx.log_event(f"description → {_truncate(resolved_text)!r}")
    else:
        await _send_error(ch, FDLogicError("`$description` requires one argument: $description[text]"))