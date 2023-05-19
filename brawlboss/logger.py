import discord
import logging
import logging.handlers

# Loggers
logger = logging.getLogger('brawlboss')
bot_logger = logging.getLogger('discord')
http_logger = logging.getLogger('discord.http')

# Levels
logger.setLevel(logging.DEBUG)
bot_logger.setLevel(logging.DEBUG)
http_logger.setLevel(logging.INFO)

# Handlers
null_handler = logging.NullHandler()
stream_handler = logging.StreamHandler()
file_handler = logging.handlers.RotatingFileHandler(
    filename='brawlboss.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)

# Formatter
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
# Set formatter
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
bot_logger.addHandler(file_handler)
bot_logger.addHandler(stream_handler)
