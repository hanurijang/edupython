from __future__ import annotations

import os
from datetime import datetime, timedelta

import FinanceDataReader as fdr
import pandas as pd
import requests

KOSPI_SECTOR_INDEX_RANGE = range(1005, 1028)
# 제조(1027)는 거의 모든 제조주를 포함하므로 기본 섹터 라벨에서 제외
SECTOR_BROAD_CODES = frozenset({'1027'})
# 금융(1021)은 증권(1024)·보험(1025)보다 후순위
SECTOR_LOW_PRIORITY_CODES = frozenset({'1021'})

from app.services.sector_cache import (
    assemble_constituents,
    load_sector_cache,
    load_sector_item,
    save_sector_cache,
)

FDR_CACHE_BASE = (
    'https://raw.githubusercontent.com/FinanceData/fdr_krx_data_cache/master/data/snap'
)
FDR_CACHE_API = 'https://api.github.com/repos/FinanceData/fdr_krx_data_cache/contents/data/snap'
CACHE_LOOKUP_DAYS = 30

CONSTITUENT_COLUMNS = ('Code', 'Name', 'Close', 'Rate', 'Marcap')


def krx_login_configured() -> bool:
    """KRX 로그인 환경 변수(KRX_ID, KRX_PW) 설정 여부."""
    return bool(os.getenv('KRX_ID') and os.getenv('KRX_PW'))


def get_krx_index_list() -> pd.DataFrame:
    """KRX 전체 지수 목록을 반환합니다."""
    df = fdr.SnapDataReader('KRX/INDEX/LIST')
    return df.reset_index(drop=True)


def get_sector_indices() -> pd.DataFrame:
    """KOSPI 업종(섹터) 지수 목록을 반환합니다. (1005~1027)"""
    index_list = get_krx_index_list()
    numeric = index_list[index_list['Code'].str.match(r'^\d+$')].copy()
    numeric['_code_num'] = numeric['Code'].astype(int)
    sector = numeric[numeric['_code_num'].isin(KOSPI_SECTOR_INDEX_RANGE)].drop(columns='_code_num')
    return sector.reset_index(drop=True)


def discover_cached_index_codes(*, refresh: bool = False) -> list[str]:
    """GitHub 캐시에 구성종목 데이터가 있는 지수 코드 목록을 반환합니다."""
    cache: list[str] | None = None if refresh else getattr(discover_cached_index_codes, '_cache', None)
    if cache is not None:
        return list(cache)

    response = requests.get(FDR_CACHE_API, timeout=15)
    response.raise_for_status()
    codes = sorted(
        item['name'].removeprefix('index_stock_')
        for item in response.json()
        if item['name'].startswith('index_stock_')
    )
    discover_cached_index_codes._cache = codes
    return list(codes)


def _normalize_constituents(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        'ComparedRate': 'Change',
        'STR_CMP_PRC': 'Change',
        'RateCode': 'ChangeCode',
        'FLUC_RT': 'Rate',
        'TDD_CLSPRC': 'Close',
        'MKTCAP': 'Marcap',
        'ISU_SRT_CD': 'Code',
        'ISU_ABBRV': 'Name',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    keep = [col for col in CONSTITUENT_COLUMNS if col in df.columns]
    if 'Code' not in keep:
        return pd.DataFrame(columns=list(CONSTITUENT_COLUMNS))

    out = df[keep].copy()
    out['Code'] = out['Code'].astype(str).str.zfill(6)
    for col in ('Close', 'Rate', 'Marcap'):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors='coerce')
    return out.reset_index(drop=True)


def _fetch_cache_constituents(code: str) -> tuple[pd.DataFrame, str | None]:
    """GitHub 캐시에서 지수 구성종목을 조회합니다. (최근 비어 있지 않은 날짜 사용)"""
    today = datetime.today()
    for offset in range(CACHE_LOOKUP_DAYS):
        date_str = (today - timedelta(days=offset)).strftime('%Y-%m-%d')
        url = f'{FDR_CACHE_BASE}/index_stock_{code}/{date_str}.csv'
        try:
            df = pd.read_csv(url, index_col=0, dtype=str)
        except Exception:
            continue
        if df.empty:
            continue
        return _normalize_constituents(df), date_str
    return pd.DataFrame(columns=list(CONSTITUENT_COLUMNS)), None


def _fetch_live_constituents(code: str) -> pd.DataFrame:
    """FinanceDataReader SnapDataReader로 실시간 조회를 시도합니다."""
    ticker = f'KRX/INDEX/STOCK/{code}'
    df = fdr.SnapDataReader(ticker)
    return _normalize_constituents(df)


def _fetch_krx_session_constituents(code: str) -> tuple[pd.DataFrame, str | None]:
    """KRX 로그인 세션(pykrx)으로 지수 구성종목을 조회합니다."""
    if not krx_login_configured():
        return pd.DataFrame(columns=list(CONSTITUENT_COLUMNS)), None

    from pykrx.stock import get_nearest_business_day_in_a_week
    from pykrx.website.krx.market.core import 지수구성종목

    trade_date = get_nearest_business_day_in_a_week().replace('-', '')
    group_id = code[0]
    ticker = code[1:]
    raw = 지수구성종목().fetch(trade_date, ticker, group_id)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=list(CONSTITUENT_COLUMNS)), None

    as_of = datetime.strptime(trade_date, '%Y%m%d').strftime('%Y-%m-%d')
    return _normalize_constituents(raw), as_of


def get_index_constituents(code: str) -> dict:
    """지수 코드에 포함된 구성종목을 반환합니다."""
    code = str(code).strip()
    if not code.isdigit():
        raise ValueError(f'지수 코드는 숫자여야 합니다: {code}')

    index_list = get_krx_index_list()
    matched = index_list[index_list['Code'].astype(str) == code]
    index_name = str(matched.iloc[0]['Name']) if not matched.empty else None
    index_market = str(matched.iloc[0]['Market']) if not matched.empty else None

    df, as_of = _fetch_cache_constituents(code)
    source = 'github_cache' if as_of else None
    error = None

    if df.empty:
        df, as_of = _fetch_krx_session_constituents(code)
        if not df.empty:
            source = 'krx_session'

    if df.empty:
        try:
            df = _fetch_live_constituents(code)
            source = 'krx_live'
            as_of = datetime.today().strftime('%Y-%m-%d')
        except Exception as exc:
            if krx_login_configured():
                error = str(exc)
            else:
                error = (
                    f'{exc} — 섹터·지수 구성종목은 edupython/.env 에 '
                    'KRX_ID, KRX_PW 설정 또는 GitHub 캐시가 필요합니다.'
                )

    return {
        'code': code,
        'name': index_name,
        'market': index_market,
        'source': source,
        'as_of': as_of,
        'count': len(df),
        'available': not df.empty,
        'login_configured': krx_login_configured(),
        'error': error,
        'constituents': df.to_dict(orient='records'),
    }


def get_index_coverage() -> dict:
    """전체 지수 중 구성종목 데이터를 조회할 수 있는 지수 현황을 반환합니다."""
    index_list = get_krx_index_list()
    cached_codes = set(discover_cached_index_codes())

    indices = []
    for row in index_list.itertuples(index=False):
        code = str(row.Code)
        indices.append({
            'code': code,
            'name': str(row.Name),
            'market': str(row.Market),
            'cached': code in cached_codes,
        })

    cached = [item for item in indices if item['cached']]
    sector = get_sector_indices()
    return {
        'total_indices': len(indices),
        'cached_indices': len(cached),
        'uncached_indices': len(indices) - len(cached),
        'login_configured': krx_login_configured(),
        'sector_index_count': len(sector),
        'indices': indices,
        'cached_only': cached,
        'sector_indices': sector.to_dict(orient='records'),
    }


def build_stock_index_map(codes: list[str] | None = None) -> dict:
    """종목별로 어떤 지수에 포함되는지 역매핑을 생성합니다."""
    if codes is None:
        codes = discover_cached_index_codes()
    if not codes:
        return {'codes_requested': [], 'stock_map': {}, 'index_summary': []}

    stock_map: dict[str, dict] = {}
    index_summary = []

    for code in codes:
        result = get_index_constituents(code)
        index_summary.append({
            'code': result['code'],
            'name': result['name'],
            'count': result['count'],
            'available': result['available'],
            'as_of': result['as_of'],
            'source': result['source'],
        })
        if not result['available']:
            continue

        for item in result['constituents']:
            symbol = str(item.get('Code', '')).zfill(6)
            if not symbol:
                continue
            entry = stock_map.setdefault(symbol, {
                'symbol': symbol,
                'name': item.get('Name'),
                'indices': [],
            })
            entry['indices'].append({
                'code': result['code'],
                'name': result['name'],
                'market': result['market'],
            })

    return {
        'codes_requested': codes,
        'stock_count': len(stock_map),
        'index_summary': index_summary,
        'stock_map': stock_map,
    }


def get_sector_code_names() -> dict[str, str]:
    """섹터 지수 코드 → 섹터명 (예: '1013' → '전기전자')."""
    sectors = get_sector_indices()
    return dict(zip(sectors['Code'].astype(str), sectors['Name'].astype(str)))


def _sector_assignment_order(codes: list[str]) -> list[str]:
    """중복 종목은 구체적 섹터가 우선되도록 코드 순서를 정합니다."""
    numeric = sorted(
        (c for c in codes if c not in SECTOR_BROAD_CODES),
        key=lambda c: (c in SECTOR_LOW_PRIORITY_CODES, int(c) if c.isdigit() else 9999),
    )
    return numeric


def build_code_to_sector_map(
    sector_constituents: dict[str, list[str]],
    sector_names: dict[str, str] | None = None,
) -> dict[str, str]:
    """{섹터코드: [종목코드]} → {종목코드: 섹터명} 역매핑을 만듭니다."""
    if sector_names is None:
        sector_names = get_sector_code_names()

    mapping: dict[str, str] = {}
    for sector_code in _sector_assignment_order(list(sector_constituents.keys())):
        sector_name = sector_names.get(sector_code, sector_code)
        for stock_code in sector_constituents.get(sector_code, []):
            code = str(stock_code).strip().zfill(6)
            if code and code not in mapping:
                mapping[code] = sector_name
    return mapping


def apply_sector_to_dataframe(
    df: pd.DataFrame,
    code_to_sector: dict[str, str],
    *,
    code_column: str = 'Code',
    default: str = '기타',
) -> pd.DataFrame:
    """종목 목록 DataFrame에 Sector 열을 추가합니다."""
    if code_column not in df.columns:
        raise ValueError(f"'{code_column}' 열이 없습니다.")

    result = df.copy()
    normalized = result[code_column].astype(str).str.strip().str.zfill(6)
    result['Sector'] = normalized.map(code_to_sector).fillna(default)
    return result


def _fetch_sector_constituents_from_api(
    *,
    force_refresh: bool = False,
    only_codes: list[str] | None = None,
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """KRX API로 섹터 구성종목을 조회합니다 (캐시 미스·만료분만)."""
    sectors = get_sector_indices()
    sector_names = dict(zip(sectors['Code'].astype(str), sectors['Name'].astype(str)))
    target_codes = only_codes or sectors['Code'].astype(str).tolist()

    constituents: dict[str, list[str]] = {}
    if not force_refresh:
        for code in target_codes:
            cached = load_sector_item(code)
            if cached is not None:
                constituents[code] = cached

    for code in target_codes:
        if code in constituents:
            continue
        payload = get_index_constituents(code)
        if not payload['available']:
            continue
        stocks = [
            str(item['Code']).zfill(6)
            for item in payload['constituents']
            if item.get('Code')
        ]
        if stocks:
            constituents[code] = stocks

    return constituents, sector_names


def warm_sector_cache(sector_constituents: dict[str, list[str]]) -> dict:
    """이미 조회한 sectorList 를 캐시에 저장합니다 (API 재호출 없음)."""
    normalized = {
        str(k): [str(c).zfill(6) for c in v]
        for k, v in sector_constituents.items()
    }
    sector_names = get_sector_code_names()
    code_to_sector = build_code_to_sector_map(normalized, sector_names)
    return save_sector_cache(normalized, sector_names, code_to_sector)


def get_code_to_sector_map(*, force_refresh: bool = False) -> dict[str, str]:
    """종목코드 → 섹터명 매핑 (캐시 우선)."""
    if not force_refresh:
        cached = load_sector_cache()
        if cached is not None:
            return dict(cached['code_to_sector'])

        sector_codes = list(get_sector_code_names().keys())
        assembled = assemble_constituents(sector_codes)
        if assembled is not None:
            sector_names = get_sector_code_names()
            code_to_sector = build_code_to_sector_map(assembled, sector_names)
            save_sector_cache(assembled, sector_names, code_to_sector)
            return code_to_sector

    constituents, sector_names = _fetch_sector_constituents_from_api(force_refresh=force_refresh)
    if not constituents:
        return {}

    code_to_sector = build_code_to_sector_map(constituents, sector_names)
    save_sector_cache(constituents, sector_names, code_to_sector)
    return code_to_sector


def fetch_kospi_sector_constituents(
    *,
    force_refresh: bool = False,
    sector_constituents: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """KOSPI 섹터 지수(1005~1027)별 구성종목 코드 목록 (캐시 우선)."""
    if sector_constituents is not None:
        return {
            str(k): [str(c).zfill(6) for c in v]
            for k, v in sector_constituents.items()
        }

    cached = load_sector_cache(force_refresh=force_refresh)
    if cached is not None:
        return dict(cached['constituents'])

    sector_codes = list(get_sector_code_names().keys())
    assembled = assemble_constituents(sector_codes)
    if assembled is not None:
        sector_names = get_sector_code_names()
        code_to_sector = build_code_to_sector_map(assembled, sector_names)
        save_sector_cache(assembled, sector_names, code_to_sector)
        return assembled

    constituents, sector_names = _fetch_sector_constituents_from_api(force_refresh=force_refresh)
    if constituents:
        code_to_sector = build_code_to_sector_map(constituents, sector_names)
        save_sector_cache(constituents, sector_names, code_to_sector)
    return constituents


def enrich_listing_with_sector(
    df: pd.DataFrame,
    *,
    sector_constituents: dict[str, list[str]] | None = None,
    force_refresh: bool = False,
    default: str = '기타',
) -> pd.DataFrame:
    """KRX 종목 목록에 Sector 열을 붙여 반환합니다."""
    if sector_constituents is not None:
        sector_map = build_code_to_sector_map(sector_constituents)
    else:
        sector_map = get_code_to_sector_map(force_refresh=force_refresh)
    return apply_sector_to_dataframe(df, sector_map, default=default)

