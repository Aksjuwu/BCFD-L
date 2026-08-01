# cmds_FDScripts/onlyIf.py
import discord
from main_exe.core_fdsb.FDScript import (
    ExecutionContext, Command,
    FDLogicError, FDAbortScript, _send_error, evaluate_condition
)

def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    if len(args) < 2:
        return "false"
    from main_exe.core_fdsb.FDScript import evaluate_condition
    return "true" if evaluate_condition(args[0].strip(), ctx) else "false"


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(cmd.args) < 2:
        await _send_error(ch, FDLogicError(
            "`$onlyIf` requires a condition and an error message separated by a semicolon `;` — "
            "example: `$onlyIf[x == y; Custom Error Message!]`"
        ))
        # تم حذف الـ return الميت هنا لأن _send_error ترفع استثناءً يقطع التنفيذ تلقائياً

    # المشكلة الأولى: استخدام المعاملات المحلولة مسبقاً (Resolved) لضمان الاتساق ومنع خلط المفاهيم
    cond_str  = args[0].strip()
    error_msg = args[1].strip()

    result = evaluate_condition(cond_str, ctx)
    ctx.log_event(f"onlyIf [{cond_str}] → {'✓ Passed' if result else '✗ Failed'}")

    if not result:
        ctx.stop_typing()
        dest = await ctx.get_dest()
        if error_msg:
            sent = await dest.send(error_msg)
            ctx.last_bot_message = sent
        ctx.log_event("onlyIf → Aborting script execution.")
        raise FDAbortScript()