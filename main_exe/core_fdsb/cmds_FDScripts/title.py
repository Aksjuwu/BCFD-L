# cmds_FDScripts/title.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error, _truncate


def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    if args:
        ctx.embed_builder.title = ctx.resolve(args[0])
    return ""


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 1:
        resolved_text = ctx.resolve(args[0])
        ctx.embed_builder.title = resolved_text
        ctx.log_event(f"title → {_truncate(resolved_text)!r}")
    else:
        await _send_error(ch, FDLogicError("`$title` requires one argument: $title[text]"))