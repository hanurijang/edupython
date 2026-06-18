from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any

from app.config import Config
from app.services.cache import get_cached
from app.services.collectors.base import parse_index_date
from app.services.custom_cards import CUSTOMIZABLE_CATEGORIES, get_revision_token
from app.services.indicators import (
    CATEGORIES,
    KR_INDEX_IDS,
    get_indicators,
    _fetch_df,
    _round_num,
)

CATEGORY_LABELS = {item['id']: item['label'] for item in CATEGORIES}

MACRO_CATEGORIES = frozenset({'bonds', 'fx', 'commodities', 'crypto'})
MARKET_CATEGORIES = frozenset({'us_indices', 'kr_market', 'etf_kr', 'etf_us'})

COVERAGE_CATEGORY_ORDER = [
    'us_indices',
    'kr_market',
    'etf_kr',
    'etf_us',
    'bonds',
    'fx',
    'commodities',
    'crypto',
]

SIMULATION_SCOPES: dict[str, dict[str, str]] = {
    'cards': {
        'label': '카드 항목',
        'description': '채권 · 환율 · 원자재 · 코인 탭 카드만 비교 (지수·개별종목·ETF 제외)',
    },
    'all': {
        'label': '증시 포함',
        'description': '미국·한국 지수, 대표 종목·ETF, 사용자 추가 카드를 포함한 전체 비교',
    },
}


def normalize_scope(scope: str | None) -> str:
    if scope in SIMULATION_SCOPES:
        return scope
    return 'all'


def get_simulation_indicators(scope: str) -> list[dict[str, Any]]:
    scope = normalize_scope(scope)
    indicators = get_indicators()
    if scope == 'cards':
        return [item for item in indicators if item['category'] in MACRO_CATEGORIES]
    return indicators


def _coverage_item(indicator: dict[str, Any]) -> dict[str, str]:
    return {
        'id': indicator['id'],
        'name': indicator['name'],
        'symbol': indicator['symbol'],
    }


def _default_custom_subsections(category_id: str, indicators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    in_category = [item for item in indicators if item['category'] == category_id]
    defaults = [_coverage_item(item) for item in in_category if item.get('is_default')]
    customs = [_coverage_item(item) for item in in_category if item.get('is_custom')]
    subsections: list[dict[str, Any]] = []
    if defaults:
        subsections.append({'label': '기본 설정', 'count': len(defaults), 'items': defaults})
    if customs:
        subsections.append({'label': '사용자 추가', 'count': len(customs), 'items': customs})
    return subsections


def get_simulation_coverage(scope: str) -> dict[str, Any]:
    scope = normalize_scope(scope)
    indicators = get_simulation_indicators(scope)
    by_category: dict[str, list[dict[str, str]]] = {}
    for indicator in indicators:
        by_category.setdefault(indicator['category'], []).append(_coverage_item(indicator))

    groups: list[dict[str, Any]] = []
    for category_id in COVERAGE_CATEGORY_ORDER:
        items = by_category.get(category_id)
        if not items:
            continue
        group: dict[str, Any] = {
            'id': category_id,
            'label': CATEGORY_LABELS.get(category_id, category_id),
            'count': len(items),
            'items': items,
        }
        if category_id == 'fx':
            krw = [
                _coverage_item(item)
                for item in indicators
                if item['category'] == 'fx' and item.get('fx_group') == 'krw'
            ]
            reference = [
                _coverage_item(item)
                for item in indicators
                if item['category'] == 'fx' and item.get('fx_group') == 'reference'
            ]
            group['subsections'] = [
                {'label': 'KRW 직접 환율', 'count': len(krw), 'items': krw},
                {'label': '참조 환율', 'count': len(reference), 'items': reference},
            ]
        elif category_id == 'kr_market':
            indices = [
                _coverage_item(item)
                for item in indicators
                if item['category'] == 'kr_market' and item['id'] in KR_INDEX_IDS
            ]
            stocks_default = [
                _coverage_item(item)
                for item in indicators
                if item['category'] == 'kr_market' and item.get('is_default') and item['id'] not in KR_INDEX_IDS
            ]
            stocks_custom = [
                _coverage_item(item)
                for item in indicators
                if item['category'] == 'kr_market' and item.get('is_custom')
            ]
            subsections = []
            if indices:
                subsections.append({'label': '지수', 'count': len(indices), 'items': indices})
            if stocks_default:
                subsections.append({'label': '기본 설정', 'count': len(stocks_default), 'items': stocks_default})
            if stocks_custom:
                subsections.append({'label': '사용자 추가', 'count': len(stocks_custom), 'items': stocks_custom})
            group['subsections'] = subsections
        elif category_id in CUSTOMIZABLE_CATEGORIES:
            group['subsections'] = _default_custom_subsections(category_id, indicators)
        groups.append(group)

    if scope == 'cards':
        excluded_note = '미국·한국 지수, 대표 종목·ETF, 사용자 추가 카드는 포함하지 않습니다.'
    else:
        excluded_note = (
            'ETF/KR·KRX 전체 상장 목록은 포함하지 않습니다. '
            '한국 증시·ETF 탭의 기본 카드와 사용자가 추가한 카드만 비교합니다.'
        )

    return {
        'scope': scope,
        'scope_label': SIMULATION_SCOPES[scope]['label'],
        'description': SIMULATION_SCOPES[scope]['description'],
        'total_count': len(indicators),
        'groups': groups,
        'excluded_note': excluded_note,
    }


def default_start_date() -> str:
    return (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')


def validate_start_date(start_date: str) -> str | None:
    try:
        parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
    except ValueError:
        return '날짜 형식은 YYYY-MM-DD 입니다.'

    today = datetime.now().date()
    if parsed >= today:
        return '시작일은 오늘 이전이어야 합니다.'
    return None


def _compute_return(indicator: dict[str, Any], start_date: str) -> dict[str, Any] | None:
    end = datetime.now().strftime('%Y-%m-%d')
    try:
        df = _fetch_df(indicator, start_date, end)
    except Exception:
        return None

    if df.empty or 'Close' not in df.columns:
        return None

    start_price = float(df.iloc[0]['Close'])
    end_price = float(df.iloc[-1]['Close'])
    if not start_price:
        return None

    return_pct = (end_price - start_price) / start_price * 100.0
    return {
        'id': indicator['id'],
        'name': indicator['name'],
        'category': indicator['category'],
        'category_label': CATEGORY_LABELS.get(indicator['category'], indicator['category']),
        'start_date': parse_index_date(df.index[0]),
        'end_date': parse_index_date(df.index[-1]),
        'start_price': _round_num(start_price, indicator.get('decimals', 2)),
        'end_price': _round_num(end_price, indicator.get('decimals', 2)),
        'return_pct': _round_num(return_pct, 2),
        'direction': 'up' if return_pct > 0 else 'down' if return_pct < 0 else 'flat',
    }


def run_simulation(
    start_date: str,
    *,
    scope: str = 'all',
    force_refresh: bool = False,
) -> dict[str, Any]:
    scope = normalize_scope(scope)
    error = validate_start_date(start_date)
    if error:
        return {'error': error, 'start_date': start_date, 'scope': scope}

    indicators = get_simulation_indicators(scope)
    coverage = get_simulation_coverage(scope)
    ttl = 0 if force_refresh else Config.SERIES_TTL_SEC
    revision = get_revision_token()
    cache_key = f'simulation:{scope}:{start_date}:{revision}'

    def loader() -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(_compute_return, indicator, start_date)
                for indicator in indicators
            ]
            for future in as_completed(futures):
                item = future.result()
                if item is not None:
                    results.append(item)

        ranked = sorted(results, key=lambda row: row['return_pct'], reverse=True)
        bottom = sorted(results, key=lambda row: row['return_pct'])
        return {
            'scope': scope,
            'scope_label': SIMULATION_SCOPES[scope]['label'],
            'scope_description': SIMULATION_SCOPES[scope]['description'],
            'coverage': coverage,
            'start_date': start_date,
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'total_assets': len(indicators),
            'evaluated': len(ranked),
            'skipped': len(indicators) - len(ranked),
            'top3': ranked[:3],
            'bottom3': bottom[:3],
            'all': ranked,
        }

    if ttl == 0:
        payload = loader()
    else:
        payload = get_cached(cache_key, ttl, loader)

    if 'error' not in payload:
        payload['start_date'] = start_date
        payload['scope'] = scope
        payload['coverage'] = coverage
    return payload
