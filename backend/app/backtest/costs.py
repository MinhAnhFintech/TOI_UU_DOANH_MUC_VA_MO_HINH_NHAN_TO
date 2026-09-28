import numpy as np


def compute_transaction_costs(
    w_before: np.ndarray,
    w_after: np.ndarray,
    fee_buy: float = 0.0015,
    fee_sell: float = 0.0025
) -> float:
    """Compute total transaction costs from rebalancing.

    Cost = sum(max(Δw_i, 0)) × fee_buy + sum(max(-Δw_i, 0)) × fee_sell

    On Vietnam's HOSE exchange:
    - Buying fee: ~0.15% of transaction value
    - Selling fee: ~0.15% brokerage + 0.10% selling tax = 0.25% total

    Args:
        w_before: Current portfolio weights (may have drifted from target)
        w_after: New target weights after rebalancing
        fee_buy: Buying commission rate (default 0.15%)
        fee_sell: Selling commission + tax rate (default 0.25%)

    Returns:
        Total transaction cost as a fraction of portfolio value
    """
    delta = w_after - w_before

    # Buys: positive delta (increasing position)
    buy_cost = np.sum(np.maximum(delta, 0)) * fee_buy
    # Sells: negative delta (decreasing position)
    sell_cost = np.sum(np.maximum(-delta, 0)) * fee_sell

    return float(buy_cost + sell_cost)

