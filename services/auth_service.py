from repositories.auth_repository import AuthRepository
from helpers.logger import logger
from constants import StatusCode
from i18n import I18nService


class AuthService:
    @staticmethod
    def login(username: str, password: str):
        try:
            user: dict[str, str] = AuthRepository.find_user(username)
            if all(value is None for value in user.values()):
                raise Exception(
                    {
                        "message": I18nService.t("notification.user_not_found"),
                        "status": StatusCode.UNAUTHORIZED.value,
                    }
                )
            if user.get("password") != password:
                raise Exception(
                    {
                        "message": I18nService.t("notification.incorrect_password"),
                        "status": StatusCode.UNAUTHORIZED.value,
                    }
                )

            factories = AuthRepository.get_factories(user["id"])
            return {"user": user, "factories": factories}
        except Exception as e:
            if isinstance(e.args[0], dict) and "status" in e.args[0]:
                e.status = e.args[0]["status"]
                if e.status == StatusCode.UNAUTHORIZED.value:
                    raise Exception(e.args[0])
