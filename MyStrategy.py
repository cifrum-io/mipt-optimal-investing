import logging

import pandas as pd
from technical import qtpylib


# isort: off

from freqtrade.strategy import IStrategy
from freqtrade.constants import Config

# isort: on

logger = logging.getLogger(__name__)


# * Download OHLCV data for the pairlist including all informative pairs
#       This step is only executed once per Candle to avoid unnecessary network traffic.
# * Call populate_indicators()
# * Call populate_entry_trend()
# * Call populate_exit_trend()


class MyStrategy(IStrategy):
    def __init__(self, config: Config):
        super().__init__(config)
        self.stoploss = -0.5

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        logger.info(f"populate_indicators: {metadata}")
        df["typical_price"] = qtpylib.typical_price(df)
        df["signal-entry"] = df["typical_price"] < 2000.0
        df["signal-exit"] = df["typical_price"] > 2000.0
        return df

    def populate_entry_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[df["signal-entry"], ["enter_long", "enter_tag"]] = (1, "long-enter")
        return df

    def populate_exit_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[df["signal-exit"], ["exit_long", "exit_tag"]] = (1, "long-exit")
        return df
