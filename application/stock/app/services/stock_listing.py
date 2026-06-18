import re
from io import StringIO
from itertools import product

import FinanceDataReader as fdr
import pandas as pd
import requests
from bs4 import BeautifulSoup

from app.services.listing_cache import get_listing_meta, load_naver_listing, save_naver_listing

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


def _coerce_float(value) -> float | None:
    """쉼표·공백이 포함된 숫자 문자열도 변환합니다."""
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(',', '').strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value, *, decimals: int | None = None) -> str | None:
    """숫자를 세 자리마다 쉼표가 들어간 문자열로 반환합니다."""
    num = _coerce_float(value)
    if num is None:
        if _is_missing(value):
            return None
        return str(value)

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
    amount = _coerce_float(value)
    if amount is None:
        return None

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


def _parse_naver_number(value) -> float | None:
    """네이버 시세 표기(상승/하락, ▲▼, 쉼표)를 숫자로 변환합니다."""
    if _is_missing(value):
        return None
    text = str(value).strip()
    if not text or text in ('-', 'N/A'):
        return None
    if '하락' in text:
        sign = -1
    elif '상승' in text:
        sign = 1
    elif text.startswith('▼') or text.startswith('-'):
        sign = -1
    else:
        sign = 1
    cleaned = re.sub(r'[^\d.]', '', text.replace('▲', '').replace('▼', ''))
    if not cleaned:
        return None
    return sign * float(cleaned)


def _krx_change_code_from_ratio(ratio) -> str:
    """등락률(%) 기준 KRX ChangeCode: 1=상승, 2=하락, 3=보합, 4=상한, 5=하한."""
    if _is_missing(ratio):
        return '3'
    try:
        value = float(ratio)
    except (TypeError, ValueError):
        return '3'
    if value == 0:
        return '3'
    if value >= 29.5:
        return '4'
    if value <= -29.5:
        return '5'
    return '1' if value > 0 else '2'


def _normalize_krx_change_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Changes·ChangeCode를 등락률 부호에 맞게 정리합니다 (FDR/네이버 공통)."""
    if 'ChagesRatio' not in df.columns:
        return df

    result = df.copy()
    ratio = pd.to_numeric(result['ChagesRatio'], errors='coerce')
    result['ChangeCode'] = ratio.map(_krx_change_code_from_ratio)

    if 'Changes' in result.columns:
        abs_changes = pd.to_numeric(result['Changes'], errors='coerce').abs()
        sign = ratio.apply(lambda x: 0 if pd.isna(x) or x == 0 else (1 if x > 0 else -1))
        result['Changes'] = abs_changes * sign

    return result


def _finalize_krx_listing(df: pd.DataFrame) -> pd.DataFrame:
    return _apply_krx_sector(_normalize_krx_change_codes(df))


def _normalize_naver_krx_listing(raw: pd.DataFrame) -> pd.DataFrame:
    """네이버 marcap 스크랩 결과를 StockListing(KRX) 스키마에 맞춥니다."""
    market_map = {0: 'KOSPI', 1: 'KOSDAQ', '0': 'KOSPI', '1': 'KOSDAQ'}
    df = pd.DataFrame()
    df['Code'] = raw['종목코드'].astype(str).str.zfill(6)
    df['Name'] = raw['종목명'].astype(str)
    df['Market'] = raw['시장'].map(market_map).fillna('KOSPI')
    df['Close'] = pd.to_numeric(raw['현재가'], errors='coerce')
    df['Changes'] = raw['전일비'].map(_parse_naver_number)
    df['ChagesRatio'] = pd.to_numeric(raw['등락률'], errors='coerce') * 100
    df['Open'] = pd.to_numeric(raw['시가'], errors='coerce')
    df['High'] = pd.to_numeric(raw['고가'], errors='coerce')
    df['Low'] = pd.to_numeric(raw['저가'], errors='coerce')
    df['Volume'] = pd.to_numeric(raw['거래량'], errors='coerce')
    # 네이버 거래대금·시가총액: 백만원 / 억원 → 원 단위
    df['Amount'] = pd.to_numeric(raw['거래대금'], errors='coerce') * 1_000_000
    df['Marcap'] = pd.to_numeric(raw['시가총액'], errors='coerce') * 100_000_000
    df['Stocks'] = pd.to_numeric(raw['상장주식수'], errors='coerce') * 1_000

    df = df.dropna(subset=['Code', 'Close']).reset_index(drop=True)
    df.attrs = {'exchange': 'KRX', 'source': 'NAVER', 'data': 'LISTINGS'}
    return df


def _naver_marcap_page(sosok: int, page: int) -> pd.DataFrame:
    """네이버 시가총액 페이지에서 종목 시세를 읽습니다 (FDR snap 대체, FutureWarning 없음)."""
    url = f'https://finance.naver.com/sise/sise_market_sum.nhn?sosok={sosok}&page={page}'
    field_list = [
        ('12|06108810', ['N', '종목명', '현재가', '전일비', '등락률', '거래량', '거래대금', '시가총액']),
        ('12|01882048', ['시가']),
        ('12|00441424', ['고가']),
        ('12|00234202', ['저가', '상장주식수']),
    ]

    marcap = pd.DataFrame()
    html = ''
    for field_key, cols in field_list:
        html = requests.get(url, cookies={'field_list': field_key}, timeout=15).text
        table_df = pd.read_html(StringIO(html))[1]
        if table_df.empty:
            return marcap
        marcap[cols] = table_df[cols]

    soup = BeautifulSoup(html, 'lxml')
    table = soup.find_all('table')[1]
    codes = []
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        if len(tds) >= 2 and tds[1].a:
            codes.append(tds[1].a['href'].split('=')[1])
        else:
            codes.append(None)

    marcap.insert(0, '종목코드', codes)
    marcap['시장'] = sosok
    marcap['등락률'] = (
        marcap['등락률'].astype(str).str.replace('%', '', regex=False).str.replace(',', '', regex=False)
        .replace('', pd.NA).astype(float) / 100.0
    )
    marcap.dropna(how='all', inplace=True)
    return marcap.reset_index(drop=True)


def _fetch_krx_listing_live() -> pd.DataFrame:
    """네이버 금융에서 KRX 전 종목 시세를 조회합니다 (장중 실시간 반영)."""
    pages = list(product([0], range(1, 32 + 1))) + list(product([1], range(1, 29 + 1)))
    frames: list[pd.DataFrame] = []
    for sosok, page in pages:
        page_df = _naver_marcap_page(sosok, page)
        if page_df.empty:
            continue
        frames.append(page_df)

    if not frames:
        raise ValueError('네이버 시세 조회 결과가 없습니다.')

    return _normalize_naver_krx_listing(pd.concat(frames, ignore_index=True))


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
    """종목 목록을 조회합니다.

    - KRX 일반 조회: FDR 스냅샷(빠름, 캐시 없음). 실시간 갱신 후 저장된 네이버 목록이 있으면 우선 사용.
    - KRX 실시간 갱신: 네이버 전 종목 조회(~1분) 후 저장.
    - 해외 시장: FDR 직접 조회(캐시 없음).
    """
    if market not in SUPPORTED_MARKETS:
        raise ValueError(
            f"지원하지 않는 market입니다: {market}. "
            f"사용 가능: {', '.join(SUPPORTED_MARKETS)}"
        )

    if market == 'KRX':
        if force_refresh:
            df = add_market_share_columns(_fetch_krx_listing_live())
            df = _finalize_krx_listing(df)
            save_naver_listing(market, df)
            return df

        cached = load_naver_listing(market)
        if cached is not None:
            return _finalize_krx_listing(cached)

        df = add_market_share_columns(fdr.StockListing(market))
        return _finalize_krx_listing(df)

    return add_market_share_columns(fdr.StockListing(market))


def get_stock_listing_meta(market: str) -> dict | None:
    """목록 메타정보 (KRX 네이버 실시간 저장분·섹터 캐시)."""
    if market != 'KRX':
        return None
    from app.services.sector_cache import get_cache_info as get_sector_cache_info

    info = get_listing_meta(market) or {'cached': False, 'data_source': 'fdr', 'storage': None}
    return {**info, 'sector': get_sector_cache_info()}
