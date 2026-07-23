# Copyright (C) 2026 obgwew
# SPDX-License-Identifier: AGPL-3.0-or-later

# -*- coding: utf-8 -*-
# main_exe/core_fdsb/local_server.py 

import discord
from discord.ext import commands
import json
import os
import sys
import asyncio
import threading
import time
import flet as ft 
from main_exe.core_fdsb.FDScript import run_script
from main_exe.core_fdsb.FDCore   import set_vars_dir, set_bot_start_time

# ══════════════════════════════════════════════════════════════
#  Canonical event prefixes (single source of truth)
# ══════════════════════════════════════════════════════════════

EVENT_PREFIXES: set[str] = {
    '$onJoined',
    '$onLeave',
    '$onInteraction',
    '$onVoiceJoined',
    '$onVoiceLeave',
    '$alwaysReply',
    '$messageContains',
    '$messageContainsAll',
}

# ══════════════════════════════════════════════════════════════
#  PrefixManager 
# ══════════════════════════════════════════════════════════════

class PrefixManager:
    def __init__(self):
        self._bot_commands_dir = ''
        self._bot_events_dir = ''  

    def set_bot_dir(self, bot_dir: str):
        abs_dir = os.path.abspath(bot_dir)
        if os.path.basename(abs_dir).lower() == 'bot_files':
            bot_root = os.path.dirname(abs_dir)
        else:
            bot_root = abs_dir
        self._bot_commands_dir = os.path.join(bot_root, 'bot_commands')
        self._bot_events_dir = os.path.join(bot_root, 'bot_events') 

    def get_event_scripts(self, event_name: str) -> list[str]:
        results: list[str] = []
        if not os.path.isdir(self._bot_events_dir):
            return results

        for fname in sorted(os.listdir(self._bot_events_dir)):
            fpath = os.path.join(self._bot_events_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not content.strip():
                    continue

                first_line = content.split('\n')[0].strip().replace(" ", "").upper()
                if first_line.startswith("#PREFIX:"):
                    prefix_part = first_line.replace("#PREFIX:", "").split('[')[0]
                    if prefix_part == event_name.upper():
                        results.append(content)
            except Exception:
                pass
        return results

    def get_script_by_message(self, message_content: str) -> str | None:
        if not os.path.isdir(self._bot_commands_dir):
            return None

        for fname in os.listdir(self._bot_commands_dir):
            fpath = os.path.join(self._bot_commands_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    continue
                
                first_line = content.split('\n')[0].strip()
                if first_line.upper().startswith("#PREFIX:"):
                    prefix = first_line.split(":", 1)[1].strip()
                    after = message_content.strip()[len(prefix):]
                    if message_content.strip().startswith(prefix) and (not after or after[0].isspace()):
                        return content
            except Exception:
                pass
        return None

# ─────────────────────────────────────────────────────────────
#  setting up the bot 
# ─────────────────────────────────────────────────────────────

_client          = None
_thread          = None
_loop            = None
_stopping        = False
_vars_dir_path   = ''
prefix_manager   = PrefixManager()
_flet_page       = None  

def get_vars_dir() -> str:
    return _vars_dir_path

def _get_token(bot_dir: str) -> str:
    possible_paths = [
        os.path.join(bot_dir, 'config.json'),
        os.path.join(bot_dir, 'bot_files', 'config.json'),
        os.path.join(os.path.dirname(bot_dir), 'config.json'),
        os.path.join(os.path.dirname(bot_dir), 'bot_files', 'config.json'),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                
                token = data.get('token') or data.get('TOKEN') or data.get('bot_token')
                if token:
                    return str(token)
            except Exception:
                pass
    return ''

# ══════════════════════════════════════════════════════════════
#  Flet Notifications (Safe & Native SnackBar)
# ══════════════════════════════════════════════════════════════

def send_flet_notification(message: str):
    global _flet_page
    if _flet_page:
        try:
            _flet_page.snack_bar = ft.SnackBar(
                content=ft.Text(message, color=ft.colors.WHITE),
                bgcolor=ft.colors.BLUE_GREY_900,
                open=True,
                duration=4000
            )
            _flet_page.update()
        except Exception:
            pass

# ══════════════════════════════════════════════════════════════
#  Android Persistent Status Notification (using android_notify)
# ══════════════════════════════════════════════════════════════

def send_android_status_notification(bot_name: str, online: bool):
    try:
        from android_notify import Notification
    except ImportError:
        return

    if not (hasattr(sys, 'getandroidapilevel') or 'ANDROID_ARGUMENT' in os.environ):
        return

    status_text = "🟢 متصل ويعمل الآن" if online else "🔴 غير متصل"
    title = bot_name or "FDSB Bot"

    try:
        Notification(
            title=title,
            message=status_text,
            channel_id="fdsb_bot_status",
            channel_name="Bot Status",
            persistent=True, 
        ).send()
    except Exception as e:
        print(f"[AndroidNotif] send failed: {e}")

def clear_android_status_notification():
    try:
        from android_notify import NotificationHandler
    except ImportError:
        return

    try:
        NotificationHandler.cancelAll()
    except Exception as e:
        print(f"[AndroidNotif] clear failed: {e}")

# ══════════════════════════════════════════════════════════════
# event_FDScripts
# ══════════════════════════════════════════════════════════════

def _make_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True
    intents.presences = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"[Bot] Logged in successfully as: {bot.user}")
        set_bot_start_time(time.time())
        send_flet_notification(f"البوت نشط الآن: {bot.user}")
        await asyncio.sleep(3)
        send_android_status_notification(str(bot.user), online=True)
    
    @bot.event
    async def on_interaction(interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id")
        if not custom_id:
            return
        try:
            await interaction.response.defer()
        except Exception:
            pass
        from main_exe.core_fdsb.event_FDScripts.onInteraction import handle_event
        try:
            await handle_event(interaction, bot, custom_id, prefix_manager._bot_events_dir)
        except Exception as e:
            print(f"[Bot] Error executing $onInteraction event: {e}")

    @bot.event
    async def on_member_join(member):
        scripts = prefix_manager.get_event_scripts("$onJoined")
        if not scripts: return
        from main_exe.core_fdsb.event_FDScripts.onJoined import handle_event
        for script_text in scripts:
            try: await handle_event(member, bot, script_text)
            except Exception: pass

    @bot.event
    async def on_member_remove(member):
        scripts = prefix_manager.get_event_scripts("$onLeave")
        if not scripts: return
        from main_exe.core_fdsb.event_FDScripts.onLeave import handle_event
        for script_text in scripts:
            try: await handle_event(member, bot, script_text)
            except Exception: pass

    @bot.event
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        left_channel = before.channel if before.channel != after.channel else None
        joined_channel = after.channel if before.channel != after.channel else None

        if left_channel is not None:
            scripts = prefix_manager.get_event_scripts("$onVoiceLeave")
            if scripts:
                from main_exe.core_fdsb.event_FDScripts.onVoiceLeave import handle_event
                for script_text in scripts:
                    try: await handle_event(member, left_channel, bot, script_text)
                    except Exception: pass

        if joined_channel is not None:
            scripts = prefix_manager.get_event_scripts("$onVoiceJoined")
            if scripts:
                from main_exe.core_fdsb.event_FDScripts.onVoiceJoined import handle_event
                for script_text in scripts:
                    try: await handle_event(member, joined_channel, bot, script_text)
                    except Exception: pass

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        always_scripts = prefix_manager.get_event_scripts("$alwaysReply")
        if always_scripts:
            try:
                from main_exe.core_fdsb.event_FDScripts.alwaysReply import handle_event as handle_always_reply
                for script_text in always_scripts:
                    await handle_always_reply(message, bot, script_text)
            except Exception: pass

        try:
            from main_exe.core_fdsb.event_FDScripts.messageContains import handle_event as handle_message_contains
            await handle_message_contains(message, bot, prefix_manager._bot_events_dir)
        except Exception: pass

        try:
            from main_exe.core_fdsb.event_FDScripts.messageContainsAll import handle_event as handle_message_contains_all
            await handle_message_contains_all(message, bot, prefix_manager._bot_events_dir)
        except Exception: pass

        script_text = prefix_manager.get_script_by_message(message.content)
        if script_text is not None:
            try: await run_script(message, bot, script_text)
            except Exception: pass
            return

        await bot.process_commands(message)

    return bot

# ══════════════════════════════════════════════════════════════
#  Threading
# ══════════════════════════════════════════════════════════════

def _runner(token: str):
    global _loop, _client, _stopping
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    
    try:
        _loop.run_until_complete(_client.start(token))
    except Exception:
        pass
    finally:
        _stopping = False
        _client = None

def start_bot(bot_dir: str) -> bool:
    global _client, _thread, _stopping, _vars_dir_path

    if _stopping: return False
    if _client and not _client.is_closed(): return False

    token = _get_token(bot_dir)
    if not token: return False

    prefix_manager.set_bot_dir(bot_dir)

    abs_bot_dir = os.path.abspath(bot_dir)
    if os.path.basename(abs_bot_dir).lower() == 'bot_files':
        bot_root = os.path.dirname(abs_bot_dir)
    else:
        bot_root = abs_bot_dir

    _vars_dir_path = os.path.join(bot_root, 'bot_vars')
    os.makedirs(_vars_dir_path, exist_ok=True)
    set_vars_dir(_vars_dir_path)

    _client = _make_bot()
    _thread = threading.Thread(target=_runner, args=(token,), daemon=True)
    _thread.start()
    
    send_flet_notification("جاري تهيئة وتشغيل البوت...")
    return True

def stop_bot() -> None:
    global _stopping
    if _stopping: return
    if _client is None or _client.is_closed(): return
    _stopping = True
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_client.close(), _loop)
        
    send_flet_notification("تم إيقاف خدمة البوت.")
    clear_android_status_notification()

# ══════════════════════════════════════════════════════════════
#  Flet GUI & Android Background Permissions
# ══════════════════════════════════════════════════════════════

def request_flet_permissions(page: ft.Page):
    notif_status = page.get_permission_status(ft.PermissionType.NOTIFICATION)
    if notif_status != ft.PermissionStatus.GRANTED:
        page.request_permission(ft.PermissionType.NOTIFICATION)
    
    battery_status = page.get_permission_status(ft.PermissionType.IGNORE_BATTERY_OPTIMIZATIONS)
    if battery_status != ft.PermissionStatus.GRANTED:
        page.request_permission(ft.PermissionType.IGNORE_BATTERY_OPTIMIZATIONS)
    
    try:
        from android_notify.core import asks_permission_if_needed
        asks_permission_if_needed(legacy=True)
    except (ImportError, Exception):
        pass

def main_gui(page: ft.Page):
    global _flet_page
    _flet_page = page 
    
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    status_icon = ft.Icon(name=ft.icons.DNS, size=60, color=ft.colors.GREY)
    status_text = ft.Text(value="جاري التحميل...", size=16, weight=ft.FontWeight.BOLD)

    page.add(
        ft.Column(
            [status_icon, status_text],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

    def launch_sequence():
        request_flet_permissions(page)

        bot_directory = os.path.dirname(os.path.abspath(__file__))
        
        is_running = start_bot(bot_directory)

        if is_running:
            status_icon.color = ft.colors.GREEN
            status_text.value = "البوت متصل ويعمل حالياً"
        else:
            status_icon.color = ft.colors.RED
            status_text.value = "فشل بدء البوت"
            
        page.update()

    page.run_task(launch_sequence)

if __name__ == "__main__":
    ft.app(target=main_gui)