import logging
import os

# Tạo thư mục logs nếu chưa tồn tại
log_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
os.makedirs(log_dir, exist_ok=True)

# Đường dẫn file log
log_file = os.path.join(log_dir, "app.log")


# Tạo logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


# Xóa basicConfig vì nó có thể gây xung đột
# Chỉ sử dụng FileHandler
file_handler = logging.FileHandler(
    filename=log_file,
    mode="a",
    encoding="utf-8",
)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
)

# Đảm bảo không thêm nhiều handler nếu file được import nhiều lần
if not logger.handlers:
    logger.addHandler(file_handler)
