import json
import wandb
import itertools
import subprocess
from typing import List

import numpy as np
import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.data.btanalysis import load_backtest_data, load_backtest_stats, load_backtest_metadata
from freqtrade.resolvers import StrategyResolver
from freqtrade.data.history import load_pair_history
from freqtrade.enums import CandleType
from freqtrade.data.dataprovider import DataProvider
from tqdm import tqdm


def handle_pattern(rise_and_fall_pattern: List[str], target_pattern: str):
    config = Configuration.from_files(["config_rise_and_fall_patterns_strategy.json"])["original_config"]
    config["custom_params"]["rise_and_fall_pattern"] = rise_and_fall_pattern
    config["custom_params"]["target_pattern"] = target_pattern
    with open("config_rise_and_fall_patterns_strategy___custom.json", "w") as fp:
        json.dump(config, fp)
        fp.flush()

    cmd = "freqtrade backtesting --config config_rise_and_fall_patterns_strategy___custom.json --config config_private.json --cache none"
    proc = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, cwd="..")
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        print("stdout:", line.rstrip())

    config = Configuration.from_files(["config_rise_and_fall_patterns_strategy___custom.json"])
    backtest_dir = config["user_data_dir"] / "backtest_results"
    stats = load_backtest_stats(backtest_dir)
    strategy_name = "RiseAndFallPatternsStrategy"
    strategy_stats = stats["strategy"][strategy_name]

    df = pd.read_csv("rise_and_fall_patterns_df.csv")
    assert all(df["rise_and_fall_pattern"] == str(list(rise_and_fall_pattern)))
    assert all(df["target_pattern"] == target_pattern)

    df_predict_true = df[df["close_diff_kind__predict"] == 1.0]
    winrate = np.count_nonzero(df_predict_true["close_diff_kind"] == target_pattern) / len(df_predict_true)

    with open("user_data/backtest_results/.last_result.json", "r") as fp:
        last_result_dict = json.load(fp)

    wandb.init(project="...", entity="...", job_type="backtest")

    config["custom_params"]["rise_and_fall_pattern"] = ",".join(config["custom_params"]["rise_and_fall_pattern"])
    config["trading_mode"] = str(config["trading_mode"])
    config["runmode"] = str(config["runmode"])
    config["candle_type_def"] = str(config["candle_type_def"])
    del config["user_data_dir"]
    del config["datadir"]
    del config["exportfilename"]
    wandb.log({
        "config": config,
        "stats": strategy_stats,
        "winrate": winrate,
        "last_result": last_result_dict,
    })

    wandb.finish()


def main():
    all_patterns = list(itertools.product(["up", "down", "skip"], repeat=5))

    for pattern in tqdm(all_patterns):
        for target in ["up", "down"]:
            handle_pattern(pattern, target)


if __name__ == "__main__":
    main()
