"""Base service — shared concerns for all services."""
from abc import ABC

import logging

from utils.logger import get_logger

logger = get_logger()


class BaseService(ABC):
    pass
