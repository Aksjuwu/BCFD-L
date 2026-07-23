# Copyright (C) 2026 obgwew
# SPDX-License-Identifier: AGPL-3.0-or-later

# -*- coding: utf-8 -*-
# main_exe/main.py . migrated to Flet 0.80+ / v1 API 

import os
import json
import base64

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
        self._bot_data      = {}

        self._avatar_ctrl = ft.Container(
            content=ft.Text(_t('avatar_none'), size=13, color=_c('text_dim'),
                            text_align=ft.TextAlign.CENTER),
            width=96, height=96,
            border_radius=48,
            bgcolor=_c('card_border'),
            alignment=ft.Alignment(0, 0),
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

        self._srv_dot   = ft.Container(
            width=12, height=12, border_radius=6,
            bgcolor='#E53935',
        )
        self._srv_state = ft.Text(
            'Offline', size=13,
            color='#E53935',
            weight=ft.FontWeight.W_700,
        )
        self._srv_card  = ft.Container(
            content=ft.Row(
                controls=[
                    self._srv_dot,
                    ft.Text(
                        'State Server',
                        size=13,
                        color='#2D3748',
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Container(expand=True),
                    self._srv_state,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            height=44,
            bgcolor='#EEF2F7',
            border_radius=10,
            padding=ft.Padding(left=14, top=0, right=14, bottom=0),
            border=ft.Border(
                left=ft.BorderSide(1, '#CBD5E0'),
                top=ft.BorderSide(1, '#CBD5E0'),
                right=ft.BorderSide(1, '#CBD5E0'),
                bottom=ft.BorderSide(1, '#CBD5E0'),
            ),
        )

        self._toggle_icon  = ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color='#FFFFFF', size=20)
        self._toggle_label = ft.Text(_t('start'), color='#FFFFFF', size=14,
                                     weight=ft.FontWeight.W_500)
        self._toggle_container = _ink_btn(
            content=ft.Row([self._toggle_icon, self._toggle_label],
                           spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=_c('success'),
            on_click=self._toggle_server,
            width=180,
            padding=ft.Padding(left=20, top=12, right=20, bottom=12),
        )

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
            self._srv_dot.bgcolor          = '#43A047'
            self._srv_state.value          = 'Online'
            self._srv_state.color          = '#43A047'
            self._toggle_icon.name         = ft.Icons.STOP_ROUNDED
            self._toggle_label.value       = _t('stop')
            self._toggle_container.bgcolor = _c('danger')
        else:
            self._srv_dot.bgcolor          = '#E53935'
            self._srv_state.value          = 'Offline'
            self._srv_state.color          = '#E53935'
            self._toggle_icon.name         = ft.Icons.PLAY_ARROW_ROUNDED
            self._toggle_label.value       = _t('start')
            self._toggle_container.bgcolor = _c('success')

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _on_theme(self, data: dict):
        get = lambda k: data.get(k, '#888888')
        self._name_text.color    = get('text')
        self._news_text.color    = get('text_dim')
        self._invite_btn.bgcolor = get('btn_invite')
        self._set_online_state(self._server_online)
        self._page.update()

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        server_card = self._srv_card

        top_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self._avatar_ctrl],
                           alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self._name_text],
                           alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self._invite_btn],
                           alignment=ft.MainAxisAlignment.CENTER),
                    server_card,
                    ft.Row([self._toggle_container],
                           alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=_c('divider')),
                    ft.Text(_t('whats_new'), size=15,
                            weight=ft.FontWeight.BOLD, color=_c('text')),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=ft.Padding(left=16, top=16, right=16, bottom=0),
        )

        news_card = ft.Container(
            content=ft.Column(
                [self._news_text],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            bgcolor=_c('card_bg'),
            border=self._card_border(),
            border_radius=12,
            padding=ft.Padding(left=16, top=12, right=16, bottom=12),
            expand=True,
            margin=ft.Margin(left=16, top=8, right=16, bottom=16),
        )

        return ft.Column(
            [top_section, news_card],
            spacing=0,
            expand=True,
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

        self._set_online_state(False)
        self._news_text.value = _read_new_txt()

    async def _invite_bot(self, e):
        bot_id = _get_bot_id_from_token(self._bot_data.get('token', ''))
        if bot_id:
            url = f'https://discord.com/oauth2/authorize?client_id={bot_id}&permissions=8&scope=bot'
            
            await self._page.launch_url(url)
 
    def _toggle_server(self, _):
        new_state = not self._server_online
        self._set_online_state(new_state)
        if new_state:
            try:
                from main_exe.core_fdsb import local_server
                try:
                    if self._page.platform.value in ('android', 'ios'):
                        local_server.request_flet_permissions(self._page)
                except (AttributeError, Exception):
                    pass
                local_server.start_bot(self._bot_data.get('bot_dir', ''))
            except Exception as e:
                print(f'[Dashboard] start failed: {e}')
                self._set_online_state(False)
        else:
            try:
                from main_exe.core_fdsb import local_server
                local_server.stop_bot()
            except Exception as e:
                print(f'[Dashboard] stop failed: {e}')
        self._page.update()


# ══════════════════════════════════════════════════════════════════════════════
#  BotDashboardScreen
# ══════════════════════════════════════════════════════════════════════════════

class BotDashboardScreen:
    def __init__(self, page: ft.Page, bot_dir: str = '', on_back=None):
        self._page    = page
        self._on_back = on_back
        self._active  = 'main'

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
        self._settings_tab  = BotSettingsTab(page)
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

        self._nav_bar.destinations = self._build_destinations()

        if hasattr(self, '_content'):
            self._content.content = self._tab_views[self._active].build()

        self._page.update()

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        header = ft.Container(
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
        )

        self._switch_tab('main')

        return ft.Column(
            [header, self._content, self._nav_bar],
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
        