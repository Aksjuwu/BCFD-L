# cmds_FDScripts/setVar.py
import discord
from main_exe.core_fdsb.FDCore import (
    ExecutionContext, Command,
    FDLogicError, FDRuntimeError,
    _send_error, _load_data, _save_data,
    _load_ids_data, _save_ids_data, _truncate,
)

def _fmt(err) -> str:
    return f"{err._icon} **{err._category}** — {err.msg}"

def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    return _fmt(FDLogicError("`$setVar` cannot be used inline — use it as a standalone command."))

async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 3:
        name    = ctx.resolve(args[0]).strip()
        value   = ctx.resolve(args[1])
        user_id = ctx.resolve(args[2]).strip()

        if not name:
            await _send_error(ch, FDLogicError("`$setVar` — variable name cannot be empty."))
            return
        if not user_id:
            await _send_error(ch, FDLogicError("`$setVar` — user ID cannot be empty."))
            return

        data = _load_ids_data()
        if name not in data:
            data[name] = {}
        data[name][user_id] = value
        _save_ids_data(data)
        ctx.log_event(f"setVar [{name}] for user {user_id} ← {_truncate(value)!r} (persistent)")

    elif len(args) == 2:
        name  = ctx.resolve(args[0]).strip()
        value = ctx.resolve(args[1])

        if not name:
            await _send_error(ch, FDLogicError("`$setVar` — variable name cannot be empty."))
            return

        data = _load_data()
        data[name] = value
        _save_data(data)
        ctx.log_event(f"setVar [{name}] ← {_truncate(value)!r} (persistent)")

    else:
        await _send_error(ch, FDLogicError(
            "`$setVar` requires 2 or 3 arguments: `$setVar[name; value]` or `$setVar[name; value; user_id]`"
        ))