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

try:
    from flet_android_notifications import FletAndroidNotifications
except ImportError:
    FletAndroidNotifications = None

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
    '$onBotOnline',
    '$onBotMessage',
    '$onBoostServer',
}

_BOOST_MESSAGE_TYPES = {
    discord.MessageType.premium_guild_subscription,
    discord.MessageType.premium_guild_tier_1,
    discord.MessageType.premium_guild_tier_2,
    discord.MessageType.premium_guild_tier_3,
}

# ══════════════════════════════════════════════════════════════
#  Status Bot — presence rotation (mirrors status_view.py)
# ══════════════════════════════════════════════════════════════

_STATUS_DISCORD_STATE = {
    'online':    discord.Status.online,
    'idle':      discord.Status.idle,
    'dnd':       discord.Status.dnd,
    'invisible': discord.Status.invisible,
}

_STATUS_ACTIVITY_TYPE = {
    'playing':    discord.ActivityType.playing,
    'listening':  discord.ActivityType.listening,
    'watching':   discord.ActivityType.watching,
    'competing':  discord.ActivityType.competing,
}

_STATUS_LOOP_UNIT_SECONDS = {
    'second': 1,
    'minute': 60,
    'hour':   3600,
    'day':    86400,
}

_STATUS_LOOP_TIME_MIN_SECONDS = 12
_STATUS_POLL_IDLE_SECONDS = 15

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
_status_task     = None
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

def _load_status_config(bot_dir: str) -> dict | None:
    possible_paths = [
        os.path.join(bot_dir, 'bot_files', 'status_config.json'),
        os.path.join(bot_dir, 'status_config.json'),
        os.path.join(os.path.dirname(bot_dir), 'bot_files', 'status_config.json'),
        os.path.join(os.path.dirname(bot_dir), 'status_config.json'),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return None

def _build_status_activity(entry: dict):
    activity_type = (entry.get('activity_type') or 'playing').strip().lower()
    status_text   = (entry.get('status') or '').strip()

    if activity_type == 'streaming':
        url = (entry.get('stream_url') or '').strip()
        if not url:
            return None
        return discord.Streaming(name=status_text or 'Live', url=url)

    if not status_text:
        return None

    activity_enum = _STATUS_ACTIVITY_TYPE.get(
        activity_type, discord.ActivityType.playing
    )
    return discord.Activity(type=activity_enum, name=f"● {status_text}")

async def _status_rotator(bot, bot_dir: str):
    try:
        while not bot.is_closed():
            config = _load_status_config(bot_dir)

            if not config or not config.get('enabled'):
                await asyncio.sleep(_STATUS_POLL_IDLE_SECONDS)
                continue

            discord_status = _STATUS_DISCORD_STATE.get(
                (config.get('status') or 'online').strip().lower(),
                discord.Status.online,
            )

            raw_entries = config.get('entries') or []
            entries = [
                e for e in raw_entries
                if (e.get('status') or '').strip()
                or (
                    (e.get('activity_type') or '').strip().lower() == 'streaming'
                    and (e.get('stream_url') or '').strip()
                )
            ]

            loop_unit = (config.get('loop_unit') or 'second').strip().lower()
            try:
                loop_time = int(config.get('loop_time') or 30)
            except (TypeError, ValueError):
                loop_time = 30
            interval = max(
                loop_time * _STATUS_LOOP_UNIT_SECONDS.get(loop_unit, 1),
                _STATUS_LOOP_TIME_MIN_SECONDS,
            )

            if not entries:
                try:
                    await bot.change_presence(status=discord_status, activity=None)
                except Exception:
                    pass
                await asyncio.sleep(_STATUS_POLL_IDLE_SECONDS)
                continue

            for entry in entries:
                if bot.is_closed():
                    return

                activity = _build_status_activity(entry)
                try:
                    await bot.change_presence(
                        status=discord_status,
                        activity=activity,
                    )
                except Exception:
                    pass

                await asyncio.sleep(interval)

    except asyncio.CancelledError:
        pass

# ══════════════════════════════════════════════════════════════
#  Flet Notifications (Safe & Native SnackBar)
# ══════════════════════════════════════════════════════════════

def set_flet_page(page: ft.Page):
    global _flet_page
    _flet_page = page

def send_flet_notification(message: str):
    global _flet_page
    if _flet_page:
        try:
            _flet_page.open(
                ft.SnackBar(
                    content=ft.Text(message, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    duration=4000,
                )
            )
        except Exception:
            pass

# ══════════════════════════════════════════════════════════════
#  Android Background Mode (flet-android-notifications + Wakelock)
# ══════════════════════════════════════════════════════════════

_android_notifications = None
_wakelock = None
_flet_session_loop = None
_fgs_running = False

def _is_android() -> bool:
    return (
        hasattr(sys, 'getandroidapilevel')
        or 'ANDROID_ARGUMENT' in os.environ
        or os.environ.get('FLET_PLATFORM') == 'android'
    )

def _schedule_on_flet_loop(coro):
    loop = _flet_session_loop
    if loop is None or loop.is_closed():
        return None
    try:
        return asyncio.run_coroutine_threadsafe(coro, loop)
    except RuntimeError:
        return None

def ensure_background_mode(page: ft.Page):
    global _android_notifications, _wakelock, _flet_session_loop
    if not _is_android():
        return
    try:
        _flet_session_loop = asyncio.get_running_loop()
    except RuntimeError:
        _flet_session_loop = None

    if _android_notifications is None and FletAndroidNotifications is not None:
        _android_notifications = FletAndroidNotifications()
    if _wakelock is None:
        try:
            _wakelock = ft.Wakelock()
        except Exception as e:
            print(f"[Background] Wakelock unavailable: {e}")
            _wakelock = None

    if _client and not _client.is_closed():
        _schedule_on_flet_loop(_start_background_mode(str(_client.user) or 'FDSB Bot'))

async def start_android_foreground_service(bot_name: str):
    global _fgs_running

    if not _is_android():
        return

    notifications = _android_notifications
    if not notifications:
        print("[FGS] flet-android-notifications not registered")
        return

    title = bot_name or "FDSB Bot"
    body = "Bot is active and running in the background"

    try:
        await notifications.request_permissions()

        await notifications.start_foreground_service(
            notification_id=101,
            title=title,
            body=body,
            foreground_service_types=["special_use"],
            start_type="start_sticky", 
            ongoing=True, 
            show_when_locked=True,
            show_badge=True
        )
        _fgs_running = True
        print(f"[FGS] Foreground Service started/updated for {title}")
    except Exception as e:
        print(f"[FGS] start failed: {e}")


async def stop_android_foreground_service():
    global _fgs_running

    if not _is_android():
        return

    notifications = _android_notifications
    if not notifications:
        return

    try:
        await notifications.stop_foreground_service()
        _fgs_running = False
        print("[FGS] Foreground Service stopped")
    except Exception as e:
        print(f"[FGS] stop failed: {e}")

async def _enable_wakelock():
    w = _wakelock
    if w is None:
        return
    try:
        await w.enable()
    except Exception as e:
        print(f"[Wakelock] enable failed: {e}")

async def _disable_wakelock():
    w = _wakelock
    if w is None:
        return
    try:
        await w.disable()
    except Exception:
        pass

async def _start_background_mode(bot_name: str):
    await _enable_wakelock()
    await start_android_foreground_service(bot_name)

async def _stop_background_mode():
    await _disable_wakelock()
    await stop_android_foreground_service()

async def update_android_status_notification(bot_name: str, online: bool):
    if online:
        future = _schedule_on_flet_loop(_start_background_mode(bot_name))
    else:
        future = _schedule_on_flet_loop(_stop_background_mode())
    if future is not None:
        try:
            await future
        except Exception as e:
            print(f"[FGS] background mode error: {e}")

# ══════════════════════════════════════════════════════════════
# event_FDScripts
# ══════════════════════════════════════════════════════════════

def _make_bot(bot_dir: str):
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
        await asyncio.sleep(2)
        await update_android_status_notification(str(bot.user), online=True)

        global _status_task
        if _status_task is None or _status_task.done():
            _status_task = bot.loop.create_task(_status_rotator(bot, bot_dir))

        scripts = prefix_manager.get_event_scripts("$onBotOnline")
        if scripts:
            from main_exe.core_fdsb.event_FDScripts.onBotOnline import handle_event as handle_bot_online
            for script_text in scripts:
                try: await handle_bot_online(bot, script_text)
                except Exception: pass
    
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
        if message.type in _BOOST_MESSAGE_TYPES:
            scripts = prefix_manager.get_event_scripts("$onBoostServer")
            if scripts:
                from main_exe.core_fdsb.event_FDScripts.onBoostServer import handle_event
                for script_text in scripts:
                    try: await handle_event(message, bot, script_text)
                    except Exception: pass
            return

        if message.author.bot:
            try:
                from main_exe.core_fdsb.event_FDScripts.onBotMessage import handle_event as handle_bot_message
                await handle_bot_message(message, bot, prefix_manager._bot_events_dir)
            except Exception: pass
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

    _client = _make_bot(bot_root)
    _thread = threading.Thread(target=_runner, args=(token,))
    _thread.start()

    _schedule_on_flet_loop(_start_background_mode('FDSB Bot'))

    send_flet_notification("جاري تهيئة وتشغيل البوت...")
    return True

def stop_bot() -> None:
    global _stopping, _status_task
    if _stopping: return
    if _client is None or _client.is_closed(): return
    _stopping = True
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_client.close(), _loop)

    if _status_task and not _status_task.done():
        _status_task.cancel()
    _status_task = None

    send_flet_notification("تم إيقاف خدمة البوت.")

    _schedule_on_flet_loop(_stop_background_mode())

# ══════════════════════════════════════════════════════════════
#  Flet GUI & Android Background Permissions
# ══════════════════════════════════════════════════════════════

_permission_handler = None

async def request_flet_permissions(page: ft.Page):
    global _permission_handler
    if _permission_handler is None:
        _permission_handler = ft.PermissionHandler()
        page.overlay.append(_permission_handler)
        page.update()

    ph = _permission_handler

    try:
        notif_status = ph.check_permission(ft.PermissionType.NOTIFICATION)
        if notif_status != ft.PermissionStatus.GRANTED:
            ph.request_permission(ft.PermissionType.NOTIFICATION)
    except Exception as e:
        print(f"[Permissions] notification request failed: {e}")

    try:
        battery_status = ph.check_permission(ft.PermissionType.IGNORE_BATTERY_OPTIMIZATIONS)
        if battery_status != ft.PermissionStatus.GRANTED:
            ph.request_permission(ft.PermissionType.IGNORE_BATTERY_OPTIMIZATIONS)
    except Exception as e:
        print(f"[Permissions] battery optimization request failed: {e}")

def main_gui(page: ft.Page):
    global _flet_page
    _flet_page = page
    ensure_background_mode(page)
    
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    status_icon = ft.Icon(name=ft.Icons.DNS, size=60, color=ft.Colors.GREY)
    status_text = ft.Text(value="جاري التحميل...", size=16, weight=ft.FontWeight.BOLD)

    page.add(
        ft.Column(
            [status_icon, status_text],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

    async def launch_sequence():
        await request_flet_permissions(page)

        bot_directory = os.path.dirname(os.path.abspath(__file__))
        
        is_running = start_bot(bot_directory)

        if is_running:
            status_icon.color = ft.Colors.GREEN
        else:
            status_icon.color = ft.Colors.RED
            
        page.update()

    page.run_task(launch_sequence)

if __name__ == "__main__":
    ft.app(target=main_gui)