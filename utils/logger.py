# utils/logger.py

import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

    # Rotating File Handler
    handler = RotatingFileHandler('logs/strategy.log', maxBytes=5*1024*1024, backupCount=5)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
