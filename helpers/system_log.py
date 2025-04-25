import logging


def setup_logger(log_file):
    """
    Set up a logger to write logs to a file with three levels: INFO, ERROR, DEBUG.
    """
    logger = logging.getLogger("system_log")
    logger.setLevel(logging.DEBUG)

    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Create formatter and add it to the handler
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add the handler to the logger
    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger


# Example usage
if __name__ == "__main__":
    log_file_path = "/logs/"
    logger = setup_logger(log_file_path)

    logger.info("This is an info message.")
    logger.error("This is an error message.")
    logger.debug("This is a debug message.")
