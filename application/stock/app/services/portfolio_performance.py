import pandas as pd

from app.services.company_detail import NAME_COLUMN, get_symbol_column
from app.services.stock_listing import SUPPORTED_MARKETS, _is_missing, get_stock_listing

CHANGE_RATE_COLUMNS = ('ChagesRatio', 'ChangeRate', 'ChangesRatio', 'Change%')


def _extract_change_pct(row: pd.Series) -> float | None:
    for col in CHANGE_RATE_COLUMNS:
        if col not in row.index:
            continue
        value = row[col]
        if _is_missing(value):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _lookup_quote(market: str, symbol: str) -> dict | None:
    if market not in SUPPORTED_MARKETS:
        return None

    df = get_stock_listing(market)
    sym_col = get_symbol_column(market)
    if sym_col not in df.columns:
        return None

    matched = df[df[sym_col].astype(str) == str(symbol)]
    if matched.empty:
        return None

    row = matched.iloc[0]
    name = row[NAME_COLUMN] if NAME_COLUMN in row.index and not _is_missing(row[NAME_COLUMN]) else str(symbol)
    change_pct = _extract_change_pct(row)

    return {
        'market': market,
        'symbol': str(symbol),
        'name': str(name),
        'change_pct': change_pct,
    }


def get_portfolio_performance(holdings: list[dict]) -> dict:
    """포트폴리오 비중·등락률 기반 종합 수익률을 계산합니다."""
    results = []
    total_weight = 0.0
    weighted_return = 0.0
    all_quoted = True

    for holding in holdings:
        market = str(holding.get('market', '')).strip()
        symbol = str(holding.get('symbol', '')).strip()
        try:
            weight = float(holding.get('weight', 0))
        except (TypeError, ValueError):
            weight = 0.0

        total_weight += weight
        quote = _lookup_quote(market, symbol) if market and symbol else None
        change_pct = quote['change_pct'] if quote else None
        contribution = None

        if change_pct is None:
            all_quoted = False
        else:
            contribution = weight * change_pct / 100
            weighted_return += contribution

        results.append({
            'market': market,
            'symbol': symbol,
            'name': quote['name'] if quote else holding.get('name'),
            'weight': round(weight, 2),
            'change_pct': change_pct,
            'contribution': round(contribution, 4) if contribution is not None else None,
            'found': quote is not None,
        })

    weight_valid = abs(total_weight - 100) < 0.01
    valid = weight_valid and bool(holdings) and all_quoted

    return {
        'holdings': results,
        'total_weight': round(total_weight, 2),
        'weighted_return_pct': round(weighted_return, 4) if valid else None,
        'valid': valid,
        'weight_valid': weight_valid,
    }
