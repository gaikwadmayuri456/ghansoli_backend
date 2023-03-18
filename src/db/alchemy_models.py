from loguru import logger
from .alchemy import Base

try:
    rates_live = Base.classes.rates_live

except Exception as e:
    logger.debug(f"Error While Creating Models: {e}")
