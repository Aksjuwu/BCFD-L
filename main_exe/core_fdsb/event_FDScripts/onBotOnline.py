# main_exe/core_fdsb/event_FDScripts/onBotOnline.py
import discord
from main_exe.core_fdsb.FDScript import run_script


async def handle_event(bot: discord.Client, script_text: str) -> None:
    try:
        await run_script(None, bot, script_text, is_event=True)
    except Exception as e:
        print(f"[onBotOnline Event Error] : {e}")