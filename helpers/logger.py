import logging
import os


# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Không cần khai báo global logger ở đây vì logging.getLogger đã trả về singleton
logger = logging.getLogger(__name__)


# Tạo thư mục logs nếu chưa tồn tại
log_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs"
)
os.makedirs(log_dir, exist_ok=True)

# Đường dẫn file log
log_file = os.path.join(log_dir, "app.log")

# Thêm FileHandler để ghi log vào file
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
)

# Đảm bảo không thêm nhiều handler nếu file được import nhiều lần
if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
    logger.addHandler(file_handler)
