from loguru import logger

import sys

logger.remove()


logger.add(
    sys.stdout,
    level='INFO',
    colorize=True,
    enqueue=True,
    backtrace=True,
    diagnose=False
)

logger.add(
    "logs/app.log",
    level='DEBUG',
    rotation="100 MB",
    retention="30 days",
    compression='zip',
    enqueue=True
)

logger.add(
    "logs/error.log",
    level='ERROR',
    rotation="50 MB",
    retention="60 days",
    compression='zip',
    enqueue=True
)