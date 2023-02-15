import logging

LOG_LEVEL = "DEBUG"
COMMON_FORMAT_STRING = " [%(levelname)-4s] [%(asctime)s] >> %(message)s"
USER_FORMAT_STRING = (
    "[L:%(lineno)d] [%(filename)s | %(funcName)s] [%(name)s]" + COMMON_FORMAT_STRING
)
INTERNAL_FORMAT_STRING = (
    "[L:%(lineno)d] [internal | uvicorn] [message]" + COMMON_FORMAT_STRING
)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "format": USER_FORMAT_STRING,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": LOG_LEVEL,
        }
    },
    "loggers": {
        "root": {"handlers": ["console"], "level": LOG_LEVEL},
    },
}

logger = logging.getLogger(__name__)
