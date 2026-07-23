# Copyright (C) 2026 obgwew
# SPDX-License-Identifier: AGPL-3.0-or-later

# -*- coding: utf-8 -*-
# FDSB.py (root) . Flet 0.80+ / v1 API

import os
import re
import sys
import json
import shutil
import logging
import asyncio

import flet as ft

# ══════════════════════════════════════════════════════════════════════════════
#  PLATFORM DETECTION 
# ══════════════════════════════════════════════════════════════════════════════

def get_platform() -> str:
    env = os.getenv('FLET_PLATFORM', '').lower()
    if env in ('android', 'ios', 'windows', 'macos', 'linux', 'web'):
        return env
    if sys.platform.startswith('win'):
        return 'windows'
    if sys.platform.startswith('darwin'):
        return 'macos'
    if sys.platform.startswith('linux'):
        return 'linux'
    return 'unknown'


def is_mobile() -> bool:
    return get_platform() in ('android', 'ios')


def is_desktop() -> bool:
    return get_platform() in ('windows', 'macos', 'linux')


# ══════════════════════════════════════════════════════════════════════════════
#  WINDOW CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

def _configure_window(page: ft.Page):
    platform = get_platform()

    if platform == 'windows':
        page.window.width  = 1350
        page.window.height = 700

    elif platform in ('macos', 'linux'):
        page.window.width      = 420
        page.window.height     = 720
        page.window.min_width  = 360
        page.window.min_height = 600
        page.window.resizable  = False

    elif platform in ('android', 'ios'):
        page.padding = 0 

    elif platform == 'web':
        page.padding = 0

    else:
        page.window.width  = 420
        page.window.height = 720


# ══════════════════════════════════════════════════════════════════════════════
#  PERSISTENT STORAGE PATHS (writable — settings, bot configs, app_data/)
# ══════════════════════════════════════════════════════════════════════════════

def get_persistent_base_dir() -> str:
    storage_data = os.getenv('FLET_APP_STORAGE_DATA')
    if storage_data:
        return storage_data
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_app_data_dir() -> str:
    path = os.path.join(get_persistent_base_dir(), 'app_data')
    os.makedirs(path, exist_ok=True)
    return path

# ══════════════════════════════════════════════════════════════════════════════
#  BUNDLED RESOURCE PATHS (read-only — icons, fonts shipped inside the app)
# ══════════════════════════════════════════════════════════════════════════════

def get_resource_path(*parts: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


from main_exe.langs.translations import Translations
from main_exe.settings import get_current_lang, get_current_theme, apply_theme_globally
from main_exe.theme_engine import ThemeEngine
from main_exe.main import BotDashboardScreen

logging.getLogger('discord').setLevel(logging.INFO)

import main_exe.core_fdsb.local_server

icon_path = get_resource_path('main_exe', 'icons', 'FDSB.png')

# ══════════════════════════════════════════════════════════════════════════════
#  TRANSLATION HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _t(key: str) -> str:
    return Translations.get(key, get_current_lang())

def _ar(text: str) -> str:
    return text

# ══════════════════════════════════════════════════════════════════════════════
#  STORAGE
# ══════════════════════════════════════════════════════════════════════════════

APP_DATA_DIR = get_app_data_dir()


def ensure_app_data_dir():
    os.makedirs(APP_DATA_DIR, exist_ok=True)


def get_bot_dir(bot_name: str) -> str:
    safe = "".join(c for c in bot_name if c.isalnum() or c in (' ', '-', '_')).strip()
    return os.path.join(APP_DATA_DIR, safe.replace(' ', '_') or 'bot')


def save_bot_data(bot_data: dict) -> dict:
    ensure_app_data_dir()
    bot_dir       = get_bot_dir(bot_data.get('name', 'bot'))
    bot_files_dir = os.path.join(bot_dir, 'bot_files')
    os.makedirs(bot_dir,       exist_ok=True)
    os.makedirs(bot_files_dir, exist_ok=True)

    saved_image_path = ''
    original_image   = bot_data.get('image', '')
    if original_image and os.path.isfile(original_image):
        ext  = os.path.splitext(original_image)[1]
        dest = os.path.join(bot_dir, f'avatar{ext}')
        shutil.copy2(original_image, dest)
        saved_image_path = dest

    config = {
        'name':  bot_data.get('name', 'My Bot'),
        'token': bot_data.get('token', ''),
        'image': saved_image_path,
    }
    with open(os.path.join(bot_files_dir, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return config


def load_all_bots() -> list:
    ensure_app_data_dir()
    bots = []
    for entry in os.scandir(APP_DATA_DIR):
        if not entry.is_dir():
            continue
        config_path = os.path.join(entry.path, 'bot_files', 'config.json')
        if not os.path.isfile(config_path):
            continue
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if config.get('image') and not os.path.isfile(config['image']):
                config['image'] = ''
            bots.append(config)
        except Exception as e:
            print(f"[Storage] error {config_path}: {e}")
    return bots


def bot_exists(bot_name: str) -> bool:
    return os.path.isfile(
        os.path.join(get_bot_dir(bot_name), 'bot_files', 'config.json')
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TOKEN VALIDATOR
# ══════════════════════════════════════════════════════════════════════════════

DISCORD_TOKEN_RE = re.compile(
    r'^[A-Za-z0-9_-]{24,28}'   # Part 1
    r'\.'
    r'[A-Za-z0-9_-]{6}'        # Part 2
    r'\.'
    r'[A-Za-z0-9_-]{27,38}$'   # Part 3
)


def is_valid_discord_token(token: str) -> bool:
    if token == 'admin':
        return True
    return bool(DISCORD_TOKEN_RE.match(token))


# ══════════════════════════════════════════════════════════════════════════════
#  THEME
# ══════════════════════════════════════════════════════════════════════════════

THEME = {
    'bg':             '#FFFFFF',
    'card_bg':        '#C7D6FF',
    'card_border':    '#FFFFFF',
    'footer_bg':      '#A3CBFF',
    'popup_bg':       '#FFFFFF',
    'input_bg':       '#818181',
    'input_border':   '#797979',
    'text':           '#000000',
    'text_dim':       '#8A90A8',
    'text_on_accent': '#FFFFFF',
    'accent':         '#1B1F2E',
    'accent_hover':   '#2C3150',
    'success':        '#16A34A',
    'danger':         '#DC2626',
    'icon_bg':        '#8F8F8F',
    'discord':        '#5865F2',
    'github':         '#24292E',
    'title_bcfd':     '#1B1F2E',
}


def _c(key: str) -> str:
    return THEME[key]


# ══════════════════════════════════════════════════════════════════════════════
#  WARNING DIALOG
# ══════════════════════════════════════════════════════════════════════════════

def _show_warning(page: ft.Page, message: str):
    def _close(_):
        page.pop_dialog()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            '!',
            color=_c('danger'),
            size=28,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Text(
            message,
            color=_c('text'),
            text_align=ft.TextAlign.CENTER,
        ),
        actions=[
            ft.TextButton(
                content=ft.Text(_t('ok'), color=_c('danger')),
                on_click=_close,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        bgcolor=_c('popup_bg'),
        shape=ft.RoundedRectangleBorder(radius=16),
    )
    page.show_dialog(dlg)


# ══════════════════════════════════════════════════════════════════════════════
#  BOT CARD
# ══════════════════════════════════════════════════════════════════════════════

def build_bot_card(
    bot_data: dict,
    on_open_dashboard,
) -> ft.Container:

    img_path = bot_data.get('image', '')
    if img_path and os.path.isfile(img_path):
        avatar = ft.Image(
            src=img_path,
            width=42, height=42,
            fit=ft.BoxFit.COVER,
            border_radius=21,
        )
    else:
        avatar = ft.Container(
            content=ft.Text(_t('avatar_none'), size=11, color=_c('text_dim')),
            width=42, height=42,
            border_radius=21,
            bgcolor=_c('icon_bg'),
            alignment=ft.Alignment(0, 0),
        )

    name_lbl = ft.Text(
        bot_data.get('name', 'Bot'),
        size=14,
        weight=ft.FontWeight.BOLD,
        color=_c('text'),
    )

    go_btn = ft.IconButton(
        icon=ft.Icons.ARROW_FORWARD_ROUNDED,
        icon_color=_c('text_on_accent'),
        bgcolor=_c('accent'),
        icon_size=18,
        on_click=lambda _: on_open_dashboard(bot_data),
        tooltip='Open Dashboard',
        style=ft.ButtonStyle(shape=ft.CircleBorder()),
    )

    return ft.Container(
        content=ft.Row(
            [avatar, ft.Column([name_lbl], expand=True), go_btn],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        padding=ft.Padding(left=14, top=10, right=14, bottom=10),
        height=70,
        bgcolor=_c('card_bg'),
        border_radius=12,
        border=ft.Border(
            left=ft.BorderSide(1, _c('card_border')),
            top=ft.BorderSide(1, _c('card_border')),
            right=ft.BorderSide(1, _c('card_border')),
            bottom=ft.BorderSide(1, _c('card_border')),
        ),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE BOT DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class CreateBotDialog:

    def __init__(self, page: ft.Page, on_create: callable):
        self._page      = page
        self._on_create = on_create
        self._img_path  = ''

        self._avatar_stack = ft.Stack(
            [
                ft.Container(
                    content=ft.Text(
                        _t('image_label'),
                        size=12,
                        color=_c('text'),
                        text_align=ft.TextAlign.CENTER,
                    ),
                    width=80, height=80,
                    bgcolor=_c('icon_bg'),
                    border_radius=40,
                    alignment=ft.Alignment(0, 0),
                )
            ],
            width=80, height=80,
        )
        self._pick_btn = ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, color=_c('accent')),
                 ft.Text(_t('image_label'), color=_c('accent'))],
                spacing=4, tight=True,
            ),
            on_click=self._pick_image,
        )

        self._name_field = ft.TextField(
            label=_t('name_label') or 'Bot Name',
            hint_text=_t('name_hint') or 'My Awesome Bot',
            border_color=_c('input_border'),
            focused_border_color=_c('accent'),
            cursor_color=_c('accent'),
            bgcolor='#F5F5F5',
            border_radius=10,
            label_style=ft.TextStyle(color=_c('text'), size=13),
            text_style=ft.TextStyle(color=_c('text'), size=13),
        )
        self._token_field = ft.TextField(
            label=_t('token_label') or 'Bot Token',
            hint_text=_t('token_hint') or 'Paste your Discord token here',
            password=True,
            can_reveal_password=True,
            border_color=_c('input_border'),
            focused_border_color=_c('accent'),
            cursor_color=_c('accent'),
            bgcolor='#F5F5F5',
            border_radius=10,
            label_style=ft.TextStyle(color=_c('text'), size=13),
            text_style=ft.TextStyle(color=_c('text'), size=13),
        )

        self._file_picker = ft.FilePicker()

        self._dlg = ft.AlertDialog(
            modal=True,
            bgcolor=_c('popup_bg'),
            shape=ft.RoundedRectangleBorder(radius=18),
            title=ft.Text(
                _t('new_bot'),
                weight=ft.FontWeight.BOLD,
                color=_c('text'),
            ),
            content=ft.Column(
                [
                    ft.Row(
                        [self._avatar_stack, self._pick_btn],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                    ),
                    self._name_field,
                    self._token_field,
                ],
                tight=True,
                spacing=14,
                width=300,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text('Cancel', color=_c('text_dim')),
                    on_click=self._cancel,
                ),
                ft.FilledButton(
                    content=ft.Text(_t('make') or 'Create', color='#FFFFFF', weight=ft.FontWeight.W_600),
                    on_click=self._submit,
                    style=ft.ButtonStyle(
                        bgcolor=_c('accent'),
                        color='#FFFFFF',
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.Padding(left=20, top=10, right=20, bottom=10),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def open(self):
        self._page.show_dialog(self._dlg)

    async def _pick_image(self, _):
        files = await self._file_picker.pick_files(
            dialog_title='Choose Bot Image',
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        )
        if not files:
            return
        path = files[0].path
        if not path or not os.path.isfile(path):
            return

        self._img_path = path
        self._avatar_stack.controls.clear()
        self._avatar_stack.controls.append(
            ft.Container(
                content=ft.Image(
                    src=path,
                    width=80, height=80,
                    fit=ft.BoxFit.COVER,
                    border_radius=40,
                ),
                width=80, height=80,
                border_radius=40,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            )
        )
        self._page.update()

    def _submit(self, _):
        name  = self._name_field.value.strip() or 'My Bot'
        token = self._token_field.value.strip()

        # ── 1. التحقق من وجود التوكن ──────────────────────────────────
        if not token:
            self._token_field.error_text = _t('token_required')
            self._page.update()
            return

        if not is_valid_discord_token(token):
            self._token_field.error_text = (
                _t('token_invalid_format')
                or 'Invalid token format. Expected:\nXXXXXXXXXXXXXXXXXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
            )
            self._page.update()
            return

        self._token_field.error_text = None
        self._page.pop_dialog()
        self._on_create({'name': name, 'token': token, 'image': self._img_path})

    def _cancel(self, _):
        self._page.pop_dialog()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════

class MainView:

    def __init__(self, page: ft.Page, on_open_dashboard: callable):
        self._page              = page
        self._on_open_dashboard = on_open_dashboard

        self._cards_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        self._empty_label = ft.Container(
            content=ft.Text(
                _t('no_bots_hint'),
                size=14,
                color=_c('text_dim'),
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

        self._load_saved_bots()

    async def _open_link(self, url: str):
        await self._page.launch_url(url)

    # ── public ───────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        _t('main_title'),
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=_c('title_bcfd'),
                    ),
                ],
            ),
            padding=ft.Padding(left=18, top=10, right=18, bottom=10),
        )

        self._content_area = ft.Container(
            content=self._cards_col if self._cards_col.controls else self._empty_label,
            expand=True,
            padding=ft.Padding(left=16, top=8, right=16, bottom=8),
        )

        footer = ft.Container(
            content=ft.Row(
                [
                    ft.FilledButton(
                        content=ft.Row(
                            [ft.Icon(ft.Icons.TAG, color='#FFFFFF', size=16),
                             ft.Text(_t('discord'), color='#FFFFFF', size=13)],
                            spacing=5, tight=True,
                        ),
                        style=ft.ButtonStyle(
                            bgcolor=_c('discord'),
                            color='#FFFFFF',
                            shape=ft.RoundedRectangleBorder(radius=20),
                            padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                        ),
                        on_click=lambda _: self._page.run_task(self._open_link, 'https://discord.gg/JngaJRC6Y9'),
                    ),
                    ft.FilledButton(
                        content=ft.Row(
                            [ft.Icon(ft.Icons.CODE, color='#FFFFFF', size=16),
                             ft.Text(_t('github'), color='#FFFFFF', size=13)],
                            spacing=5, tight=True,
                        ),
                        style=ft.ButtonStyle(
                            bgcolor=_c('github'),
                            color='#FFFFFF',
                            shape=ft.RoundedRectangleBorder(radius=20),
                            padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                        ),
                        on_click=lambda _: self._page.run_task(self._open_link, 'https://github.com/obgwew/FDSB'),
                    ),
                    ft.Container(expand=True),
                    ft.FilledButton(
                        content=ft.Row(
                            [ft.Icon(ft.Icons.ADD, color='#FFFFFF', size=16),
                             ft.Text(_t('new_bot'), color='#FFFFFF', size=13)],
                            spacing=5, tight=True,
                        ),
                        style=ft.ButtonStyle(
                            bgcolor=_c('accent'),
                            color='#FFFFFF',
                            shape=ft.RoundedRectangleBorder(radius=20),
                            padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                        ),
                        on_click=self._open_create_dialog,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=_c('footer_bg'),
            padding=ft.Padding(left=14, top=11, right=14, bottom=11),
            height=62,
        )

        return ft.Column(
            [header, self._content_area, footer],
            spacing=0,
            expand=True,
        )

    # ── private ──────────────────────────────────────────────────────

    def _open_create_dialog(self, _):
        CreateBotDialog(self._page, on_create=self._add_bot).open()

    def _load_saved_bots(self):
        for bot_data in load_all_bots():
            self._push_card(bot_data)

    def _add_bot(self, data: dict):
        name = data.get('name', 'My Bot')
        if bot_exists(name):
            _show_warning(self._page, _t('name_taken'))
            return
        self._push_card(save_bot_data(data))
        self._refresh_content_area()
        self._page.update()

    def _push_card(self, bot_data: dict):
        card = build_bot_card(
            bot_data=bot_data,
            on_open_dashboard=self._on_open_dashboard,
        )
        self._cards_col.controls.append(card)

    def _refresh_content_area(self):
        if not hasattr(self, '_content_area'):
            return
        if self._cards_col.controls:
            self._content_area.content = self._cards_col
        else:
            self._content_area.content = self._empty_label

    def _start_bot(self, data):
        try:
            main_exe.core_fdsb.local_server.start_bot(data.get('bot_dir', ''))
        except Exception as e:
            print(f'[FDSB] start: {e}')

    def _stop_bot(self, data):
        try:
            main_exe.core_fdsb.local_server.stop_bot()
        except Exception as e:
            print(f'[FDSB] stop: {e}')


# ══════════════════════════════════════════════════════════════════════════════
#  NAVIGATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _show_main(page: ft.Page):
    page.clean()

    def open_dashboard(bot_data: dict):
        _show_dashboard(page, bot_data)

    view = MainView(page=page, on_open_dashboard=open_dashboard)

    if is_mobile():
        page.add(ft.SafeArea(content=view.build(), expand=True))
    else:
        page.add(view.build())

    page.update()
    

def _show_dashboard(page: ft.Page, bot_data: dict):
    bot_name  = bot_data.get('name', 'bot')
    safe_name = "".join(
        c for c in bot_name if c.isalnum() or c in (' ', '-', '_')
    ).strip().replace(' ', '_') or 'bot'

    bot_dir = os.path.join(get_app_data_dir(), safe_name)

    page.clean()

    dashboard = BotDashboardScreen(page=page, bot_dir=bot_dir, on_back=lambda: _show_main(page))

    if is_mobile():
        page.add(ft.SafeArea(content=dashboard.build(), expand=True))
    else:
        page.add(dashboard.build())

    page.update()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main(page: ft.Page):
    page.title   = 'FDSB'
    page.padding = 0

    if is_desktop():
        page.window.icon = icon_path

    _configure_window(page)

    fonts_dir = get_resource_path('main_exe', 'langs', 'fonts')
    fonts = {}
    if os.path.isdir(fonts_dir):
        for file in os.listdir(fonts_dir):
            if file.lower().endswith('.ttf'):
                name = os.path.splitext(file)[0]
                fonts[name] = os.path.join(fonts_dir, file)

    page.fonts = fonts if fonts else {
        "Cairo": "https://github.com/google/fonts/raw/main/ofl/cairo/Cairo-Regular.ttf"
    }
    default_font = next(iter(page.fonts), "Cairo")
    page.theme = ft.Theme(font_family=default_font)
    page.dark_theme = ft.Theme(font_family=default_font)

    saved_theme = get_current_theme()

    # امنع نظام أندرويد/iOS من فرض ColorScheme داكن افتراضي فوق
    # ثيماتنا المخصّصة يدوياً، وإلا فقد تظهر النصوص السوداء رمادية باهتة
    # عندما يكون "الوضع الداكن" مفعّلاً في إعدادات الهاتف.
    page.theme_mode = (
        ft.ThemeMode.DARK if saved_theme in ('system_da', 'v2_dark')
        else ft.ThemeMode.LIGHT
    )

    apply_theme_globally(saved_theme)

    def _sync_page_bg(data: dict):
        page.bgcolor = data.get('bg', '#FFFFFF')
        page.update()

    page._bg_sync = _sync_page_bg
    ThemeEngine.subscribe(page._bg_sync)
    page.bgcolor = ThemeEngine.hex('bg')

    _show_main(page)


if __name__ == '__main__':
    ft.run(main)