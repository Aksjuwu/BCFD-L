# cmds_FDScripts/getVar.py
import discord
from main_exe.core_fdsb.FDCore import (
    ExecutionContext, Command,
    FDLogicError, FDRuntimeError,
    _send_error, _load_data, _load_ids_data, _truncate,
)

def _fmt(err) -> str:
    return f"{err._icon} **{err._category}** — {err.msg}"

def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    resolved_args = [ctx.resolve(a) for a in args]
    
    if len(resolved_args) == 2:
        name    = resolved_args[0].strip()
        user_id = resolved_args[1].strip()
        if not name:
            ctx.log_event("getVar inline error: empty variable name")
            return ""
        if not user_id:
            ctx.log_event("getVar inline error: empty user ID")
            return ""
        data = _load_ids_data()
        val  = data.get(name, {}).get(user_id, '')
        ctx.log_event(f"getVar [{name}] for user {user_id} → {_truncate(val)!r}")
        return str(val)

    elif len(resolved_args) == 1:
        name = resolved_args[0].strip()
        if not name:
            ctx.log_event("getVar inline error: empty variable name")
            return ""
        data = _load_data()
        val = str(data.get(name, ''))
        ctx.log_event(f"getVar [{name}] → {_truncate(val)!r}")
        return val

    else:
        ctx.log_event("getVar inline error: invalid argument count")
        return ""

async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    result = resolve_inline(args, ctx)
    if result:
        await ch.send(result)