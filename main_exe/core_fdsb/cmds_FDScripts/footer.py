# cmds_FDScripts/footer.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error, _truncate


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 1:
        resolved_text = ctx.resolve(args[0])
        ctx.embed_builder.footer = resolved_text
        ctx.log_event(f"footer → {_truncate(resolved_text)!r}")
    else:
        await _send_error(ch, FDLogicError("`$footer` requires one argument: $footer[text]"))