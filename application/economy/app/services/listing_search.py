from __future__ import annotations

import pandas as pd

from app.config import Config
from app.services.cache import get_cached

POPULAR_US_ETFS: list[tuple[str, str]] = [
    ('SPY', 'SPY (S&P500)'),
    ('QQQ', 'QQQ (나스닥100)'),
    ('VTI', 'VTI (미국 전체)'),
    ('VOO', 'VOO (S&P500)'),
    ('IVV', 'IVV (S&P500)'),
    ('IWM', 'IWM (러셀2000)'),
    ('DIA', 'DIA (다우)'),
    ('XLK', 'XLK (기술)'),
    ('XLF', 'XLF (금융)'),
    ('XLE', 'XLE (에너지)'),
    ('GLD', 'GLD (금)'),
    ('TLT', 'TLT (미국채20년+)'),
    ('HYG', 'HYG (하이일드)'),
    ('EEM', 'EEM (신흥국)'),
    ('VEA', 'VEA (선진 ex-US)'),
    ('VWO', 'VWO (신흥국)'),
    ('SCHD', 'SCHD (배당)'),
    ('SMH', 'SMH (반도체)'),
    ('SOXX', 'SOXX (반도체)'),
    ('ARKK', 'ARKK (혁신)'),
]


def _load_listing(market: str) -> pd.DataFrame:
    def loader() -> pd.DataFrame:
        import FinanceDataReader as fdr

        df = fdr.StockListing(market)
        return _normalize_listing_df(df)

    return get_cached(f'listing:v2:{market}', Config.SNAPSHOT_TTL_SEC, loader)


def _normalize_listing_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    if 'Code' not in out.columns and 'Symbol' in out.columns:
        out['Code'] = out['Symbol']
    if 'Name' not in out.columns:
        for col in ('종목명', 'name'):
            if col in out.columns:
                out['Name'] = out[col]
                break
    return out


def _normalize_symbol(raw: object) -> str:
    if raw is None or pd.isna(raw):
        return ''
    text = str(raw).strip()
    if not text or text.lower() == 'nan':
        return ''
    try:
        num = int(float(text))
        return str(num).zfill(6)
    except (TypeError, ValueError):
        return text


def _extract_name(row: pd.Series) -> str:
    for col in ('Name', '종목명', 'name'):
        if col not in row.index:
            continue
        raw = row[col]
        if raw is None or pd.isna(raw):
            continue
        text = str(raw).strip()
        if text and text.lower() != 'nan':
            return text
    return ''


def _extract_code(row: pd.Series) -> str:
    for col in ('Code', 'Symbol', 'code', 'symbol'):
        if col not in row.index:
            continue
        code = _normalize_symbol(row[col])
        if code:
            return code
    return ''


def _match_rows(df: pd.DataFrame, query: str, *, limit: int = 20) -> list[dict[str, str]]:
    q = query.strip().lower()
    if not q or df.empty:
        return []

    q_digits = q if q.isdigit() else ''.join(ch for ch in q if ch.isdigit())
    rows: list[dict[str, str]] = []
    for _, row in df.iterrows():
        code = _extract_code(row)
        name = _extract_name(row)
        if not code or not name:
            continue

        haystack = f'{code} {name}'.lower()
        matched = q in haystack
        if not matched and q_digits:
            matched = code.startswith(q_digits.zfill(6)) or q_digits in code
        if not matched:
            continue

        rows.append({'symbol': code, 'name': name})
        if len(rows) >= limit:
            break
    return rows


def search_category_listings(category: str, query: str, *, limit: int = 20) -> list[dict[str, str]]:
    query = query.strip()
    if not query:
        return []

    if category == 'kr_market':
        df = _load_listing('KRX')
        return _match_rows(df, query, limit=limit)

    if category == 'etf_kr':
        df = _load_listing('ETF/KR')
        return _match_rows(df, query, limit=limit)

    if category == 'etf_us':
        q = query.upper()
        results: list[dict[str, str]] = []
        for symbol, name in POPULAR_US_ETFS:
            if q in symbol or q in name.upper():
                results.append({'symbol': symbol, 'name': name})
            if len(results) >= limit:
                return results
        if len(results) < limit and q.isalpha() and len(q) <= 5:
            from app.services.custom_cards import validate_us_etf_ticker

            validated = validate_us_etf_ticker(q)
            if validated and not any(item['symbol'] == validated[0] for item in results):
                results.append({'symbol': validated[0], 'name': validated[0]})
        return results[:limit]

    return []
