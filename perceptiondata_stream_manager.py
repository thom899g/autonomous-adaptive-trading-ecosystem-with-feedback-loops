"""
Data Stream Manager for the Perception Layer.
Handles real-time market data ingestion from multiple sources with fault tolerance.
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import ccxt
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from config.firebase_config import firebase_client
from utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


@dataclass
class DataStreamConfig:
    """Configuration for data streams"""
    exchange_id: str
    symbols: List[str]
    timeframe: str = '1m'
    max_retries: int = 3
    retry_delay: int = 5
    buffer_size: int = 1000
    heartbeat_interval: int = 30  # seconds
    
    def __post_init__(self):
        """Validate configuration"""
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4