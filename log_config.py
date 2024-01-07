import logging
from logging.handlers import RotatingFileHandler


def setup_logging(name, log_file, level=logging.INFO):
    handler = RotatingFileHandler(
        log_file, maxBytes=10000, backupCount=5
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
