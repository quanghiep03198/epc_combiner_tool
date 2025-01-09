global auth_context

auth_context = {
    "is_authenticated": False,
    "user_code": None,
    "employee_name": None,
    "employee_code": None,
    "factory_code": None,
    "factory_name": None,
}
"""
    Context for authentication state management.

    Scope: global

    Properties:
        - is_authenticated: bool
        - user_code: str | None
        - employee_name: str | None
        - employee_code: str | None
        - factory_code: str | None
        - factory_name: str | None
"""
