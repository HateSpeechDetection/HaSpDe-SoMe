import logging
import logging.handlers
import os

# Optional: Colorize console logs (requires 'colorlog' package)
try:
    from colorlog import ColoredFormatter
    color_logging_enabled = True
except ImportError:
    color_logging_enabled = False

# Determine logging level based on environment variable, default to DEBUG
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()

# Set up logging configuration
logger = logging.getLogger("HaSpDe_SoMe")
logger.setLevel(log_level)

# Formatter for log messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console handler with color support
console_handler = logging.StreamHandler()
if color_logging_enabled:
    color_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(color_formatter)
else:
    console_handler.setFormatter(formatter)

# Add console handler to logger
logger.addHandler(console_handler)

# File handler with rotation
log_file = "app.log"
file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(formatter)

# Add file handler to logger
logger.addHandler(file_handler)

# Example of adding a custom log level (optional)
# logging.addLevelName(25, "NOTICE")
# def notice(self, message, *args, **kws):
#     if self.isEnabledFor(25):
#         self._log(25, message, args, **kws)
# logging.Logger.notice = notice

# Example usage:
# logger.debug("This is a debug message")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.critical("This is a critical message")
# logger.notice("This is a notice message")  # Custom log level example
