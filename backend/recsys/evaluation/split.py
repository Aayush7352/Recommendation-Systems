from __future__ import annotations

import numpy as np
import pandas as pd

from ..models.base import TrainTestSplit


def leave_one_out_split(
    interactions: pd.DataFrame,
    timestamp_col: str = "timestamp",
    min_interactions: int = 2,
    seed: int = 42,
) -> TrainTestSplit:
    rng = np.random.default_rng(seed)
    interactions = interactions.copy()

    counts = interactions.groupby("user_id").size()
    eligible_users = counts[counts >= min_interactions].index
    eligible_mask = interactions["user_id"].isin(eligible_users)

    eligible = interactions[eligible_mask]
    ineligible = interactions[~eligible_mask]

    if timestamp_col in eligible.columns:
        idx = eligible.groupby("user_id")[timestamp_col].idxmax()
    else:
        idx = (
            eligible.groupby("user_id")
            .apply(lambda g: rng.choice(g.index))
            .values
        )

    test = eligible.loc[idx]
    train = pd.concat([eligible.drop(idx), ineligible], ignore_index=True)

    return TrainTestSplit(train=train.reset_index(drop=True), test=test.reset_index(drop=True))


def random_split(
    interactions: pd.DataFrame,
    test_frac: float = 0.2,
    seed: int = 42,
) -> TrainTestSplit:
    shuffled = interactions.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    n_test = int(len(shuffled) * test_frac)
    test = shuffled.iloc[:n_test].reset_index(drop=True)
    train = shuffled.iloc[n_test:].reset_index(drop=True)
    return TrainTestSplit(train=train, test=test)


def temporal_split(
    interactions: pd.DataFrame,
    test_frac: float = 0.2,
    timestamp_col: str = "timestamp",
) -> TrainTestSplit:
    sorted_df = interactions.sort_values(timestamp_col).reset_index(drop=True)
    cut = int(len(sorted_df) * (1 - test_frac))
    return TrainTestSplit(
        train=sorted_df.iloc[:cut].reset_index(drop=True),
        test=sorted_df.iloc[cut:].reset_index(drop=True),
    )
