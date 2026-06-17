from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import FinanceDataReader as fdr
import pandas as pd
from app.services.stock_listing import get_stock_listing
from app.services.company_detail import get_symbol_column

INDEX_CACHE_TTL = timedelta(seconds=60)
_index_cache: dict[str, tuple[datetime, list[dict]]] = {}

SESSION_LABELS = {
    'open': '장중',
    'closed': '장마감',
    'pre': '프리마켓',
    'after': '애프터마켓',
    'holiday': '휴장',
}

US_INDICES = [
    {'symbol': 'US500', 'name': 'S&P 500'},
    {'symbol': 'IXIC', 'name': '나스닥'},
    {'symbol': 'DJI', 'name': '다우존스'},
]

KR_INDICES = [
    {'symbol': 'KS11', 'name': '코스피'},
    {'symbol': 'KQ11', 'name': '코스닥'},
]

MARKET_INDEX_CONFIG: dict[str, list[dict]] = {
    'KRX': [{**item, 'session': 'kr'} for item in KR_INDICES],
    'ETF/KR': [{**item, 'session': 'kr'} for item in KR_INDICES],
    'NASDAQ': [{**item, 'session': 'us'} for item in US_INDICES],
    'NYSE': [{**item, 'session': 'us'} for item in US_INDICES],
    'AMEX': [{**item, 'session': 'us'} for item in US_INDICES],
    'S&P500': [{**item, 'session': 'us'} for item in US_INDICES],
    'SSE': [{'symbol': 'SSEC', 'name': '상해종합', 'session': 'cn'}],
    'SZSE': [{'symbol': 'SZSE:399001', 'name': '심천성분', 'session': 'cn'}],
    'HKEX': [{'symbol': 'HSI', 'name': '항셍', 'session': 'hk'}],
    'TSE': [{'symbol': 'N225', 'name': '니케이 225', 'session': 'jp'}],
}


def _is_weekday(dt: datetime) -> bool:
    return dt.weekday() < 5


def get_session_status(session: str, now: datetime | None = None) -> dict:
    """시장 세션 상태를 반환합니다."""
    if session == 'kr':
        now = now or datetime.now(ZoneInfo('Asia/Seoul'))
        if not _is_weekday(now):
            return {'code': 'holiday', 'label': SESSION_LABELS['holiday']}

        current = now.time()
        if time(9, 0) <= current < time(15, 30):
            return {'code': 'open', 'label': SESSION_LABELS['open']}
        if time(8, 0) <= current < time(9, 0):
            return {'code': 'pre', 'label': '장 시작 전'}
        if current >= time(15, 30):
            return {'code': 'closed', 'label': SESSION_LABELS['closed']}
        return {'code': 'closed', 'label': SESSION_LABELS['closed']}

    if session == 'us':
        now = now or datetime.now(ZoneInfo('America/New_York'))
        if not _is_weekday(now):
            return {'code': 'holiday', 'label': SESSION_LABELS['holiday']}

        current = now.time()
        if time(9, 30) <= current < time(16, 0):
            return {'code': 'open', 'label': SESSION_LABELS['open']}
        if time(4, 0) <= current < time(9, 30):
            return {'code': 'pre', 'label': SESSION_LABELS['pre']}
        if time(16, 0) <= current < time(20, 0):
            return {'code': 'after', 'label': SESSION_LABELS['after']}
        return {'code': 'closed', 'label': SESSION_LABELS['closed']}

    if session == 'jp':
        now = now or datetime.now(ZoneInfo('Asia/Tokyo'))
        if not _is_weekday(now):
            return {'code': 'holiday', 'label': SESSION_LABELS['holiday']}
        current = now.time()
        if (time(9, 0) <= current < time(11, 30)) or (time(12, 30) <= current < time(15, 0)):
            return {'code': 'open', 'label': SESSION_LABELS['open']}
        if time(8, 0) <= current < time(9, 0):
            return {'code': 'pre', 'label': '장 시작 전'}
        return {'code': 'closed', 'label': SESSION_LABELS['closed']}

    if session == 'hk':
        now = now or datetime.now(ZoneInfo('Asia/Hong_Kong'))
        if not _is_weekday(now):
            return {'code': 'holiday', 'label': SESSION_LABELS['holiday']}
        current = now.time()
        if (time(9, 30) <= current < time(12, 0)) or (time(13, 0) <= current < time(16, 0)):
            return {'code': 'open', 'label': SESSION_LABELS['open']}
        return {'code': 'closed', 'label': SESSION_LABELS['closed']}

    if session == 'cn':
        now = now or datetime.now(ZoneInfo('Asia/Shanghai'))
        if not _is_weekday(now):
            return {'code': 'holiday', 'label': SESSION_LABELS['holiday']}
        current = now.time()
        if (time(9, 30) <= current < time(11, 30)) or (time(13, 0) <= current < time(15, 0)):
            return {'code': 'open', 'label': SESSION_LABELS['open']}
        return {'code': 'closed', 'label': SESSION_LABELS['closed']}

    return {'code': 'closed', 'label': SESSION_LABELS['closed']}


def _round_num(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _direction(change: float) -> str:
    if change > 0:
        return 'up'
    if change < 0:
        return 'down'
    return 'flat'


def _parse_index_date(value) -> str:
    if isinstance(value, pd.Timestamp):
        return value.strftime('%Y-%m-%d')
    return str(value)[:10]


def _fetch_krx_style_index(symbol: str, name: str, session: str) -> dict | None:
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    df = fdr.DataReader(symbol, start, end)
    if df.empty or 'Close' not in df.columns:
        return None

    df = df.dropna(subset=['Close']).sort_index()
    if df.empty:
        return None

    row = df.iloc[-1]
    close = float(row['Close'])
    if 'Comp' in df.columns and pd.notna(row.get('Comp')):
        change = float(row['Comp'])
    else:
        change = close - float(df.iloc[-2]['Close']) if len(df) > 1 else 0.0

    if 'Change' in df.columns and pd.notna(row.get('Change')):
        raw = float(row['Change'])
        change_pct = raw * 100 if abs(raw) < 1 else raw
    elif len(df) > 1:
        prev_close = float(df.iloc[-2]['Close'])
        change_pct = (change / prev_close * 100) if prev_close else 0.0
    else:
        change_pct = 0.0

    if 'UpDown' in df.columns and pd.notna(row.get('UpDown')):
        updown = str(int(row['UpDown']))
        direction = 'up' if updown == '1' else 'down' if updown == '2' else 'flat'
    else:
        direction = _direction(change)

    return {
        'name': name,
        'symbol': symbol,
        'close': _round_num(close, 2),
        'change': _round_num(change, 2),
        'change_pct': _round_num(change_pct, 2),
        'direction': direction,
        'date': _parse_index_date(df.index[-1]),
        'session': get_session_status(session),
    }


def _fetch_yahoo_style_index(symbol: str, name: str, session: str) -> dict | None:
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    df = fdr.DataReader(symbol, start, end)
    if df.empty or 'Close' not in df.columns:
        return None

    df = df.dropna(subset=['Close']).sort_index()
    if df.empty:
        return None

    row = df.iloc[-1]
    close = float(row['Close'])
    if len(df) > 1:
        prev_close = float(df.iloc[-2]['Close'])
        change = close - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
    else:
        change = 0.0
        change_pct = 0.0

    return {
        'name': name,
        'symbol': symbol,
        'close': _round_num(close, 2),
        'change': _round_num(change, 2),
        'change_pct': _round_num(change_pct, 2),
        'direction': _direction(change),
        'date': _parse_index_date(df.index[-1]),
        'session': get_session_status(session),
    }


def _fetch_index_card(config: dict) -> dict | None:
    symbol = config['symbol']
    name = config['name']
    session = config['session']

    try:
        if session == 'kr':
            return _fetch_krx_style_index(symbol, name, session)
        return _fetch_yahoo_style_index(symbol, name, session)
    except Exception:
        return None


def _to_number_series(df: pd.DataFrame, column: str) -> pd.Series | None:
    if column not in df.columns:
        return None
    return pd.to_numeric(df[column], errors='coerce')


def _compute_market_stats(market: str) -> list[dict]:
    """시장 요약 카드(상승/하락/거래량/상·하한)를 생성합니다."""
    try:
        df = get_stock_listing(market)
    except Exception:
        return []

    if df.empty:
        return []

    total_volume = 0
    volume_series = _to_number_series(df, 'Volume')
    if volume_series is not None:
        total_volume = int(volume_series.fillna(0).sum())

    up_count = 0
    down_count = 0
    limit_up_count = 0
    limit_down_count = 0

    if 'ChangeCode' in df.columns:
        codes = df['ChangeCode'].astype(str)
        up_count = int(codes.eq('1').sum())
        down_count = int(codes.eq('2').sum())
        limit_up_count = int(codes.eq('4').sum())
        limit_down_count = int(codes.eq('5').sum())
    else:
        change_col = None
        for col in ('Changes', 'Change'):
            if col in df.columns:
                change_col = col
                break
        if change_col:
            changes = pd.to_numeric(df[change_col], errors='coerce').fillna(0)
            up_count = int(changes.gt(0).sum())
            down_count = int(changes.lt(0).sum())

    symbol_column = get_symbol_column(market)
    if symbol_column not in df.columns:
        symbol_column = 'Symbol' if 'Symbol' in df.columns else None

    def _limit_items(target_code: str) -> list[dict]:
        if 'ChangeCode' not in df.columns:
            return []
        subset = df[df['ChangeCode'].astype(str) == target_code]
        if subset.empty:
            return []
        items: list[dict] = []
        for _, row in subset.iterrows():
            symbol_val = row.get(symbol_column) if symbol_column else None
            name_val = row.get('Name')
            if pd.isna(symbol_val) or pd.isna(name_val):
                continue
            items.append({
                'symbol': str(symbol_val),
                'name': str(name_val),
            })
        return items

    limit_up_items = _limit_items('4')
    limit_down_items = _limit_items('5')

    volume_million = total_volume / 1_000_000

    stats = [
        {
            'card_type': 'market_stat',
            'name': '상승 + 상한가',
            'value': f'{up_count + limit_up_count:,}',
            'subvalue': f'상승 {up_count:,}종목 · 상한가 {limit_up_count:,}종목',
            'direction': 'up' if (up_count + limit_up_count) > 0 else 'flat',
            'metric_key': 'limit_up',
            'items': limit_up_items,
        },
        {
            'card_type': 'market_stat',
            'name': '하락 + 하한가',
            'value': f'{down_count + limit_down_count:,}',
            'subvalue': f'하락 {down_count:,}종목 · 하한가 {limit_down_count:,}종목',
            'direction': 'down' if (down_count + limit_down_count) > 0 else 'flat',
            'metric_key': 'limit_down',
            'items': limit_down_items,
        },
        {
            'card_type': 'market_stat',
            'name': '총 거래량',
            'value': f'{volume_million:,.2f}M',
            'subvalue': '당일 누적 거래량 (백만주)',
            'direction': 'flat',
            'metric_key': 'total_volume',
        },
    ]

    # 시가총액 기준 상위 N개 종목 평균 등락률
    change_col = next((col for col in ('ChagesRatio', 'ChangeRate') if col in df.columns), None)
    marcap_col = next((col for col in ('Marcap', 'MarCap') if col in df.columns), None)

    if change_col and marcap_col:
        ranked = df.copy()
        ranked['_change'] = pd.to_numeric(ranked[change_col], errors='coerce')
        ranked['_marcap'] = pd.to_numeric(ranked[marcap_col], errors='coerce')
        ranked = ranked.dropna(subset=['_change', '_marcap']).sort_values('_marcap', ascending=False)

        top_return_values: list[tuple[int, float]] = []
        for top_n in (10, 30, 50, 100):
            sample = ranked.head(top_n)
            if sample.empty:
                continue
            avg_change = float(sample['_change'].mean())
            top_return_values.append((top_n, avg_change))

        if top_return_values:
            merged_avg = sum(v for _, v in top_return_values) / len(top_return_values)
            stats.append({
                'card_type': 'market_stat',
                'name': '상위 평균 수익 (10/30/50/100)',
                'value': f'{merged_avg:+.2f}%',
                'subvalue': '시가총액 상위 N개 평균 등락률',
                'direction': _direction(merged_avg),
                'metric_key': 'top_avg_returns',
                'breakdown': [
                    {'label': f'TOP {n}', 'value': f'{v:+.2f}%', 'direction': _direction(v)}
                    for n, v in top_return_values
                ],
            })

    if market == 'KRX':
        sector_card = _compute_sector_avg_stats(df)
        if sector_card:
            stats.append(sector_card)

    return stats


def _compute_sector_avg_stats(df: pd.DataFrame) -> dict | None:
    """코스피 섹터별 평균 등락률 카드를 생성합니다."""
    if 'Sector' not in df.columns:
        return None

    change_col = next((col for col in ('ChagesRatio', 'ChangeRate') if col in df.columns), None)
    if not change_col:
        return None

    subset = df.copy()
    if 'Market' in subset.columns:
        subset = subset[subset['Market'].astype(str) == 'KOSPI']
    subset = subset[subset['Sector'].astype(str) != '기타']
    subset['_change'] = pd.to_numeric(subset[change_col], errors='coerce')
    subset = subset.dropna(subset=['_change', 'Sector'])
    if subset.empty:
        return None

    grouped = (
        subset.groupby('Sector', as_index=False)
        .agg(avg_change=('_change', 'mean'), count=('Code', 'count'))
        .sort_values('avg_change', ascending=False)
    )

    breakdown = [
        {
            'label': str(row.Sector),
            'value': f'{float(row.avg_change):+.2f}%',
            'direction': _direction(float(row.avg_change)),
            'count': int(row.count),
        }
        for row in grouped.itertuples()
    ]
    if not breakdown:
        return None

    overall = float(grouped['avg_change'].mean())
    best = breakdown[0]
    worst = breakdown[-1]

    return {
        'card_type': 'market_stat',
        'name': '섹터 평균 등락률',
        'value': f'{overall:+.2f}%',
        'subvalue': f'최고 {best["label"]} {best["value"]} · 최저 {worst["label"]} {worst["value"]}',
        'direction': _direction(overall),
        'metric_key': 'sector_avg_returns',
        'breakdown': breakdown,
    }


def get_market_indices(market: str, *, force_refresh: bool = False) -> list[dict]:
    """시장별 대표 지수 카드 데이터를 반환합니다."""
    configs = MARKET_INDEX_CONFIG.get(market, [])
    if not configs:
        return []

    if not force_refresh and market in _index_cache:
        fetched_at, cached = _index_cache[market]
        if datetime.now() - fetched_at < INDEX_CACHE_TTL:
            return cached

    cards = [card for cfg in configs if (card := _fetch_index_card(cfg))]
    for card in cards:
        card['card_type'] = 'index'

    cards.extend(_compute_market_stats(market))
    _index_cache[market] = (datetime.now(), cards)
    return cards
