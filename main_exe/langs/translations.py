# -*- coding: utf-8 -*-
# main_exe/langs/translations.py

from .ar import ARABIC_DICT
from .en import ENGLISH_DICT
from .fr import FRENCH_DICT
from .de import GERMAN_DICT
from .ch import CHINESE_DICT
from .ru import RUSSIAN_DICT
from .tr import TURKISH_DICT
from .pl import POLISH_DICT


class Translations:
    show_debug_ids = False

    translations = {
        'ar': ARABIC_DICT,
        'en': ENGLISH_DICT,
        'fr': FRENCH_DICT,
        'de': GERMAN_DICT,
        'ch': CHINESE_DICT,
        'ru': RUSSIAN_DICT,
        'tr': TURKISH_DICT,
        'pl': POLISH_DICT,
    }

    @staticmethod
    def get(key: str, lang: str = 'en') -> str:
        val = Translations.translations.get(lang, {}).get(key, key)
        
        if isinstance(val, tuple) and len(val) == 2:
            num_id, text = val
            
            if Translations.show_debug_ids:
                return f"[{num_id}] {text}"
            
            return text
        
        return val

    @staticmethod
    def toggle_debug_ids():
        Translations.show_debug_ids = not Translations.show_debug_ids
