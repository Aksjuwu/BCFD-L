# Copyright (C) 2026 obgwew
# SPDX-License-Identifier: AGPL-3.0-or-later

# -*- coding: utf-8 -*-
# main_exe/wiki_view.py — Wiki tab (Flet 0.80+ / v1 API)
#

import os
import re
import json
import asyncio
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Callable

import flet as ft

from main_exe.theme_engine import ThemeEngine
from main_exe.settings import get_current_lang
from main_exe.langs.translations import Translations


def _c(key: str) -> str:
    return ThemeEngine.hex(key)


GITHUB_RAW_BASE = "https://raw.githubusercontent.com/obgwew/FDSB/main/wiki"

REQUEST_TIMEOUT = 10 

_BLOCK_TAG_RE  = re.compile(r'<block([^>]*)>(.*?)</block>', re.DOTALL | re.IGNORECASE)
_BLOCK_ATTR_RE = re.compile(r'(\w+)\s*=\s*"?([^"\s]+)"?')

_CALLOUT_STYLES: Dict[str, Tuple[str, str, str, str]] = {
    'note':      ('#3B82F6', 'EDIT_OUTLINED',                    'callout_note',        'Note'),
    'warning':   ('#F59E0B', 'WARNING_AMBER_ROUNDED',             'callout_limit',       'Limit'),
    'important': ('#EF4444', 'CLOSE_ROUNDED',                    'callout_important',   "It's important!"),
    'question':  ('#22C55E', 'QUESTION_MARK_ROUNDED',             'callout_question',   'What is this?'),
}
_CALLOUT_DEFAULT_ICON = 'INFO_OUTLINE_ROUNDED'

# ══════════════════════════════════════════════════════════════════════════════
#  Syntax Highlighting Constants
# ══════════════════════════════════════════════════════════════════════════════

try:
    from main_exe.core_fdsb.FDCore import KNOWN_COMMANDS
except ImportError:
    KNOWN_COMMANDS = set()

CONTROL_FLOW_COMMANDS = {
    "if", "elif", "else", "endif", "while", "endwhile", "for", "endfor",
    "break", "return", "and", "or", "onlyIf", "onlyAdmin", "log"
}

_HL_FONT_SIZE   = 13
_HL_FONT_FAMILY = 'Consolas'


def _t(key: str) -> str:
    return Translations.get(key, get_current_lang() or 'en')


@dataclass
class WikiParam:
    name: str
    type: str
    flag: str
    desc: str


@dataclass
class WikiDetails:
    syntax: str
    params:     List[WikiParam] = field(default_factory=list)
    examples:   List[str]       = field(default_factory=list)
    notes:      List[str]       = field(default_factory=list)
    warnings:   List[str]       = field(default_factory=list)
    importants: List[str]       = field(default_factory=list)
    questions:  List[str]       = field(default_factory=list)


@dataclass
class WikiDashBlock:
    type:    str = ''
    title:   str = ''
    kind:    str = ''
    items:   List[str]              = field(default_factory=list)
    options: List[Tuple[str, str]]  = field(default_factory=list)
    text:    str = ''
    image_id: str = ''
    caption:  str = ''


@dataclass
class WikiEntry:
    name:     str
    desc:     str
    category: str = ''
    details:  Optional[WikiDetails] = None
    blocks:   List[WikiDashBlock]   = field(default_factory=list)
    file_name: str = ''
    has_details: bool = False


class WikiParser:

    @staticmethod
    def _extract_block(text: str, tag: str) -> Optional[str]:
        open_tag, close_tag = f'<{tag}>', f'</{tag}>'
        start = text.find(open_tag)
        end   = text.find(close_tag)
        if start == -1 or end == -1 or end < start:
            return None
        return text[start + len(open_tag):end].strip('\n')

    @staticmethod
    def _strip_nested_blocks(text: str) -> str:
        return _BLOCK_TAG_RE.sub('', text)

    @staticmethod
    def _parse_dash(block: str) -> Optional[Dict[str, str]]:
        if block is None:
            return None
        data: Dict[str, str] = {}
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or ':' not in line:
                continue
            key, _, value = line.partition(':')
            data[key.strip().lower()] = value.strip()
        if not data.get('name') or not data.get('desc'):
            return None
        return data

    @staticmethod
    def _parse_dash_blocks(block: str) -> List[WikiDashBlock]:
        if not block:
            return []

        blocks: List[WikiDashBlock] = []
        for match in _BLOCK_TAG_RE.finditer(block):
            attrs_str, body = match.group(1), match.group(2)
            attrs = {k.lower(): v for k, v in _BLOCK_ATTR_RE.findall(attrs_str)}

            btype = attrs.get('type', '').strip().lower()
            if not btype:
                continue

            dash_block = WikiDashBlock(
                type=btype,
                title=attrs.get('title', '').strip(),
                kind=attrs.get('kind', '').strip().lower(),
            )

            for raw_line in body.splitlines():
                line = raw_line.strip()
                if not line or ':' not in line:
                    continue
                key, _, value = line.partition(':')
                key   = key.strip().lower()
                value = value.strip()

                try:
                    if key == 'item':
                        dash_block.items.append(value)
                    elif key == 'option':
                        parts = [p.strip() for p in value.split('|', 1)]
                        if len(parts) == 2 and parts[0]:
                            dash_block.options.append((parts[0], parts[1]))
                    elif key == 'text':
                        dash_block.text = (
                            f'{dash_block.text}\n{value}' if dash_block.text else value
                        )
                    elif key == 'id':
                        dash_block.image_id = value
                    elif key == 'caption':
                        dash_block.caption = value
                except Exception:
                    continue

            blocks.append(dash_block)

        return blocks

    @staticmethod
    def _parse_details(block: str) -> Optional[WikiDetails]:
        if block is None:
            return None

        syntax     = ''
        params:     List[WikiParam] = []
        examples:   List[str] = []
        notes:      List[str] = []
        warnings:   List[str] = []
        importants: List[str] = []
        questions:  List[str] = []

        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or ':' not in line:
                continue
            key, _, value = line.partition(':')
            key   = key.strip().lower()
            value = value.strip()

            try:
                if key == 'syntax':
                    syntax = value
                elif key == 'param':
                    parts = [p.strip() for p in value.split('|')]
                    if len(parts) < 4:
                        continue
                    params.append(WikiParam(name=parts[0], type=parts[1],
                                             flag=parts[2], desc=parts[3]))
                elif key == 'example':
                    examples.append(value)
                elif key == 'note':
                    notes.append(value)
                elif key == 'warning':
                    warnings.append(value)
                elif key == 'important':
                    importants.append(value)
                elif key == 'question':
                    questions.append(value)
            except Exception:
                continue

        if not syntax:
            return None

        return WikiDetails(syntax=syntax, params=params, examples=examples,
                            notes=notes, warnings=warnings,
                            importants=importants, questions=questions)

    @classmethod
    def parse(cls, text: str, file_name: str = '') -> Optional[WikiEntry]:
        try:
            dash_block = cls._extract_block(text, 'dash')
            if dash_block is None:
                return None

            dash_blocks = cls._parse_dash_blocks(dash_block)
            dash_data   = cls._parse_dash(cls._strip_nested_blocks(dash_block))
            if dash_data is None:
                return None

            details_block = cls._extract_block(text, 'details')
            details = cls._parse_details(details_block)

            return WikiEntry(
                name=dash_data['name'],
                desc=dash_data['desc'],
                category=dash_data.get('category', ''),
                details=details,
                blocks=dash_blocks,
                file_name=file_name,
            )
        except Exception:
            return None


class WikiCache:

    @staticmethod
    def _base_dir() -> str:
        android_storage = os.getenv('FLET_APP_STORAGE_DATA')
        if android_storage:
            path = os.path.join(android_storage, 'wiki_cache')
        elif os.name == 'nt':
            root = os.getenv('APPDATA') or os.path.expanduser('~')
            path = os.path.join(root, 'FDScriptDashboard', 'wiki_cache')
        else:
            root = os.getenv('XDG_DATA_HOME') or os.path.join(
                os.path.expanduser('~'), '.local', 'share')
            path = os.path.join(root, 'FDScriptDashboard', 'wiki_cache')
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def lang_dir(cls, lang: str) -> str:
        path = os.path.join(cls._base_dir(), lang)
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_local_version(cls, lang: str) -> int:
        path = os.path.join(cls.lang_dir(lang), 'version.json')
        if not os.path.isfile(path):
            return 0
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return int(json.load(f).get('version', 0))
        except Exception:
            return 0

    @classmethod
    def set_local_version(cls, lang: str, version: int):
        path = os.path.join(cls.lang_dir(lang), 'version.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'version': version}, f)

    @classmethod
    def save_index(cls, lang: str, files: List[str]):
        path = os.path.join(cls.lang_dir(lang), 'index.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(files, f, ensure_ascii=False)

    @classmethod
    def load_index(cls, lang: str) -> List[str]:
        path = os.path.join(cls.lang_dir(lang), 'index.json')
        if not os.path.isfile(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def save_function(cls, lang: str, file_name: str, text: str):
        folder = os.path.join(cls.lang_dir(lang), 'functions')
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, file_name), 'w', encoding='utf-8') as f:
            f.write(text)

        # Keep the lightweight meta index in sync as each file is saved,
        # instead of re-scanning/parsing the whole folder later.
        entry = WikiParser.parse(text, file_name)
        if entry is not None:
            cls._update_meta(lang, cls._entry_meta(entry))

    @classmethod
    def load_all_entries(cls, lang: str) -> List[WikiEntry]:
        """Full parse of every cached file. Kept for compatibility but no
        longer used by the UI on load — prefer load_light_entries()."""
        folder = os.path.join(cls.lang_dir(lang), 'functions')
        entries: List[WikiEntry] = []
        if not os.path.isdir(folder):
            return entries
        for file_name in sorted(os.listdir(folder)):
            path = os.path.join(folder, file_name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception:
                continue
            entry = WikiParser.parse(text, file_name)
            if entry is not None:
                entries.append(entry)
        return entries

    # ── Lazy loading (meta index + on-demand single file) ──────────────────

    @classmethod
    def _meta_path(cls, lang: str) -> str:
        return os.path.join(cls.lang_dir(lang), 'meta.json')

    @staticmethod
    def _entry_meta(entry: 'WikiEntry') -> Dict:
        return {
            'name':        entry.name,
            'desc':        entry.desc,
            'category':    entry.category,
            'file_name':   entry.file_name,
            'has_details': entry.details is not None,
        }

    @classmethod
    def _load_meta_raw(cls, lang: str) -> List[Dict]:
        path = cls._meta_path(lang)
        if not os.path.isfile(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def _save_meta_raw(cls, lang: str, items: List[Dict]):
        items = sorted(items, key=lambda m: m.get('file_name', ''))
        with open(cls._meta_path(lang), 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False)

    @classmethod
    def _update_meta(cls, lang: str, meta_item: Dict):
        items = cls._load_meta_raw(lang)
        items = [m for m in items if m.get('file_name') != meta_item.get('file_name')]
        items.append(meta_item)
        cls._save_meta_raw(lang, items)

    @classmethod
    def _rebuild_meta(cls, lang: str) -> List[Dict]:
        """One-time migration only (e.g. cache created by an older version
        without meta.json). Scans the folder once and persists the index so
        future loads never need to touch the files themselves."""
        folder = os.path.join(cls.lang_dir(lang), 'functions')
        items: List[Dict] = []
        if not os.path.isdir(folder):
            return items
        for file_name in sorted(os.listdir(folder)):
            path = os.path.join(folder, file_name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception:
                continue
            entry = WikiParser.parse(text, file_name)
            if entry is not None:
                items.append(cls._entry_meta(entry))
        if items:
            cls._save_meta_raw(lang, items)
        return items

    @classmethod
    def load_light_entries(cls, lang: str) -> List[WikiEntry]:
        """Loads only name/desc/category/has_details for every entry from
        the small meta.json index — never opens the whole functions folder
        at once. This is what powers the list view."""
        raw = cls._load_meta_raw(lang)
        if not raw:
            raw = cls._rebuild_meta(lang)

        entries: List[WikiEntry] = []
        for m in raw:
            entries.append(WikiEntry(
                name=m.get('name', ''),
                desc=m.get('desc', ''),
                category=m.get('category', ''),
                details=None,
                blocks=[],
                file_name=m.get('file_name', ''),
                has_details=bool(m.get('has_details', False)),
            ))
        entries.sort(key=lambda e: e.file_name)
        return entries

    @classmethod
    def load_entry_full(cls, lang: str, file_name: str) -> Optional['WikiEntry']:
        """Reads and parses a single wiki file on demand — called only when
        the user actually opens a card, not for the whole folder up-front."""
        if not file_name:
            return None
        path = os.path.join(cls.lang_dir(lang), 'functions', file_name)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception:
            return None
        return WikiParser.parse(text, file_name)


class WikiRemote:

    @staticmethod
    def _get(url: str) -> str:
        req = urllib.request.Request(url, headers={'User-Agent': 'FDScriptDashboard'})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.read().decode('utf-8')

    @classmethod
    def fetch_version(cls, lang: str) -> int:
        url = f'{GITHUB_RAW_BASE}/{lang}/version.json'
        data = json.loads(cls._get(url))
        return int(data.get('version', 0))

    @classmethod
    def fetch_index(cls, lang: str) -> List[str]:
        url = f'{GITHUB_RAW_BASE}/{lang}/index.json'
        return json.loads(cls._get(url))

    @classmethod
    def fetch_function(cls, lang: str, file_name: str) -> str:
        url = f'{GITHUB_RAW_BASE}/{lang}/functions/{file_name}'
        return cls._get(url)


def _ink_btn(content: ft.Control, bgcolor: str, on_click,
             border_radius: int = 10, padding=None, width=None,
             disabled: bool = False) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=bgcolor if not disabled else _c('card_border'),
        border_radius=border_radius,
        padding=padding or ft.Padding(left=18, top=10, right=18, bottom=10),
        on_click=None if disabled else on_click,
        ink=not disabled,
        width=width,
        alignment=ft.Alignment(0, 0),
        opacity=0.5 if disabled else 1.0,
    )


def _badge(text: str, bgcolor: str, color: str = '#FFFFFF') -> ft.Container:
    return ft.Container(
        content=ft.Text(text, size=11, color=color, weight=ft.FontWeight.W_600),
        bgcolor=bgcolor,
        border_radius=6,
        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
    )


def _tint(hex_color: str, opacity: int = 26) -> str:
    return f'#{opacity:02X}{hex_color.lstrip("#")}'


class BotWikiTab:
    def __init__(self, page: ft.Page, on_open_dashboard: Optional[Callable[[str], None]] = None):
        self._page              = page
        self._on_open_dashboard = on_open_dashboard

        self._lang    = get_current_lang() or 'en'
        self._entries: List[WikiEntry] = WikiCache.load_light_entries(self._lang)
        self._filtered: List[WikiEntry] = list(self._entries)

        self._view_mode  = 'list'
        self._current: Optional[WikiEntry] = None
        self._filter_type: Optional[str] = None

        self._busy = False

        # Colors are cached from the same theme snapshot commands_view.py
        # uses (populated in _on_theme), instead of calling ThemeEngine.hex()
        # fresh on every highlight pass — this guarantees the wiki code
        # blocks always match the command editor's colors exactly.
        self._hl_colors: Dict[str, str] = {}

        self._header_title = ft.Text(
            _t('tab_wiki'), size=15, weight=ft.FontWeight.BOLD, color=_c('text'),
        )

        self._search_field = ft.TextField(
            hint_text=_t('search_hint'),
            height=40,
            width=180,
            content_padding=ft.Padding(left=10, right=10, top=0, bottom=0),
            bgcolor=_c('card_bg'),
            border_color=_c('card_border'),
            border_radius=8,
            on_change=self._on_search_change,
        )

        self._update_btn = ft.FloatingActionButton(
            icon=ft.Icons.SYNC_ROUNDED,
            bgcolor=_c('accent'),
            foreground_color='#FFFFFF',
            mini=True,
            tooltip=_t('check_updates'),
            on_click=self._check_updates,
        )

        self._filter_all_btn = ft.Container(
            content=ft.Text(_t('filter_all'), size=11, color='#FFFFFF', weight=ft.FontWeight.W_600),
            bgcolor=_c('accent'),
            border_radius=6,
            padding=ft.Padding(left=10, top=4, right=10, bottom=4),
            on_click=lambda e: self._on_filter_change(None),
            ink=True,
        )
        self._filter_cmd_btn = ft.Container(
            content=ft.Text(_t('filter_command'), size=11, color=_c('text'), weight=ft.FontWeight.W_600),
            bgcolor=_c('card_border'),
            border_radius=6,
            padding=ft.Padding(left=10, top=4, right=10, bottom=4),
            on_click=lambda e: self._on_filter_change('command'),
            ink=True,
        )
        self._filter_event_btn = ft.Container(
            content=ft.Text(_t('filter_event'), size=11, color=_c('text'), weight=ft.FontWeight.W_600),
            bgcolor=_c('card_border'),
            border_radius=6,
            padding=ft.Padding(left=10, top=4, right=10, bottom=4),
            on_click=lambda e: self._on_filter_change('event'),
            ink=True,
        )
        self._filter_row = ft.Row(
            [self._filter_all_btn, self._filter_cmd_btn, self._filter_event_btn],
            spacing=6,
        )

        self._header = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [self._header_title, self._search_field],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._filter_row,
                ],
                spacing=4,
            ),
            padding=ft.Padding(left=12, right=12, top=6, bottom=6),
        )

        self._status_text = ft.Text(self._status_label(), size=12, color=_c('text_dim'))

        self._list_view = ft.ListView(expand=True, spacing=10, padding=ft.Padding(0, 0, 0, 16))

        self._list_root = ft.Column(
            [
                self._header,
                ft.Container(
                    content=ft.Stack(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [self._status_text, self._list_view],
                                    spacing=10,
                                    expand=True,
                                ),
                                padding=ft.Padding(left=12, right=12, top=8, bottom=70),
                                expand=True,
                            ),
                            ft.Container(
                                content=self._update_btn,
                                bottom=14,
                                right=14,
                            ),
                        ],
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        self._dash_back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            icon_color='#FFFFFF',
            bgcolor=_c('accent'),
            icon_size=16,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=self._back_to_list,
        )
        self._dash_title = ft.Text('', size=18, weight=ft.FontWeight.BOLD, color=_c('text'))
        self._dash_body  = ft.Column(spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)
        self._dash_root = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self._dash_back_btn, self._dash_title], spacing=10,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self._dash_body,
                ],
                spacing=14,
                expand=True,
            ),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            expand=True,
        )

        self._detail_back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            icon_color='#FFFFFF',
            bgcolor=_c('accent'),
            icon_size=16,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=self._back_to_list,
        )
        self._detail_title = ft.Text('', size=18, weight=ft.FontWeight.BOLD, color=_c('text'))
        self._detail_body   = ft.Column(spacing=14, scroll=ft.ScrollMode.AUTO, expand=True)
        self._detail_root = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self._detail_back_btn, self._detail_title], spacing=10,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self._detail_body,
                ],
                spacing=14,
                expand=True,
            ),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            expand=True,
        )

        self._root = ft.Container(expand=True)

        # Populate _hl_colors with sane fallbacks before the first theme
        # event arrives, so the very first render isn't left with an
        # empty dict (which would previously fall back silently).
        self._hl_colors = {
            'base':    '#2ECC71',
            'control': '#9B59B6',
            'known':   '#3498DB',
            'bracket': '#FC2323',
            'semi':    '#8A200D',
            'string':  '#FC2323',
            'comment': '#7F8C8D',
        }

        self._render()

        ThemeEngine.subscribe(self._on_theme)

    def _is_rtl(self) -> bool:
        # Overall interface layout stays LTR regardless of language;
        # only card content is mirrored to RTL when the language is Arabic.
        return (self._lang or '').lower().startswith('ar')

    def _status_label(self) -> str:
        v = WikiCache.get_local_version(self._lang)
        if v == 0 and not self._entries:
            return _t('no_cache')
        return _t('up_to_date').format(v=v)

    def _card_border(self) -> ft.Border:
        return ft.Border(
            left=ft.BorderSide(1, _c('card_border')),
            top=ft.BorderSide(1, _c('card_border')),
            right=ft.BorderSide(1, _c('card_border')),
            bottom=ft.BorderSide(1, _c('card_border')),
        )

    def _on_theme(self, data: dict):
        get = lambda k: data.get(k, '#888888')
        self._header_title.color        = get('text')
        self._search_field.bgcolor      = get('card_bg')
        self._search_field.border_color = get('card_border')
        self._status_text.color         = get('text_dim')
        self._update_btn.bgcolor           = get('accent')
        self._update_btn.foreground_color  = get('text_on_accent')
        self._dash_back_btn.bgcolor     = get('accent')
        self._dash_title.color          = get('text')
        self._detail_back_btn.bgcolor   = get('accent')
        self._detail_title.color        = get('text')

        # Same lookup/fallbacks commands_view.py uses for its own
        # _hl_colors, sourced from the exact same `data` snapshot — this
        # is what keeps the wiki's code highlighting pixel-identical to
        # the command editor's.
        self._hl_colors = {
            'base':    get('success'),
            'control': get('syntax_control_flow'),
            'known':   get('syntax_cmd'),
            'bracket': get('syntax_brackets'),
            'semi':    get('syntax_semicolon'),
            'string':  get('warning'),
            'comment': get('text_dim'),
        }

        self._update_filter_btns()
        self._render()
        self._page.update()

    def build(self) -> ft.Control:
        self._lang = get_current_lang() or 'en'
        self._render()
        return self._root

    def _render(self):
        if self._view_mode == 'list':
            self._root.content = self._list_root
        elif self._view_mode == 'dash':
            self._root.content = self._dash_root
        else:
            self._root.content = self._detail_root

    def _on_search_change(self, e):
        self._apply_filters()
        self._page.update()

    def _on_filter_change(self, filter_type: Optional[str]):
        self._filter_type = filter_type
        self._update_filter_btns()
        self._apply_filters()
        self._page.update()

    def _update_filter_btns(self):
        btns = [
            (self._filter_all_btn, None),
            (self._filter_cmd_btn, 'command'),
            (self._filter_event_btn, 'event'),
        ]
        for btn, ftype in btns:
            is_active = self._filter_type == ftype
            btn.bgcolor = _c('accent') if is_active else _c('card_border')
            btn.content.color = '#FFFFFF' if is_active else _c('text')

    def _apply_filters(self):
        query = (self._search_field.value or '').strip().lower()
        result = list(self._entries)

        if self._filter_type == 'event':
            result = [en for en in result if en.category.lower() == 'event']
        elif self._filter_type == 'command':
            result = [en for en in result if en.category.lower() != 'event']

        if query:
            result = [
                en for en in result
                if query in en.name.lower() or query in en.desc.lower()
            ]

        self._filtered = result
        self._rebuild_list()

    def _rebuild_list(self):
        self._list_view.controls.clear()

        if not self._filtered:
            self._list_view.controls.append(
                ft.Container(
                    content=ft.Text(_t('no_results'), color=_c('text_dim'), size=13,
                                     text_align=ft.TextAlign.CENTER),
                    padding=ft.Padding(0, 24, 0, 0),
                    alignment=ft.Alignment(0, 0),
                )
            )
            return

        for entry in self._filtered:
            self._list_view.controls.append(self._build_card(entry))

    def _build_card(self, entry: WikiEntry) -> ft.Container:
        has_details = entry.has_details

        header_children = [
            ft.Text(entry.name, size=15, weight=ft.FontWeight.BOLD, color=_c('text')),
        ]
        if entry.category:
            header_children.append(_badge(entry.category, _c('accent')))

        dash_btn = _ink_btn(
            content=ft.Row(
                [ft.Icon(ft.Icons.SPACE_DASHBOARD_ROUNDED, color='#FFFFFF', size=14),
                 ft.Text(_t('open_dashboard'), color='#FFFFFF', size=12,
                         weight=ft.FontWeight.W_500)],
                spacing=6, alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=_c('accent'),
            on_click=(lambda e, en=entry: self._open_dash(en)),
            disabled=False,
        )

        card_buttons = [dash_btn]

        if has_details:
            info_btn = _ink_btn(
                content=ft.Row(
                    [ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color='#FFFFFF', size=14),
                     ft.Text(_t('function_info'), color='#FFFFFF', size=12, weight=ft.FontWeight.W_500)],
                    spacing=6, alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=_c('accent'),
                on_click=(lambda e, en=entry: self._open_detail(en)),
                disabled=False,
            )
            card_buttons.append(info_btn)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(header_children, spacing=8),
                    ft.Text(entry.desc, size=13, color=_c('text_dim'), rtl=self._is_rtl()),
                    ft.Row(card_buttons, spacing=8, expand=True),
                ],
                spacing=8,
            ),
            bgcolor=_c('card_bg'),
            border=self._card_border(),
            border_radius=12,
            padding=ft.Padding(left=16, top=14, right=16, bottom=14),
            rtl=self._is_rtl(),
        )

    def _pill(self, text: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(text, size=12, color=_c('accent'),
                             font_family='monospace', weight=ft.FontWeight.W_600),
            bgcolor=_tint(_c('accent'), 24),
            border_radius=6,
            padding=ft.Padding(left=10, top=4, right=10, bottom=4),
        )

    def _rich_paragraph(self, text: str, size: int = 14, color: Optional[str] = None) -> ft.Text:
        color = color or _c('text')
        spans: List[ft.TextSpan] = []
        parts = (text or '').split('`')
        for i, part in enumerate(parts):
            if not part:
                continue
            if i % 2 == 1:
                spans.append(ft.TextSpan(
                    part,
                    style=ft.TextStyle(font_family='monospace', color=_c('accent'),
                                        bgcolor=_tint(_c('accent'), 22), size=size),
                ))
            else:
                spans.append(ft.TextSpan(part, style=ft.TextStyle(color=color, size=size)))
        if not spans:
            spans = [ft.TextSpan(text or '', style=ft.TextStyle(color=color, size=size))]
        return ft.Text(spans=spans, size=size, rtl=self._is_rtl())

    def _callout_style(self, kind: str) -> Tuple[str, str, str]:
        color, icon_name, key, fallback = _CALLOUT_STYLES.get(
            kind, ('#3B82F6', _CALLOUT_DEFAULT_ICON, 'callout_note', 'Info'))
        icon = getattr(ft.Icons, icon_name, ft.Icons.INFO_OUTLINE_ROUNDED)
        label = _t(key) or fallback
        return color, icon, label

    def _callout(self, title: str, text: str, color: str, icon) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [ft.Icon(icon, color=color, size=18),
                         ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=color)],
                        spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(text, size=13, color=_c('text'), rtl=self._is_rtl()),
                ],
                spacing=6,
            ),
            bgcolor=_tint(color, 24),
            border=ft.Border(left=ft.BorderSide(4, color)),
            border_radius=10,
            padding=ft.Padding(12, 10, 12, 10),
            rtl=self._is_rtl(),
        )

    # ── Highlighting Logic ───────────────────────────────────────────────────

    def _highlight_code(self, text: str) -> List[ft.TextSpan]:
        known_cmds = set(KNOWN_COMMANDS) if KNOWN_COMMANDS else set()
        control_flow_escaped = '|'.join(sorted(CONTROL_FLOW_COMMANDS, key=len, reverse=True))
        known_escaped = '|'.join(sorted(known_cmds - CONTROL_FLOW_COMMANDS, key=len, reverse=True))

        control_part = rf'\$(?:{control_flow_escaped})\b' if control_flow_escaped else r'(?!x)x'
        known_part   = rf'\$(?:{known_escaped})\b'        if known_escaped        else r'(?!x)x'

        master_pattern = (
            r'(?P<comment>#.*)'
            r'|(?P<string>".*?"|\'.*?\')'
            rf'|(?P<control>{control_part})'
            rf'|(?P<known>{known_part})'
            r'|(?P<token>\$\w*)'
            r'|(?P<punct>[\[\];])'
            r'|(?P<text>[^#"\'$\[\];]+)'
        )

        # Sourced from self._hl_colors (refreshed in _on_theme), so this is
        # guaranteed to be the same dict commands_view.py builds for the
        # command editor — no more drift between the two views.
        colors = self._hl_colors
        base_color = colors.get('base', '#2ECC71')

        def _span(value: str, color: str) -> ft.TextSpan:
            return ft.TextSpan(
                value,
                ft.TextStyle(
                    color=color,
                    size=_HL_FONT_SIZE,
                    font_family=_HL_FONT_FAMILY,
                ),
            )

        spans = []
        for match in re.finditer(master_pattern, text):
            value = match.group()
            group = match.lastgroup

            if group == 'comment': spans.append(_span(value, colors.get('comment', base_color)))
            elif group == 'string': spans.append(_span(value, colors.get('string', base_color)))
            elif group == 'control': spans.append(_span(value, colors.get('control', base_color)))
            elif group == 'known': spans.append(_span(value, colors.get('known', base_color)))
            elif group == 'punct':
                b_color = colors.get('semi', base_color) if value == ';' else colors.get('bracket', base_color)
                spans.append(_span(value, b_color))
            else: spans.append(_span(value, base_color))

        return spans

    def _code_box(self, text: str, with_copy: bool = False) -> ft.Control:
        box = ft.Container(
            content=ft.Text(spans=self._highlight_code(text), selectable=True),
            bgcolor='#0D1117',
            border_radius=10,
            padding=ft.Padding(14, 12, 14, 12),
        )
        
        if not with_copy:
            return box
            
        return ft.Row(
            [
                ft.Container(box, expand=True),
                ft.IconButton(
                    icon=ft.Icons.COPY_ROUNDED, icon_color=_c('text_dim'), icon_size=18,
                    tooltip=_t('copy_syntax'),
                    # IMPORTANT: on_click must be the async function itself,
                    # not a sync lambda that merely *calls* it. Flet decides
                    # whether to `await` a handler by checking
                    # inspect.iscoroutinefunction(handler) on whatever is
                    # assigned to on_click. A `lambda e: self._copy_syntax(e)`
                    # is itself a plain sync function — calling it just
                    # creates (and immediately drops) a coroutine object
                    # without ever running a single line inside it. Using a
                    # small async closure factory keeps on_click a real
                    # coroutine function while still capturing `text`.
                    on_click=self._make_copy_handler(text),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _show_snack(self, snack: ft.SnackBar):
        """Show a SnackBar in a way that's compatible across Flet versions.
        Newer Flet (>=0.24-ish) exposes `Page.open(control)`.
        Some builds bundled with serious_python don't have it, so we
        fall back to the classic `page.snack_bar = ...; open = True`.
        """
        page = self._page
        opener = getattr(page, 'open', None)
        if callable(opener):
            try:
                opener(snack)
                return
            except Exception as ex:
                print(f'[Wiki] page.open(snack_bar) failed, falling back: {ex}')
        # Fallback for Flet builds without Page.open
        page.snack_bar = snack
        snack.open = True
        page.update()

    def _make_copy_handler(self, text: str) -> Callable:
        async def _handler(e):
            await self._copy_syntax(e, text)
        return _handler

    async def _copy_syntax(self, e, text: str):
        # `Page.set_clipboard` was deprecated in Flet 0.80.0 and no longer
        # exists as of this build (0.85.x) — confirmed via:
        #   AttributeError: type object 'Page' has no attribute
        #   'set_clipboard'. Did you mean: 'clipboard'?
        # The current API is the standalone Clipboard *service*:
        #   await ft.Clipboard().set(text)
        # https://docs.flet.dev/services/clipboard/
        ok = False
        try:
            await ft.Clipboard().set(text)
            ok = True
        except Exception as ex:
            print(f'[Wiki] clipboard copy failed: {ex}')

        if ok:
            print(f'[Wiki] copied to clipboard OK ({len(text)} chars)')
            self._show_snack(ft.SnackBar(content=ft.Text(_t('copied')), duration=1400))
        else:
            self._show_snack(ft.SnackBar(
                content=ft.Text(_t('copy_failed') or 'فشل النسخ — راجع الطرفية'),
                duration=2200,
            ))

    def _render_dash_block(self, block: WikiDashBlock) -> ft.Control:
        if block.type == 'toc':
            chips: List[ft.Control] = []
            for i, item in enumerate(block.items):
                if i > 0:
                    chips.append(ft.Text('>', size=13, color=_c('text_dim')))
                chips.append(ft.Text(item, size=13, color=_c('accent'), weight=ft.FontWeight.W_600))
            col: List[ft.Control] = []
            if block.title:
                col.append(ft.Text(block.title, size=15, weight=ft.FontWeight.BOLD, color=_c('text')))
            col.append(ft.Row(chips, wrap=True, spacing=8, run_spacing=8))
            return ft.Column(col, spacing=10)

        if block.type == 'list':
            col = []
            if block.title:
                col.append(ft.Text(block.title, size=15, weight=ft.FontWeight.BOLD, color=_c('text')))
            for item in block.items:
                col.append(ft.Row([ft.Text('•', color=_c('text_dim')), self._pill(item)], spacing=8))
            return ft.Column(col, spacing=8)

        if block.type == 'options':
            col = []
            if block.title:
                col.append(ft.Text(block.title, size=15, weight=ft.FontWeight.BOLD, color=_c('text')))
            for label, desc in block.options:
                col.append(
                    ft.Row(
                        [self._pill(label), ft.Text(f'- {desc}', size=13, color=_c('text_dim'))],
                        spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )
            return ft.Column(col, spacing=10)

        if block.type == 'text':
            col = []
            if block.title:
                col.append(ft.Text(block.title, size=15, weight=ft.FontWeight.BOLD, color=_c('text')))
            col.append(self._rich_paragraph(block.text))
            return ft.Column(col, spacing=8)

        if block.type == 'code':
            col = []
            if block.title:
                col.append(ft.Text(block.title, size=15, weight=ft.FontWeight.BOLD, color=_c('text')))
            col.append(self._code_box(block.text, with_copy=True))
            return ft.Column(col, spacing=10)

        if block.type == 'callout':
            color, icon, label = self._callout_style(block.kind)
            return self._callout(label, block.text, color, icon)

        if block.type == 'image':
            col = []
            if block.title:
                col.append(ft.Text(block.title, size=15, weight=ft.FontWeight.BOLD, color=_c('text')))
            
            if block.image_id:
                img_name = block.image_id if "." in block.image_id else f"{block.image_id}.png"
                img_src = f"exm_img/{img_name}"

                img_control = ft.Image(
                    src=img_src,
                    border_radius=8,
                    fit=ft.ImageFit.CONTAIN,
                )
                col.append(ft.Container(content=img_control, alignment=ft.Alignment(0, 0)))

            if block.caption:
                col.append(ft.Text(block.caption, size=12, color=_c('text_dim'), text_align=ft.TextAlign.CENTER))

            return ft.Column(col, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Container(height=0)

    def _open_dash(self, entry: WikiEntry):
        # Only the single selected file is read/parsed here, on demand.
        full_entry = WikiCache.load_entry_full(self._lang, entry.file_name) or entry

        self._current   = full_entry
        self._view_mode = 'dash'
        self._dash_title.value = full_entry.name

        controls: List[ft.Control] = []
        if full_entry.category:
            controls.append(
                ft.Row([_badge(full_entry.category, _c('accent'))],
                       alignment=ft.MainAxisAlignment.START)
            )
        if full_entry.desc:
            controls.append(self._rich_paragraph(full_entry.desc, size=14))

        for block in full_entry.blocks:
            controls.append(self._render_dash_block(block))

        self._dash_body = ft.Column(controls, spacing=18, scroll=ft.ScrollMode.AUTO,
                                     expand=True, rtl=self._is_rtl())
        self._dash_root.content.controls[1] = self._dash_body

        self._render()
        self._page.update()

    def _open_detail(self, entry: WikiEntry):
        # Only the single selected file is read/parsed here, on demand.
        full_entry = WikiCache.load_entry_full(self._lang, entry.file_name)
        if full_entry is None or full_entry.details is None:
            return
        self._current   = full_entry
        self._view_mode = 'detail'
        self._detail_title.value = f'${full_entry.name}'
        self._build_detail_body(full_entry)
        self._render()
        self._page.update()

    def _back_to_list(self, _):
        self._view_mode = 'list'
        self._current    = None
        self._render()
        self._page.update()

    def _build_detail_body(self, entry: WikiEntry):
        details: WikiDetails = entry.details

        controls: List[ft.Control] = []

        controls.append(ft.Text(entry.desc, size=13, color=_c('text_dim')))

        controls.append(ft.Text(_t('syntax'), size=14, weight=ft.FontWeight.BOLD, color=_c('text')))
        controls.append(self._code_box(details.syntax, with_copy=True))

        if details.params:
            controls.append(ft.Text(_t('parameters'), size=14, weight=ft.FontWeight.BOLD,
                                     color=_c('text')))
            _FLAG_REQUIRED  = '#EF4444'
            _FLAG_OPTIONAL  = '#3B82F6'
            _FLAG_EMPTIABLE = '#8B5CF6'
            
            for p in details.params:
                flag_lower = p.flag.lower()
                if flag_lower.startswith('req'):
                    flag_color = _FLAG_REQUIRED
                elif flag_lower.startswith('empt'):
                    flag_color = _FLAG_EMPTIABLE
                else:
                    flag_color = _FLAG_OPTIONAL
                    
                controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [ft.Text(p.name, size=13, weight=ft.FontWeight.W_600,
                                             color=_c('text')),
                                     _badge(p.type, '#6366F1'),
                                     _badge(p.flag, flag_color)],
                                    spacing=6,
                                ),
                                ft.Text(p.desc, size=12, color=_c('text_dim'), rtl=self._is_rtl()),
                            ],
                            spacing=4,
                        ),
                        bgcolor=_c('card_bg'),
                        border=self._card_border(),
                        border_radius=8,
                        padding=ft.Padding(10, 8, 10, 8),
                        rtl=self._is_rtl(),
                    )
                )

        if details.examples:
            controls.append(ft.Text(_t('example'), size=14, weight=ft.FontWeight.BOLD,
                                     color=_c('text')))
            for ex in details.examples:
                controls.append(self._code_box(ex, with_copy=True))

        for note in details.notes:
            color, icon, label = self._callout_style('note')
            controls.append(self._callout(label, note, color, icon))

        for warn in details.warnings:
            color, icon, label = self._callout_style('warning')
            controls.append(self._callout(label, warn, color, icon))

        for imp in details.importants:
            color, icon, label = self._callout_style('important')
            controls.append(self._callout(label, imp, color, icon))

        for q in details.questions:
            color, icon, label = self._callout_style('question')
            controls.append(self._callout(label, q, color, icon))

        self._detail_body = ft.Column(controls, spacing=14, scroll=ft.ScrollMode.AUTO,
                                       expand=True, rtl=self._is_rtl())
        self._detail_root.content.controls[1] = self._detail_body

    def _set_busy(self, busy: bool, label: str = ''):
        self._busy = busy
        self._update_btn.opacity = 0.6 if busy else 1.0
        if label:
            self._status_text.value = label
        self._page.update()

    async def _check_updates(self, e):
        if self._busy:
            return
        self._set_busy(True, _t('checking'))

        loop = asyncio.get_event_loop()
        lang = self._lang

        try:
            remote_version = await loop.run_in_executor(None, WikiRemote.fetch_version, lang)
        except Exception:
            self._set_busy(False, _t('update_failed'))
            return

        local_version = WikiCache.get_local_version(lang)

        if remote_version <= local_version:
            self._set_busy(False, _t('up_to_date').format(v=local_version))
            return

        from main_exe.load.loading_view import LoadingScreen

        loader = LoadingScreen(container=self._root, page=self._page, title=_t('downloading'))

        async def _do_download(screen: LoadingScreen):
            index = await loop.run_in_executor(None, WikiRemote.fetch_index, lang)
            index.sort()

            total = len(index) or 1
            done_count = 0
            screen.set_progress(0.0, f'0/{total}')

            async def _fetch_one(file_name: str):
                nonlocal done_count
                text = await loop.run_in_executor(None, WikiRemote.fetch_function, lang, file_name)
                WikiCache.save_function(lang, file_name, text)
                done_count += 1
                screen.set_progress(done_count / total, f'{done_count}/{total}')

            chunk_size = 5
            for i in range(0, len(index), chunk_size):
                chunk = index[i:i + chunk_size]

                await asyncio.gather(*[_fetch_one(fn) for fn in chunk])

                await asyncio.sleep(20)

            WikiCache.save_index(lang, index)
            WikiCache.set_local_version(lang, remote_version)

        try:
            await loader.run(
                _do_download,
                done_message=_t('up_to_date').format(v=remote_version),
                extra_hold_max=5.0,
            )
        except Exception:
            self._set_busy(False, _t('update_failed'))
            return

        self._entries  = WikiCache.load_light_entries(lang)
        self._filtered = list(self._entries)
        self._filter_type = None
        self._update_filter_btns()
        self._apply_filters()
        self._render()

        self._set_busy(False, _t('up_to_date').format(v=remote_version))

        self._show_snack(ft.SnackBar(
            content=ft.Text(_t('up_to_date').format(v=remote_version)),
            duration=2500,
        ))
            
    def load_bot(self, *_args, **_kwargs):
        self._lang    = get_current_lang() or 'en'
        self._entries = WikiCache.load_light_entries(self._lang)
        self._filter_type = None
        self._filtered = list(self._entries)
        self._status_text.value = self._status_label()
        self._update_filter_btns()
        self._apply_filters()