# cmds_FDScripts/httpGet.py
import discord
import requests
from FDScript import ExecutionContext, Command, FDSyntaxError

def _process(args: list[str], ctx: ExecutionContext) -> str:
    if len(args) < 1:
        ctx._abort_with_error(FDSyntaxError("`$httpGet` requires 1 arg: `$httpGet[URL]`"))
        
    url = ctx.resolve(args[0]).strip()
    headers = getattr(ctx, "http_headers", {})
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        ctx.http_status = res.status_code
        try:
            ctx.http_result = res.json()
        except:
            ctx.http_result = res.text
    except Exception as e:
        ctx.http_status = 500
        ctx.http_result = str(e)
        
    ctx.http_headers = {}
    return ""

def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    return _process(args, ctx)

async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    _process(args, ctx)