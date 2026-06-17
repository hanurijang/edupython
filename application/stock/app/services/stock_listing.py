import FinanceDataReader as fdr
import pandas as pd

from app.services.listing_cache import (
    get_cache_info,
    is_cached_market,
    load_listing,
    save_listing,
)

MARKET_GROUPS = {
    'KRX': ['KRX'],
    'ETF/KR': ['ETF/KR'],
    '미국': ['NASDAQ', 'NYSE', 'AMEX', 'S&P500'],
    '해외': ['SSE', 'SZSE', 'HKEX', 'TSE', 'HOSE'],
}

SUPPORTED_MARKETS = [code for codes in MARKET_GROUPS.values() for code in codes]

DEFAULT_MARKET = 'KRX'

MARKET_LABELS = {
    'KRX': '한국거래소 전체',
    'ETF/KR': '한국 ETF',
    'NASDAQ': '나스닥',
    'NYSE': '뉴욕증권거래소',
    'AMEX': '아멕스',
    'SSE': '상하이증권거래소',
    'SZSE': '선전증권거래소',
    'HKEX': '홍콩증권거래소',
    'TSE': '도쿄증권거래소',
    'HOSE': '호치민증권거래소',
    'S&P500': '미국 S&P 500',
}

# 시장별 테이블 표시 컬럼 (원본 데이터는 유지, 화면/API 목록만 정리)
MARKET_TABLE_COLUMNS = {
    'KRX': [
        'Name',
        'Close',
        'Changes',
        'ChagesRatio',
        'Open',
        'High',
        'Low',
        'Volume',
        'Amount',
        'Marcap',
        'Marcap_비중(%)',
        'Sector',
    ],
}

# 원본 컬럼 → 시가총액 비중(%) (해당 컬럼이 있을 때만 추가)
SHARE_COLUMN_MAP = {
    'Marcap': 'Marcap_비중(%)',
    'MarCap': 'MarCap_비중(%)',
}

COLUMN_LABELS = {
    'Code': '종목코드',
    'Symbol': '심볼',
    'ISU_CD': 'ISIN',
    'Name': '종목명',
    'Market': '시장',
    'Dept': '소속부',
    'Close': '종가',
    'Price': '현재가',
    'ChangeCode': '등락구분코드',
    'Changes': '전일비',
    'ChagesRatio': '등락률',
    'Change': '전일비',
    'ChangeRate': '등락률',
    'RiseFall': '등락구분',
    'Open': '시가',
    'High': '고가',
    'Low': '저가',
    'Volume': '거래량',
    'Amount': '거래대금(억원)',
    'Marcap': '시가총액(억원)',
    'MarCap': '시가총액(억원)',
    'Marcap_비중(%)': '시가총액 비중(%)',
    'MarCap_비중(%)': '시가총액 비중(%)',
    'Stocks': '상장주식수',
    'MarketId': '시장코드',
    'Category': '카테고리',
    'NAV': 'NAV',
    'EarningRate': '수익률',
    'IndustryCode': '산업코드',
    'Industry': '산업',
    'Sector': '섹터',
    'Adj Close': '수정종가',
    'Date': '일자',
}


EOK_WON_COLUMNS = frozenset({'Amount', 'Marcap', 'MarCap'})
EOK_WON_DIVISOR = 100_000_000

DECIMAL_COLUMNS = {
    'ChagesRatio': 2,
    'ChangeRate': 2,
    'EarningRate': 2,
    'Marcap_비중(%)': 2,
    'MarCap_비중(%)': 2,
}

TEXT_COLUMNS = frozenset({
    'Name', 'Industry', 'Sector', 'Market', 'Dept', 'Category', 'Symbol', 'Code',
})


def is_numeric_column(column: str) -> bool:
    return column not in TEXT_COLUMNS


def _is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return bool(pd.isna(value))


def format_number(value, *, decimals: int | None = None) -> str | None:
    """숫자를 세 자리마다 쉼표가 들어간 문자열로 반환합니다."""
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        return str(value)
    if not isinstance(value, (int, float)):
        return str(value)

    num = float(value)
    if decimals is None:
        if num == int(num):
            return f'{int(num):,}'
        decimals = 2

    text = f'{num:,.{decimals}f}'
    if decimals > 0:
        text = text.rstrip('0').rstrip('.')
    return text


def to_eok_won(value, column: str, market: str) -> float | None:
    """원/백만원 등 원본 값을 억원 단위 숫자로 변환합니다."""
    if _is_missing(value):
        return None

    amount = float(value)
    if market == 'ETF/KR':
        if column == 'Amount':
            return amount / 100
        if column in ('MarCap', 'Marcap'):
            return amount
    return amount / EOK_WON_DIVISOR


def format_eok_won(value, column: str, market: str) -> str:
    """억원 단위 표시 문자열을 반환합니다."""
    eok = to_eok_won(value, column, market)
    if eok is None:
        return '-'
    return format_number(eok, decimals=2) or '-'


def format_cell_display(value, column: str, market: str):
    """테이블 셀 표시용 포맷."""
    if column in EOK_WON_COLUMNS:
        return format_eok_won(value, column, market)
    if _is_missing(value):
        return ''
    if isinstance(value, (int, float)):
        decimals = DECIMAL_COLUMNS.get(column)
        return format_number(value, decimals=decimals) or ''
    return value


def get_column_label(column: str) -> str:
    return COLUMN_LABELS.get(column, column)


def get_column_labels(columns: list[str]) -> dict[str, str]:
    return {column: get_column_label(column) for column in columns}


def get_table_columns(market: str, df: pd.DataFrame) -> list[str]:
    """테이블/API 표시용 컬럼 목록을 반환합니다."""
    if market in MARKET_TABLE_COLUMNS:
        return [col for col in MARKET_TABLE_COLUMNS[market] if col in df.columns]
    return df.columns.tolist()


def get_table_listing(market: str, df: pd.DataFrame) -> pd.DataFrame:
    """테이블 표시용으로 컬럼을 정리한 DataFrame을 반환합니다."""
    columns = get_table_columns(market, df)
    return df[columns]


ROW_MARKET_COLUMN = 'Market'


def get_row_market_filter(df: pd.DataFrame) -> tuple[str | None, list[dict]]:
    """행 필터용 Market 컬럼과 체크박스 옵션을 반환합니다."""
    if ROW_MARKET_COLUMN not in df.columns:
        return None, []

    counts = df[ROW_MARKET_COLUMN].astype(str).value_counts()
    options = [
        {'value': name, 'count': int(counts[name])}
        for name in sorted(counts.index.tolist())
    ]
    return ROW_MARKET_COLUMN, options


# KRX ChangeCode: 1=상승, 2=하락, 0/3=보합, 4=상한, 5=하한
CHANGE_CODE_CLASS = {
    '1': 'price-up',
    '2': 'price-down',
    '0': 'price-flat',
    '3': 'price-flat',
    '4': 'price-limit-up',
    '5': 'price-limit-down',
}

KRX_PRICE_COLUMNS = frozenset({
    'Close', 'Changes', 'ChagesRatio', 'Open', 'High', 'Low',
})
COMMON_PRICE_COLUMNS = frozenset({
    'Close', 'Price', 'Change', 'ChangeRate', 'Changes', 'ChagesRatio',
    'Open', 'High', 'Low',
})
CHANGE_VALUE_COLUMNS = ('Changes', 'Change')


def get_change_code_class(change_code) -> str:
    return CHANGE_CODE_CLASS.get(str(change_code), 'price-flat')


def get_change_value_class(change_value) -> str:
    try:
        value = float(change_value)
    except (TypeError, ValueError):
        return 'price-flat'
    if value > 0:
        return 'price-up'
    if value < 0:
        return 'price-down'
    return 'price-flat'


def get_price_columns(market: str, columns: list[str]) -> frozenset[str]:
    if market == 'KRX':
        return frozenset(col for col in columns if col in KRX_PRICE_COLUMNS)
    return frozenset(col for col in columns if col in COMMON_PRICE_COLUMNS)


def enrich_table_rows(
    market: str,
    df: pd.DataFrame,
    table_df: pd.DataFrame,
    symbol_column: str,
) -> list[dict]:
    """테이블 행에 ChangeCode·필터용 숨김 필드 등 메타데이터를 붙입니다."""
    rows = table_df.to_dict(orient='records')

    if market == 'KRX' and 'ChangeCode' in df.columns:
        for row, change_code in zip(rows, df['ChangeCode'].tolist()):
            row['_change_code'] = str(change_code)
    else:
        change_col = next((col for col in CHANGE_VALUE_COLUMNS if col in df.columns), None)
        if change_col:
            for row, change_val in zip(rows, pd.to_numeric(df[change_col], errors='coerce').tolist()):
                row['_change_value'] = change_val

    if ROW_MARKET_COLUMN in df.columns:
        for row, market_val in zip(rows, df[ROW_MARKET_COLUMN].astype(str).tolist()):
            row[ROW_MARKET_COLUMN] = market_val

    if symbol_column in df.columns:
        for row, symbol in zip(rows, df[symbol_column].astype(str).tolist()):
            row[symbol_column] = symbol

    return rows


def get_market_label(market: str) -> str:
    """시장 코드에 한글 설명을 붙인 표시명을 반환합니다."""
    desc = MARKET_LABELS.get(market, market)
    return f'{market} ({desc})'


def get_market_groups():
    """드롭다운용 시장 그룹 (name, markets[{code, label}])"""
    return [
        {
            'name': group_name,
            'markets': [{'code': code, 'label': get_market_label(code)} for code in codes],
        }
        for group_name, codes in MARKET_GROUPS.items()
    ]


def get_markets_with_labels():
    """평탄한 시장 목록 (API 호환)"""
    return [
        {'code': code, 'label': get_market_label(code), 'group': group_name}
        for group_name, codes in MARKET_GROUPS.items()
        for code in codes
    ]


def add_market_share_columns(df: pd.DataFrame) -> pd.DataFrame:
    """시장 내 시가총액 비중(%) 열을 추가합니다."""
    result = df.copy()

    for col, share_col in SHARE_COLUMN_MAP.items():
        if col not in result.columns:
            continue

        values = pd.to_numeric(result[col], errors='coerce').fillna(0)
        total = values.sum()
        if total <= 0:
            result[share_col] = 0.0
            continue

        result[share_col] = (values / total * 100).round(4)

    return result


def _apply_krx_sector(df: pd.DataFrame) -> pd.DataFrame:
    """KRX 종목 목록에 섹터 열을 붙입니다 (섹터 캐시 기준, 즉시)."""
    try:
        from app.services.index_constituents import apply_sector_to_dataframe, get_code_to_sector_map
        sector_map = get_code_to_sector_map()
        if not sector_map:
            if 'Sector' not in df.columns:
                df = df.copy()
                df['Sector'] = '기타'
            return df
        base = df.drop(columns=['Sector'], errors='ignore')
        return apply_sector_to_dataframe(base, sector_map)
    except Exception:
        if 'Sector' not in df.columns:
            df = df.copy()
            df['Sector'] = '기타'
        return df


def get_stock_listing(market: str, *, force_refresh: bool = False) -> pd.DataFrame:
    """FinanceDataReader StockListing으로 종목 목록을 조회합니다."""
    if market not in SUPPORTED_MARKETS:
        raise ValueError(
            f"지원하지 않는 market입니다: {market}. "
            f"사용 가능: {', '.join(SUPPORTED_MARKETS)}"
        )

    if is_cached_market(market) and not force_refresh:
        cached_df, _ = load_listing(market)
        if cached_df is not None:
            if market == 'KRX':
                return _apply_krx_sector(cached_df)
            return cached_df

    df = add_market_share_columns(fdr.StockListing(market))

    if market == 'KRX':
        df = _apply_krx_sector(df)

    if is_cached_market(market):
        save_listing(market, df)

    return df


def get_stock_listing_meta(market: str) -> dict | None:
    """캐시 사용 시장의 캐시 메타정보를 반환합니다."""
    if is_cached_market(market):
        info = get_cache_info(market)
        if market == 'KRX' and info:
            from app.services.sector_cache import get_cache_info as get_sector_cache_info
            info = {**info, 'sector': get_sector_cache_info()}
        return info
    return None
