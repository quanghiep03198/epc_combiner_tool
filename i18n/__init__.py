import json
from helpers.configuration import ConfigService, ConfigSection
from enum import Enum
from events import UserActionEvent, __event_emitter__
from helpers.logger import logger

global __languages__


class Language(Enum):
    ENGLISH = "en"
    VIETNAMESE = "vi"
    CHINESE = "cn"


__languages__: list[dict] = [
    {"label": "Tiếng Việt", "value": Language.VIETNAMESE.value},
    {"label": "English", "value": Language.ENGLISH.value},
    {"label": "中文(简体)", "value": Language.CHINESE.value},
]


class I18nService:

    @staticmethod
    def on_language_change(lang: Language):
        try:
            ConfigService.set_conf(ConfigSection.LOCALE.value, "LANGUAGE", lang)
            logger.debug(f"Selected language :>>>> {lang}")
            global __dictionary__
            with open(file=f"./i18n/{lang}.json", mode="r", encoding="utf-8") as file:
                __dictionary__ = json.load(file)
        except FileNotFoundError as e:
            logger.error(e)
            __dictionary__ = {}

    @staticmethod
    def get_current_language() -> Language:
        curr_lang_conf = ConfigService.get_conf(
            ConfigSection.LOCALE.value, "LANGUAGE", Language.ENGLISH.value
        )
        lang = next(
            (lang for lang in __languages__ if lang["value"] == curr_lang_conf), None
        )

        logger.debug(lang)

        return lang

    @staticmethod
    def t(key, fallback=None):
        return __dictionary__.get(key, fallback)

    @staticmethod
    def emit():
        __event_emitter__.emit(UserActionEvent.LANGUAGE_CHANGE.value)
