import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from technical import qtpylib

from features import Features

# isort: off

from freqtrade.strategy import IStrategy
from freqtrade.constants import Config
from freqtrade.persistence import Trade

# isort: on

logger = logging.getLogger(__name__)


class RiseAndFallPatternsStrategy(IStrategy):
    def __init__(self, config: Config):
        super().__init__(config)
        self.stoploss = -0.9
        self.rise_and_fall_pattern: List[str] = self.config["custom_params"]["rise_and_fall_pattern"]
        self.target_pattern: str = self.config["custom_params"]["target_pattern"]

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        logger.info(f"populate_indicators: {metadata}")
        assert self.timeframe == "1d"

        df["close_diff"] = df["close"].diff()

        def close_diff_kind(x):
            if x > 0.0:
                return "up"
            if x < 0.0:
                return "down"
            if np.isnan(x):
                return "nan"
            return "same"

        df["close_diff_kind"] = df["close_diff"].apply(close_diff_kind)
        df["close_diff_rate"] = df["close_diff"] / df["close"].shift(1)

        rise_and_fall_pattern_len = len(self.rise_and_fall_pattern)
        window_size = rise_and_fall_pattern_len + len([self.target_pattern])

        def close_diff_kind__predict__fun(values, d):
            roll = d.loc[values.index, "close_diff_kind"]
            assert len(self.rise_and_fall_pattern) == 5
            assert len(roll) == 6
            for pattern_val, data_val in zip(self.rise_and_fall_pattern, roll.values):
                if pattern_val == "skip":
                    continue
                if pattern_val != data_val:
                    return 0
            return 1

        df["close_diff_kind__predict"] = \
            (df
             .loc[:, ["close"]].rolling(window=window_size, min_periods=window_size)
             .apply(close_diff_kind__predict__fun, args=(df,))
             )

        assert df.loc[:rise_and_fall_pattern_len, "close_diff_kind__predict"].isna().sum() == rise_and_fall_pattern_len

        return df

    def populate_entry_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[df["close_diff_kind__predict"] == 1.0, ["enter_long", "enter_tag"]] = (1, "long")

        df["rise_and_fall_pattern"] = str(self.rise_and_fall_pattern)
        df["target_pattern"] = self.target_pattern
        df.to_csv("rise_and_fall_patterns_df.csv", index=False)

        return df

    def populate_exit_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # df["exit_long"] = df["enter_long"].shift(1)
        # df.loc[df["exit_long"] == 1, "exit_tag"] = "long"
        return df

    def custom_exit(
            self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float, **kwargs
    ):
        return "custom_exit"
