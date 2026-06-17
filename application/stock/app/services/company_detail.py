from datetime import datetime, timedelta

import FinanceDataReader as fdr
import pandas as pd

from app.services.stock_listing import (
    EOK_WON_COLUMNS,
    _is_missing,
    format_eok_won,
    format_number,
    get_column_label,
    get_stock_listing,
)

SYMBOL_COLUMN = {
    'KRX': 'Code',
}
DEFAULT_SYMBOL_COLUMN = 'Symbol'
NAME_COLUMN = 'Name'

PROFILE_MARKETS = {'KRX'}

PRICE_HISTORY_DAYS = 30


def get_symbol_column(market: str) -> str:
    return SYMBOL_COLUMN.get(market, DEFAULT_SYMBOL_COLUMN)


def _serialize_value(value):
    if _is_missing(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, (int, float)):
        return format_number(value)
    return str(value)


def _format_field_value(key: str, value, market: str):
    if key in EOK_WON_COLUMNS:
        formatted = format_eok_won(value, key, market)
        return None if formatted == '-' else formatted
    return _serialize_value(value)


def _records_to_items(record: dict, market: str) -> list[dict]:
    return [
        {'label': get_column_label(key), 'value': _format_field_value(key, val, market)}
        for key, val in record.items()
        if _format_field_value(key, val, market) is not None
    ]


def _find_listing_row(market: str, symbol: str) -> pd.Series | None:
    df = get_stock_listing(market)
    col = get_symbol_column(market)
    if col not in df.columns:
        return None

    matched = df[df[col].astype(str) == str(symbol)]
    if matched.empty:
        return None
    return matched.iloc[0]


def _price_reader_symbol(market: str, symbol: str) -> str:
    if market in ('KRX', 'ETF/KR', 'S&P500'):
        return symbol
    return f'{market}:{symbol}'


def _fetch_profile(symbol: str) -> dict | None:
    if not symbol.isdigit():
        return None
    try:
        from FinanceDataReader.naver.snap import factors

        return factors(symbol)
    except Exception:
        return None


def _fetch_recent_prices(market: str, symbol: str) -> list[dict]:
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=PRICE_HISTORY_DAYS)).strftime('%Y-%m-%d')
    reader_symbol = _price_reader_symbol(market, symbol)

    try:
        df = fdr.DataReader(reader_symbol, start, end)
    except Exception:
        return []

    if df.empty:
        return []

    df = df.reset_index()
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')
    df = df.sort_values(date_col, ascending=False).head(20)
    return df.to_dict(orient='records')


def get_company_detail(market: str, symbol: str) -> dict:
    row = _find_listing_row(market, symbol)
    if row is None:
        raise ValueError(f'종목을 찾을 수 없습니다: {symbol}')

    listing = {key: _serialize_value(val) for key, val in row.to_dict().items()}
    name = listing.get(NAME_COLUMN) or symbol

    sections = [
        {
            'title': '시장 정보',
            'type': 'items',
            'items': _records_to_items(listing, market),
        }
    ]

    if market in PROFILE_MARKETS:
        profile = _fetch_profile(symbol)
        if profile:
            items = [
                {'label': key, 'value': _serialize_value(val)}
                for key, val in profile.items()
                if _serialize_value(val) is not None
            ]
            if items:
                sections.append({
                    'title': '기업 정보',
                    'type': 'items',
                    'items': items,
                })

    prices = _fetch_recent_prices(market, symbol)
    if prices:
        price_columns = list(prices[0].keys())
        sections.append({
            'title': f'최근 시세 ({len(prices)}일)',
            'type': 'table',
            'columns': price_columns,
            'column_labels': [get_column_label(col) for col in price_columns],
            'rows': [
                {k: _serialize_value(v) for k, v in record.items()}
                for record in prices
            ],
        })

    return {
        'market': market,
        'symbol': symbol,
        'name': name,
        'sections': sections,
    }
