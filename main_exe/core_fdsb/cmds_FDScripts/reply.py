# cmds_FDScripts/reply.py
import discord
from FDScript import ExecutionContext, Command

async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    ctx.is_global_reply = True
    ctx.log_event("reply → reply mode enabled")