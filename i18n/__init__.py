from helpers.configuration import ConfigService, ConfigSection
from enum import Enum
from events import UserActionEvent, __event_emitter__
from helpers.logger import logger
from helpers.flatten_dict import flatten_dict

from i18n.cn import cn_dictionary
from i18n.en import en_dictionary
from i18n.vi import vi_dictionary


class Language(Enum):
    ENGLISH = "en"
    VIETNAMESE = "vi"
    CHINESE = "cn"


global __languages__
__languages__: list[dict] = [
    {"label": "中文(简体)", "value": Language.CHINESE.value},
    {"label": "English", "value": Language.ENGLISH.value},
    {"label": "Tiếng Việt", "value": Language.VIETNAMESE.value},
]

__i18n_resource__: dict[str, dict] = {
    Language.CHINESE.value: cn_dictionary,
    Language.ENGLISH.value: en_dictionary,
    Language.VIETNAMESE.value: vi_dictionary,
}


class I18nService:
    """Internationalization service"""

    @staticmethod
    def set_language(lang: Language) -> dict:
        """
        Change the current language or Get current dictionary with saved language

        Args:
        - lang: Language
        """
        try:
            ConfigService.set_conf(ConfigSection.LOCALE.value, "language", lang)
            global __dictionary__

            __dictionary__ = flatten_dict(__i18n_resource__[lang])
        except FileNotFoundError as e:
            logger.error(e)
            __dictionary__ = {}

    @staticmethod
    def get_i18n_context() -> Language:

        curr_lang_conf = ConfigService.get_conf(
            ConfigSection.LOCALE.value, "LANGUAGE", Language.ENGLISH.value
        )
        ctx = next(
            (lang for lang in __languages__ if lang["value"] == curr_lang_conf), None
        )

        return ctx

    @staticmethod
    def t(key, plurals=None, fallback=None):
        """
        Translate a key to the current language

        Args:
        - key: str
        - plurals: dict | None
        - fallback: str | None
        """
        if isinstance(plurals, dict):
            translated_text = __dictionary__.get(key, fallback)
            if translated_text and plurals:
                for k, v in plurals.items():
                    translated_text = translated_text.replace(f"{{{k}}}", str(v))
            return translated_text

        if fallback is None:
            return __dictionary__.get(key, key)

        return __dictionary__.get(key, fallback)

    @staticmethod
    def emit():
        """
        Emit an event to notify the language change
        """
        __event_emitter__.emit(UserActionEvent.LANGUAGE_CHANGE.value)
