from flask import Blueprint, jsonify, render_template, request

from app.services.company_detail import get_company_detail, get_symbol_column, NAME_COLUMN
from app.services.index_constituents import (
    build_stock_index_map,
    get_index_constituents,
    get_index_coverage,
    get_krx_index_list,
    get_sector_indices,
    krx_login_configured,
)
from app.services.market_indices import get_market_indices
from app.services.portfolio_flow import get_portfolio_flow
from app.services.portfolio_performance import get_portfolio_performance
from app.services.stock_listing import (
    DEFAULT_MARKET,
    EOK_WON_COLUMNS,
    SUPPORTED_MARKETS,
    enrich_table_rows,
    format_cell_display,
    format_number,
    get_change_code_class,
    get_change_value_class,
    get_price_columns,
    is_numeric_column,
    get_column_label,
    get_column_labels,
    get_market_groups,
    get_market_label,
    get_stock_listing,
    get_stock_listing_meta,
    get_row_market_filter,
    get_table_listing,
)

bp = Blueprint('main', __name__)


def _force_refresh() -> bool:
    return request.args.get('refresh', '').lower() in ('1', 'true', 'yes')


@bp.route('/')
def index():
    market = request.args.get('market', DEFAULT_MARKET)
    if market not in SUPPORTED_MARKETS:
        market = DEFAULT_MARKET

    df = get_stock_listing(market, force_refresh=_force_refresh())
    table_df = get_table_listing(market, df)
    symbol_column = get_symbol_column(market)
    stocks = enrich_table_rows(market, df, table_df, symbol_column)
    row_market_column, market_options = get_row_market_filter(df)

    columns = table_df.columns.tolist()

    return render_template(
        'index.html',
        market_groups=get_market_groups(),
        current_market=market,
        current_market_label=get_market_label(market),
        stocks=stocks,
        columns=columns,
        get_column_label=get_column_label,
        format_cell_display=format_cell_display,
        format_number=format_number,
        is_numeric_column=is_numeric_column,
        eok_won_columns=EOK_WON_COLUMNS,
        symbol_column=symbol_column,
        name_column=NAME_COLUMN,
        row_market_column=row_market_column,
        market_options=market_options,
        price_columns=get_price_columns(market, columns),
        get_change_code_class=get_change_code_class,
        get_change_value_class=get_change_value_class,
        count=len(stocks),
        cache_info=get_stock_listing_meta(market),
        index_cards=get_market_indices(market),
    )


@bp.route('/api/markets')
def api_markets():
    return jsonify({'groups': get_market_groups()})


@bp.route('/api/stocks')
def api_stocks():
    market = request.args.get('market', DEFAULT_MARKET)
    try:
        df = get_stock_listing(market, force_refresh=_force_refresh())
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    table_df = get_table_listing(market, df)
    columns = table_df.columns.tolist()
    response = {
        'market': market,
        'count': len(df),
        'columns': columns,
        'column_labels': get_column_labels(columns),
        'data': table_df.to_dict(orient='records'),
    }
    cache_info = get_stock_listing_meta(market)
    if cache_info:
        response['cache'] = cache_info
    return jsonify(response)


@bp.route('/api/indices')
def api_indices():
    market = request.args.get('market', DEFAULT_MARKET)
    if market not in SUPPORTED_MARKETS:
        return jsonify({'error': f'지원하지 않는 market입니다: {market}'}), 400

    cards = get_market_indices(market, force_refresh=_force_refresh())
    return jsonify({'market': market, 'indices': cards})


@bp.route('/api/krx/indices')
def api_krx_index_list():
    df = get_krx_index_list()
    return jsonify({
        'count': len(df),
        'indices': df.to_dict(orient='records'),
    })


@bp.route('/api/krx/indices/coverage')
def api_krx_index_coverage():
    return jsonify(get_index_coverage())


@bp.route('/api/krx/indices/sectors')
def api_krx_sector_indices():
    df = get_sector_indices()
    return jsonify({
        'count': len(df),
        'login_configured': krx_login_configured(),
        'sectors': df.to_dict(orient='records'),
    })


@bp.route('/api/krx/indices/<code>/constituents')
def api_krx_index_constituents(code: str):
    try:
        return jsonify(get_index_constituents(code))
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@bp.route('/api/krx/indices/stock-map')
def api_krx_index_stock_map():
    raw_codes = request.args.get('codes', '').strip()
    codes = [item.strip() for item in raw_codes.split(',') if item.strip()] if raw_codes else None
    return jsonify(build_stock_index_map(codes))


@bp.route('/api/company')
def api_company():
    market = request.args.get('market', DEFAULT_MARKET)
    symbol = request.args.get('symbol', '').strip()

    if market not in SUPPORTED_MARKETS:
        return jsonify({'error': f'지원하지 않는 market입니다: {market}'}), 400
    if not symbol:
        return jsonify({'error': 'symbol 파라미터가 필요합니다.'}), 400

    try:
        detail = get_company_detail(market, symbol)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 404

    return jsonify(detail)


@bp.route('/api/portfolio/performance', methods=['POST'])
def api_portfolio_performance():
    payload = request.get_json(silent=True) or {}
    holdings = payload.get('holdings', [])
    if not isinstance(holdings, list):
        return jsonify({'error': 'holdings는 배열이어야 합니다.'}), 400

    normalized = []
    for item in holdings:
        if not isinstance(item, dict):
            continue
        market = str(item.get('market', '')).strip()
        symbol = str(item.get('symbol', '')).strip()
        if not market or not symbol:
            continue
        if market not in SUPPORTED_MARKETS:
            continue
        try:
            weight = float(item.get('weight', 0))
        except (TypeError, ValueError):
            weight = 0.0
        normalized.append({
            'market': market,
            'symbol': symbol,
            'name': item.get('name'),
            'weight': weight,
        })

    return jsonify(get_portfolio_performance(normalized))


@bp.route('/api/portfolio/flow', methods=['POST'])
def api_portfolio_flow():
    payload = request.get_json(silent=True) or {}
    holdings = payload.get('holdings', [])
    if not isinstance(holdings, list):
        return jsonify({'error': 'holdings는 배열이어야 합니다.'}), 400

    raw_days = payload.get('days', 0)
    if isinstance(raw_days, str) and raw_days.lower() in ('max', 'all', 'full'):
        days = 0
    else:
        try:
            days = int(raw_days)
        except (TypeError, ValueError):
            days = 0

    normalized = []
    for item in holdings:
        if not isinstance(item, dict):
            continue
        market = str(item.get('market', '')).strip()
        symbol = str(item.get('symbol', '')).strip()
        if not market or not symbol:
            continue
        if market not in SUPPORTED_MARKETS:
            continue
        normalized.append({
            'market': market,
            'symbol': symbol,
            'name': item.get('name'),
            'weight': item.get('weight', 0),
        })

    return jsonify(get_portfolio_flow(normalized, days=days))
