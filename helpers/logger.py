import logging


# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Không cần khai báo global logger ở đây vì logging.getLogger đã trả về singleton
logger = logging.getLogger(__name__)
