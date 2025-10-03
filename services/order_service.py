from repositories.order_repository import OrderRepository


class OrderService:
    @staticmethod
    def search_order(search: str) -> list[dict]:
        return OrderRepository.search_order(search)
