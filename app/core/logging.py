# app/core/logging.py
import logging
from datetime import datetime

def setup_logger():
    logger = logging.getLogger('code_expert')
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler = logging.FileHandler(
        f'logs/code_expert_{datetime.now().strftime("%Y%m%d")}.log'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger