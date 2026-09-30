MODEL_REGISTRY = {
    'capm': ['mkt'],
    'ff3': ['mkt', 'smb', 'hml'],
    'ff5': ['mkt', 'smb', 'hml', 'rmw', 'cma'],
    'ff5_liq': ['mkt', 'smb', 'hml', 'rmw', 'cma', 'liq'],
    'ff5_for': ['mkt', 'smb', 'hml', 'rmw', 'cma', 'for_'],
    'ff5_vol': ['mkt', 'smb', 'hml', 'rmw', 'cma', 'vol'],
    'ff5_all': ['mkt', 'smb', 'hml', 'rmw', 'cma', 'liq', 'for_', 'vol'],
    # Backward compatible aliases used by older saved configurations.
    'ff5_liq_for': ['mkt', 'smb', 'hml', 'rmw', 'cma', 'liq', 'for_'],
    'ff5_liq_for_vol': ['mkt', 'smb', 'hml', 'rmw', 'cma', 'liq', 'for_', 'vol'],
}


def get_model_factors(model_name: str) -> list[str]:
    try:
        return MODEL_REGISTRY[model_name.strip().lower()]
    except (AttributeError, KeyError):
        raise ValueError(f"Unsupported factor model: {model_name}") from None


def get_factor_result_name(factor_name: str) -> str:
    """Map factor column names to the stable names used by API/database results."""
    return "for" if factor_name == "for_" else factor_name
