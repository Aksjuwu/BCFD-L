# cmds_FDScripts/httpPatch.py
import discord
import requests
import json
from FDScript import ExecutionContext, Command, FDSyntaxError

def _process(args: list[str], ctx: ExecutionContext) -> str:
    if len(args) < 1:
        ctx._abort_with_error(FDSyntaxError("`$httpPatch` requires at least 1 arg: `$httpPatch[URL;(Body)]`"))
        
    url = ctx.resolve(args[0]).strip()
    body_raw = ctx.resolve(args[1]) if len(args) > 1 else None
    headers = getattr(ctx, "http_headers", {})
    
    json_data = None
    data = None
    if body_raw:
        try:
            json_data = json.loads(body_raw)
        except:
            data = body_raw
    
    try:
        res = requests.patch(url, headers=headers, json=json_data, data=data, timeout=10)
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