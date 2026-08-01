# cmds_FDScripts/color.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDLogicError, _send_error, _parse_color, _NAMED_COLORS,
)


def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    if args:
        ctx.embed_builder.color = _parse_color(ctx.resolve(args[0]).strip())
    return ""


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 1:
        resolved_color = ctx.resolve(args[0]).strip()
        if not resolved_color:
            await _send_error(ch, FDLogicError("`$color` requires a non-empty color value."))
            return
        ctx.embed_builder.color = _parse_color(resolved_color)
        ctx.log_event(f"color → {resolved_color!r}")
    else:
        await _send_error(ch, FDLogicError(
            "`$color` requires one argument: $color[hex or name]\n"
            f"Named colors: {', '.join(sorted(_NAMED_COLORS))}"
        ))