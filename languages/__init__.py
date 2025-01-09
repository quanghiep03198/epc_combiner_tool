class I18nService:
    def __init__(self, language):
        self.language = language
        self.translations = {
            "en": {
                "hello": "Hello",
                "bye": "Goodbye",
            },
            "es": {
                "hello": "Hola",
                "bye": "Adiós",
            },
        }

    def t(self, word):
        return self.translations[self.language].get(word, "Not found")
