import os
import logging
from dotenv import load_dotenv

from logging.handlers import RotatingFileHandler

load_dotenv()


def setup_logging(name, log_file, level=None):
    if level is None:
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, log_level_str, logging.INFO)

    handler = RotatingFileHandler(
        log_file, maxBytes=10000000, backupCount=5
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
