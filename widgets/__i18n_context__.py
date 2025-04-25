from abc import abstractmethod


class I18nContext:

    @abstractmethod
    def __translate__(self):
        pass
