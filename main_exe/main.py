# Copyright (C) 2026 obgwew
# SPDX-License-Identifier: AGPL-3.0-or-later

# -*- coding: utf-8 -*-
# main_exe/main.py . migrated to Flet 0.85.2+ / v1 API 

import os
import json
import base64
import threading
import time

import flet as ft

from main_exe.settings import BotSettingsTab, get_current_lang
from main_exe.commands_view import BotCommandsTab
from main_exe.langs.translations import Translations
from main_exe.theme_engine import ThemeEngine
from main_exe.variables_view import BotVariablesTab
from main_exe.wiki_view import BotWikiTab

NEW_TXT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'main_exe/new.txt'
)


# ══════════════════════════════════════════════════════════════════════════════
#  Translation & Language helper
# ══════════════════════════════════════════════════════════════════════════════

def _t(key: str) -> str:
    return Translations.get(key, get_current_lang())

def _ar(text: str) -> str:
    return text

def _t_safe(key: str, fallback_en: str, fallback_ar: str = None) -> str:
    """Like _t(), but falls back to a hardcoded string instead of leaking
    a raw translation key when it isn't defined in the langs files yet."""
    try:
        val = Translations.get(key, get_current_lang())
    except Exception:
        val = None
    if val and val != key:
        return val
    if get_current_lang() == 'ar' and fallback_ar:
        return fallback_ar
    return fallback_en


def _run_bg(page: ft.Page, fn, *args):
    """Run fn(*args) off the UI thread so long calls (bot start/stop,
    network lookups) never freeze the interface."""
    runner = getattr(page, 'run_thread', None)
    if callable(runner):
        runner(fn, *args)
    else:
        threading.Thread(target=fn, args=args, daemon=True).start()

# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _c(key: str) -> str:
    return ThemeEngine.hex(key)


def _get_bot_id_from_token(token: str) -> str:
    try:
        part1   = token.split('.')[0]
        padding = 4 - len(part1) % 4
        if padding != 4:
            part1 += '=' * padding
        return base64.b64decode(part1).decode('utf-8')
    except Exception:
        return ''


def _read_new_txt() -> str:
    path = os.path.normpath(NEW_TXT_PATH)
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            return text if text else _t('no_updates')
        except Exception:
            return _t('read_error')
    return _t('no_file')


def _ink_btn(content: ft.Control, bgcolor: str, on_click,
             border_radius: int = 10, padding=None, width=None) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        border_radius=border_radius,
        padding=padding or ft.Padding(left=24, top=11, right=24, bottom=11),
        on_click=on_click,
        ink=True,
        width=width,
        alignment=ft.Alignment(0, 0),
        animate_opacity=150,
    )


def _soft_shadow(blur: int = 16, dy: int = 6, opacity: float = 0.10) -> ft.BoxShadow:
    return ft.BoxShadow(
        spread_radius=0,
        blur_radius=blur,
        color=ft.Colors.with_opacity(opacity, '#000000'),
        offset=ft.Offset(0, dy),
    )


def _card(content: ft.Control, bgcolor: str, border_color: str,
          radius: int = 14, padding=None, expand=False) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        border=ft.Border(
            left=ft.BorderSide(1, border_color), top=ft.BorderSide(1, border_color),
            right=ft.BorderSide(1, border_color), bottom=ft.BorderSide(1, border_color),
        ),
        border_radius=radius,
        padding=padding or ft.Padding(left=16, top=14, right=16, bottom=14),
        shadow=_soft_shadow(),
        expand=expand,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Tab definitions  –  label 
# ══════════════════════════════════════════════════════════════════════════════

_TABS = [
    ('main',      ft.Icons.HOME_ROUNDED,     'tab_main'),
    ('commands',  ft.Icons.CODE_ROUNDED,     'tab_commands'),
    ('variables', ft.Icons.TUNE_ROUNDED,     'tab_variables'),
    ('wiki',      ft.Icons.MENU_BOOK_ROUNDED, 'tab_wiki'),
    ('settings',  ft.Icons.SETTINGS_ROUNDED, 'tab_settings'),
]


# ══════════════════════════════════════════════════════════════════════════════
#  BotMainTab
# ══════════════════════════════════════════════════════════════════════════════

class BotMainTab:

    def __init__(self, page: ft.Page):
        self._page          = page
        self._server_online = False
        self._busy          = False
        self._bot_data      = {}

        self._avatar_ctrl = ft.Container(
            content=ft.Text(_t('avatar_none'), size=13, color=_c('text_dim'),
                            text_align=ft.TextAlign.CENTER),
            width=96, height=96,
            border_radius=48,
            bgcolor=_c('card_border'),
            alignment=ft.Alignment(0, 0),
            border=ft.Border(
                left=ft.BorderSide(3, _c('accent')), top=ft.BorderSide(3, _c('accent')),
                right=ft.BorderSide(3, _c('accent')), bottom=ft.BorderSide(3, _c('accent')),
            ),
            shadow=_soft_shadow(blur=18, dy=8, opacity=0.16),
        )

        self._name_text = ft.Text(
            '', size=18, weight=ft.FontWeight.BOLD,
            color=_c('text'), text_align=ft.TextAlign.CENTER,
        )

        self._invite_icon  = ft.Icon(ft.Icons.OPEN_IN_BROWSER, color='#FFFFFF', size=18)
        self._invite_label = ft.Text(_t('invite_bot'), color='#FFFFFF', size=14,
                                     weight=ft.FontWeight.W_500)
        self._invite_btn = _ink_btn(
            content=ft.Row([self._invite_icon, self._invite_label],
                           spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=_c('btn_invite'),
            on_click=self._invite_bot,
            width=210,
        )

        self._srv_dot = ft.Container(
            width=10, height=10, border_radius=5,
            bgcolor=_c('offline'),
        )
        self._srv_state = ft.Text(
            'Offline', size=12, color=_c('offline'), weight=ft.FontWeight.W_700,
        )
        self._srv_icon_wrap = ft.Container(
            content=ft.Icon(ft.Icons.DNS_ROUNDED, size=16, color=_c('text_dim')),
            width=28, height=28, border_radius=8,
            bgcolor=_c('bg'), alignment=ft.Alignment(0, 0),
        )
        self._srv_card = _card(
            content=ft.Column(
                [
                    ft.Row([self._srv_icon_wrap, self._srv_dot], spacing=6,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(_t_safe('status_bot_section', 'Server Status', 'حالة الخادم'),
                            size=11, color=_c('text_dim'), weight=ft.FontWeight.W_500),
                    self._srv_state,
                ],
                spacing=4,
            ),
            bgcolor=_c('card_bg'), border_color=_c('card_border'),
            radius=12, padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            expand=True,
        )

        # ── Guild-count chip (tap to refresh) ─────────────────────────────
        self._guild_count_text = ft.Text('—', size=15, color=_c('text'),
                                          weight=ft.FontWeight.BOLD)
        self._guild_refresh_icon = ft.Icon(ft.Icons.REFRESH_ROUNDED, size=15,
                                            color=_c('text_dim'))
        self._guild_icon_wrap = ft.Container(
            content=ft.Icon(ft.Icons.GROUPS_ROUNDED, size=16, color=_c('text_dim')),
            width=28, height=28, border_radius=8,
            bgcolor=_c('bg'), alignment=ft.Alignment(0, 0),
        )
        self._guild_card = _card(
            content=ft.Column(
                [
                    ft.Row([self._guild_icon_wrap, ft.Container(expand=True),
                            self._guild_refresh_icon],
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(_t_safe('servers_count', 'Servers', 'عدد السيرفرات'),
                            size=11, color=_c('text_dim'), weight=ft.FontWeight.W_500),
                    self._guild_count_text,
                ],
                spacing=4,
            ),
            bgcolor=_c('card_bg'), border_color=_c('card_border'),
            radius=12, padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            expand=True,
        )
        self._guild_card.on_click  = self._refresh_guild_count
        self._guild_card.ink       = True

        self._status_row = ft.Row(
            [self._srv_card, self._guild_card], spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── Start / Stop toggle ───────────────────────────────────────────
        self._toggle_icon      = ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color='#FFFFFF', size=20)
        self._toggle_icon_slot = ft.Container(content=self._toggle_icon,
                                               alignment=ft.Alignment(0, 0))
        self._toggle_label     = ft.Text(_t('start'), color='#FFFFFF', size=14,
                                         weight=ft.FontWeight.W_500)
        self._toggle_container = _ink_btn(
            content=ft.Row([self._toggle_icon_slot, self._toggle_label],
                           spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=_c('success'),
            on_click=self._toggle_server,
            width=220,
            padding=ft.Padding(left=20, top=13, right=20, bottom=13),
        )
        self._toggle_container.border_radius = 12
        self._toggle_container.shadow = _soft_shadow(blur=14, dy=5, opacity=0.18)

        self._news_text = ft.Text(_read_new_txt(), size=13, color=_c('text_dim'))

        ThemeEngine.subscribe(self._on_theme)
        
    async def _open_link(self, url: str):
        await self._page.launch_url(url)
    # ── Helpers ───────────────────────────────────────────────────────────────

    def _card_border(self) -> ft.Border:
        return ft.Border(
            left=ft.BorderSide(1, _c('card_border')),
            top=ft.BorderSide(1, _c('card_border')),
            right=ft.BorderSide(1, _c('card_border')),
            bottom=ft.BorderSide(1, _c('card_border')),
        )

    def _set_online_state(self, online: bool):
        self._server_online = online
        if online:
            self._srv_dot.bgcolor          = _c('online')
            self._srv_state.value          = _t_safe('online', 'Online', 'متصل')
            self._srv_state.color          = _c('online')
            self._toggle_icon.name         = ft.Icons.STOP_ROUNDED
            self._toggle_label.value       = _t('stop')
            self._toggle_container.bgcolor = _c('danger')
        else:
            self._srv_dot.bgcolor          = _c('offline')
            self._srv_state.value          = _t_safe('offline', 'Offline', 'غير متصل')
            self._srv_state.color          = _c('offline')
            self._toggle_icon.name         = ft.Icons.PLAY_ARROW_ROUNDED
            self._toggle_label.value       = _t('start')
            self._toggle_container.bgcolor = _c('success')
            self._guild_count_text.value   = '—'
        # restore the plain icon (a busy cycle may have swapped this slot
        # for a spinner) and make sure the button is interactive again
        self._toggle_icon_slot.content = self._toggle_icon
        self._toggle_container.disabled = False
        self._toggle_container.opacity  = 1.0

    # ── Real bot-client status helpers (talks to local_server's live client) ────

    @staticmethod
    def _bot_client():
        try:
            from main_exe.core_fdsb import local_server
            return local_server, getattr(local_server, '_client', None)
        except Exception:
            return None, None

    def _client_is_ready(self) -> bool:
        _, client = self._bot_client()
        if client is None:
            return False
        try:
            return (not client.is_closed()) and client.is_ready()
        except Exception:
            return False

    def _client_guild_count(self):
        _, client = self._bot_client()
        if client is None:
            return None
        try:
            if not client.is_closed():
                return len(client.guilds)
        except Exception:
            pass
        return None

    def _wait_until(self, predicate, timeout: float = 25.0, interval: float = 0.4) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return True
            time.sleep(interval)
        return predicate()

    # ── Start / stop busy handling ──────────────────────────────────────────────

    def _set_busy(self, going_online: bool):
        self._busy = True
        self._toggle_container.disabled = True
        self._toggle_container.opacity  = 0.55
        self._toggle_icon_slot.content  = ft.ProgressRing(
            width=16, height=16, stroke_width=2, color='#FFFFFF',
        )
        self._toggle_label.value = (
            _t_safe('starting', 'Starting…', 'جاري التشغيل…') if going_online
            else _t_safe('stopping', 'Stopping…', 'جاري الإيقاف…')
        )
        try:
            self._page.update()
        except Exception:
            pass

    def _toggle_server(self, _):
        if self._busy:
            return
        going_online = not self._server_online
        self._set_busy(going_online)

        def work():
            local_server, _client = self._bot_client()
            ok = local_server is not None

            if ok:
                try:
                    local_server.set_flet_page(self._page)
                    if going_online:
                        try:
                            if self._page.platform.value in ('android', 'ios'):
                                self._page.run_task(
                                    local_server.request_flet_permissions, self._page,
                                )
                        except (AttributeError, Exception):
                            pass
                        launched = local_server.start_bot(self._bot_data.get('bot_dir', ''))
                        # start_bot() only spins up the connection thread — the bot
                        # isn't actually online until on_ready fires, so wait for it.
                        ok = launched and self._wait_until(self._client_is_ready, timeout=25)
                    else:
                        local_server.stop_bot()
                        ok = self._wait_until(lambda: not self._client_is_ready(), timeout=15)
                except Exception as e:
                    print(f'[Dashboard] {"start" if going_online else "stop"} failed: {e}')
                    ok = False

            final_online = going_online if ok else self._server_online
            self._busy = False
            self._set_online_state(final_online)
            if final_online:
                self._fetch_guild_count(apply=True)
            try:
                self._page.update()
            except Exception:
                pass

        _run_bg(self._page, work)

    # ── Guild count ───────────────────────────────────────────────────────────

    def _fetch_guild_count(self, apply: bool = False):
        count = str(self._client_guild_count()) if self._client_is_ready() else '—'
        if apply:
            self._guild_count_text.value = count
        return count

    def _refresh_guild_count(self, _):
        if not self._server_online:
            return
        self._guild_count_text.value = '…'
        try:
            self._page.update()
        except Exception:
            pass

        def work():
            self._fetch_guild_count(apply=True)
            try:
                self._page.update()
            except Exception:
                pass

        _run_bg(self._page, work)

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _on_theme(self, data: dict):
        get = lambda k: data.get(k, '#888888')
        self._name_text.color        = get('text')
        self._news_text.color        = get('text_dim')
        self._invite_btn.bgcolor     = get('btn_invite')
        self._avatar_ctrl.border     = ft.Border(
            left=ft.BorderSide(3, get('accent')), top=ft.BorderSide(3, get('accent')),
            right=ft.BorderSide(3, get('accent')), bottom=ft.BorderSide(3, get('accent')),
        )
        for card, icon_wrap in ((self._srv_card, self._srv_icon_wrap),
                                 (self._guild_card, self._guild_icon_wrap)):
            card.bgcolor = get('card_bg')
            card.border  = ft.Border(
                left=ft.BorderSide(1, get('card_border')), top=ft.BorderSide(1, get('card_border')),
                right=ft.BorderSide(1, get('card_border')), bottom=ft.BorderSide(1, get('card_border')),
            )
            icon_wrap.bgcolor = get('bg')
        self._guild_count_text.color   = get('text')
        self._guild_refresh_icon.color = get('text_dim')
        self._set_online_state(self._server_online)
        self._page.update()

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        top_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self._avatar_ctrl], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self._name_text], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self._invite_btn], alignment=ft.MainAxisAlignment.CENTER),
                    self._status_row,
                    ft.Row([self._toggle_container], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=_c('divider')),
                    ft.Text(_t('whats_new'), size=15,
                            weight=ft.FontWeight.BOLD, color=_c('text')),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=ft.Padding(left=16, top=16, right=16, bottom=0),
        )

        news_card = _card(
            content=ft.Column([self._news_text], scroll=ft.ScrollMode.AUTO),
            bgcolor=_c('card_bg'), border_color=_c('card_border'),
            radius=12, padding=ft.Padding(left=16, top=12, right=16, bottom=12),
        )
        news_card.margin = ft.Margin(left=16, top=8, right=16, bottom=16)
        news_card.height = 260

        # The whole tab scrolls as one page instead of flex-squeezing the
        # news card to nothing when the content above it grows (extra
        # cards, longer bot name, small window, phone screen, etc.) — the
        # news text always gets its full, readable height.
        return ft.Column(
            [top_section, news_card],
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    # ── Logic ─────────────────────────────────────────────────────────────────

    def load_bot(self, bot_data: dict):
        self._bot_data        = bot_data
        self._name_text.value = bot_data.get('name', 'Bot')

        img_path = bot_data.get('image', '')
        if img_path and os.path.isfile(img_path):
            self._avatar_ctrl.content = ft.Image(
                src=img_path, width=96, height=96,
                fit=ft.BoxFit.COVER,
                border_radius=48,
            )
            self._avatar_ctrl.bgcolor = None
        else:
            self._avatar_ctrl.content = ft.Text(
                _t('avatar_none'), size=13, color=_c('text_dim'),
                text_align=ft.TextAlign.CENTER,
            )
            self._avatar_ctrl.bgcolor = _c('card_border')

        # local_server keeps one global client across tab rebuilds (e.g. a
        # theme switch recreates this tab) — reflect the real state instead
        # of assuming the bot is offline.
        is_online = self._client_is_ready()
        self._set_online_state(is_online)
        if is_online:
            self._fetch_guild_count(apply=True)
        self._news_text.value = _read_new_txt()

    async def _invite_bot(self, e):
        bot_id = _get_bot_id_from_token(self._bot_data.get('token', ''))
        if bot_id:
            url = f'https://discord.com/oauth2/authorize?client_id={bot_id}&permissions=8&scope=bot'
            
            await self._page.launch_url(url)


# ══════════════════════════════════════════════════════════════════════════════
#  BotDashboardScreen
# ══════════════════════════════════════════════════════════════════════════════

class BotDashboardScreen:
    def __init__(self, page: ft.Page, bot_dir: str = '', on_back=None):
        self._page    = page
        self._on_back = on_back
        self._active  = 'main'
        self._bot_dir = bot_dir

        self._title_text = ft.Text(
            '', size=16, weight=ft.FontWeight.BOLD,
            color=_c('text'), expand=True,
            text_align=ft.TextAlign.CENTER,
        )

        # ── main ───────────────────────
        self._back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            icon_color='#FFFFFF',
            bgcolor=_c('accent'),
            on_click=lambda _: self._on_back and self._on_back(),
            icon_size=16,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            visible=True,
        )

        self._main_tab      = BotMainTab(page)
        self._commands_tab  = BotCommandsTab(page)
        self._variables_tab = BotVariablesTab(page)
        self._settings_tab  = BotSettingsTab(
            page,
            on_lang_change=self._on_settings_lang_change,
            on_theme_change=self._on_settings_theme_change,
        )
        self._wiki_tab   = BotWikiTab(page)

        self._tab_views = {
            'main':      self._main_tab,
            'commands':  self._commands_tab,
            'variables': self._variables_tab,
            'settings':  self._settings_tab,
            'wiki':  self._wiki_tab,
        }

        self._tab_ids = [t[0] for t in _TABS]
        self._content = ft.Container(expand=True)
        self._nav_bar = self._build_nav()

        if bot_dir:
            self.load_bot(bot_dir)

        ThemeEngine.subscribe(self._on_theme)

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _on_theme(self, data: dict):
        get = lambda k: data.get(k, '#888888')
        self._title_text.color        = get('text')
        self._back_btn.bgcolor        = get('accent')
        self._nav_bar.bgcolor         = get('nav_bg')
        self._nav_bar.indicator_color = get('nav_active')
        if hasattr(self, '_header'):
            self._header.bgcolor      = get('card_bg')
            self._header.border       = ft.Border(bottom=ft.BorderSide(1, get('divider')))

        self._nav_bar.destinations = self._build_destinations()

        if hasattr(self, '_content'):
            self._content.content = self._tab_views[self._active].build()

    # ── Full tab recreation ────────────────────────────────────────────────────

    def _rebuild_all_tabs(self, update_nav: bool):
        self._main_tab      = BotMainTab(self._page)
        self._commands_tab  = BotCommandsTab(self._page)
        self._variables_tab = BotVariablesTab(self._page)
        self._settings_tab  = BotSettingsTab(
            self._page,
            on_lang_change=self._on_settings_lang_change,
            on_theme_change=self._on_settings_theme_change,
        )
        self._wiki_tab      = BotWikiTab(self._page)

        self._tab_views = {
            'main':      self._main_tab,
            'commands':  self._commands_tab,
            'variables': self._variables_tab,
            'settings':  self._settings_tab,
            'wiki':      self._wiki_tab,
        }

        if self._bot_dir:
            bot_files_dir = os.path.join(self._bot_dir, 'bot_files')
            config_path   = os.path.join(self._bot_dir, 'bot_files', 'config.json')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    bot_data = json.load(f)
                bot_data['bot_dir'] = self._bot_dir
            except Exception:
                bot_data = {}

            self._title_text.value = bot_data.get('name', 'Bot')
            self._main_tab.load_bot(bot_data)
            self._commands_tab.load_bot(bot_files_dir)
            self._variables_tab.load_bot(bot_files_dir)
            self._settings_tab.load_bot(bot_data)
            self._wiki_tab.load_bot(bot_data)

        if update_nav:
            self._nav_bar.destinations = self._build_destinations()
        self._content.content = self._tab_views[self._active].build()
        self._page.update()

    def _on_settings_lang_change(self, lang: str):
        self._rebuild_all_tabs(update_nav=True)

    def _on_settings_theme_change(self, theme_key: str):
        self._rebuild_all_tabs(update_nav=False)

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        self._header = ft.Container(
            content=ft.Row(
                [
                    self._back_btn,
                    self._title_text,
                    ft.Container(width=52),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor=_c('card_bg'),
            border=ft.Border(bottom=ft.BorderSide(1, _c('divider'))),
            padding=ft.Padding(left=14, top=10, right=14, bottom=10),
            height=52,
            shadow=_soft_shadow(blur=10, dy=2, opacity=0.06),
        )

        self._switch_tab('main')

        return ft.Column(
            [self._header, self._content, self._nav_bar],
            spacing=0,
            expand=True,
        )

    def _build_destinations(self) -> list:
        return [
            ft.NavigationBarDestination(
                icon=icon,
                label=_t(label_key),
            )
            for _, icon, label_key in _TABS
        ]

    def _build_nav(self) -> ft.NavigationBar:
        return ft.NavigationBar(
            selected_index=0,
            bgcolor=_c('nav_bg'),
            indicator_color=_c('nav_active'),
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            on_change=self._on_nav_change,
            destinations=self._build_destinations(),
        )

    # ── Navigation ────────────────────────────────────────────────────────────

    def _on_nav_change(self, e):
        target_id  = self._tab_ids[e.control.selected_index]
        leaving_id = self._active

        if target_id == leaving_id:
            return

        def _do_switch():
            self._switch_tab(target_id)

        def _stay_on_current_tab():
            self._nav_bar.selected_index = self._tab_ids.index(leaving_id)
            self._page.update()

        leaving_view = self._tab_views.get(leaving_id)
        guard = getattr(leaving_view, 'guard_tab_change', None)
        if callable(guard):
            guard(_do_switch, _stay_on_current_tab)
        else:
            _do_switch()

    def _switch_tab(self, tab_id: str):
        self._active                  = tab_id
        self._nav_bar.selected_index  = self._tab_ids.index(tab_id)
        self._content.content         = self._tab_views[tab_id].build()
        self._back_btn.visible        = (tab_id == 'main')
        self._page.update()

    # ── Data ──────────────────────────────────────────────────────────────────

    def load_bot(self, bot_dir: str):
        config_path = os.path.join(bot_dir, 'bot_files', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                bot_data = json.load(f)
            bot_data['bot_dir'] = bot_dir
        except Exception as e:
            print(f'[Dashboard] failed to read config.json: {e}')
            bot_data = {}

        self._title_text.value = bot_data.get('name', 'Bot')

        bot_files_dir = os.path.join(bot_dir, 'bot_files')
        self._main_tab.load_bot(bot_data)
        self._commands_tab.load_bot(bot_files_dir)
        self._variables_tab.load_bot(bot_files_dir)
        self._settings_tab.load_bot(bot_data)
        self._wiki_tab.load_bot(bot_data)
        self._switch_tab('main')