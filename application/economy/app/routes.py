from flask import Blueprint, jsonify, render_template, request, url_for

from datetime import datetime, timedelta

from app.config import Config
from app.services.analytics import compare_favorites, correlation_favorites
from app.services.cache import clear_cache
from app.services.chart_builder import (
    build_compare_chart,
    build_correlation_heatmap,
    build_line_chart,
)
from app.services.indicators import (
    get_categories,
    get_indicator,
    get_indicator_snapshot,
    get_series,
    get_snapshots,
    list_indicators,
)
from app.services.simulation import (
    default_start_date,
    get_simulation_coverage,
    normalize_scope,
    run_simulation,
)
from app.services.custom_cards import (
    CUSTOMIZABLE_CATEGORIES,
    add_custom_card,
    load_custom_entries,
    remove_custom_card,
)
from app.services.listing_search import search_category_listings
from app.services.watchlist import (
    add_favorite,
    get_favorite_snapshots,
    load_favorites,
    remove_favorite,
)

bp = Blueprint('main', __name__)

FAVORITES_CATEGORY = 'favorites'
SIMULATION_CATEGORY = 'simulation'


def _dashboard_categories(favorite_count: int) -> list[dict[str, str]]:
    categories = get_categories()
    return [
        *[{**item, 'kind': 'indicator'} for item in categories],
        {
            'id': FAVORITES_CATEGORY,
            'label': '즐겨찾기',
            'kind': 'tool',
            'tool': 'favorites',
            'count': favorite_count,
        },
        {
            'id': SIMULATION_CATEGORY,
            'label': '시뮬레이션',
            'kind': 'tool',
            'tool': 'simulation',
        },
    ]


def format_number(value, decimals: int = 2) -> str:
    if value is None:
        return '-'
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if decimals == 0:
        return f'{num:,.0f}'
    return f'{num:,.{decimals}f}'


def _force_refresh() -> bool:
    return request.args.get('refresh', '').lower() in ('1', 'true', 'yes')


@bp.route('/')
def dashboard():
    category = request.args.get('category', Config.DEFAULT_CATEGORY)
    favorite_ids = load_favorites()
    categories = _dashboard_categories(len(favorite_ids))
    valid_ids = {item['id'] for item in categories}
    if category not in valid_ids:
        category = Config.DEFAULT_CATEGORY

    refresh = _force_refresh()
    simulation_start_date = request.args.get('start_date', default_start_date())
    simulation_scope = normalize_scope(request.args.get('scope'))
    simulation_max_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    simulation_coverage = get_simulation_coverage(simulation_scope)

    if category == FAVORITES_CATEGORY:
        cards = get_favorite_snapshots(force_refresh=refresh)
    elif category == SIMULATION_CATEGORY:
        cards = []
    else:
        cards = get_snapshots(category, force_refresh=refresh)

    if refresh:
        from flask import redirect

        return redirect(url_for('main.dashboard', category=category))

    return render_template(
        'dashboard.html',
        categories=categories,
        current_category=category,
        cards=cards,
        favorite_ids=favorite_ids,
        simulation_start_date=simulation_start_date,
        simulation_scope=simulation_scope,
        simulation_max_date=simulation_max_date,
        simulation_coverage=simulation_coverage,
        customizable_categories=sorted(CUSTOMIZABLE_CATEGORIES),
        format_number=format_number,
    )


@bp.route('/api/categories')
def api_categories():
    return jsonify(_dashboard_categories(len(load_favorites())))


@bp.route('/api/indicators')
def api_indicators():
    category = request.args.get('category', Config.DEFAULT_CATEGORY)
    if category == FAVORITES_CATEGORY:
        cards = get_favorite_snapshots(force_refresh=_force_refresh())
    else:
        cards = get_snapshots(category, force_refresh=_force_refresh())
    return jsonify({'category': category, 'indicators': cards})


@bp.route('/api/series/<indicator_id>')
def api_series(indicator_id: str):
    period = request.args.get('period', '1y')
    try:
        payload = get_series(indicator_id, period, force_refresh=_force_refresh())
    except KeyError:
        return jsonify({'error': '지표를 찾을 수 없습니다.'}), 404
    return jsonify(payload)


@bp.route('/api/chart/<indicator_id>')
def api_chart(indicator_id: str):
    period = request.args.get('period', '1y')
    indicator = get_indicator(indicator_id)
    if indicator is None:
        return jsonify({'error': '지표를 찾을 수 없습니다.'}), 404

    try:
        series = get_series(indicator_id, period, force_refresh=_force_refresh())
    except KeyError:
        return jsonify({'error': '지표를 찾을 수 없습니다.'}), 404

    chart = build_line_chart(
        series.get('points', []),
        name=indicator['name'],
        unit=indicator.get('unit', ''),
    )
    return jsonify({'chart': chart, 'series': series})


@bp.route('/api/favorites', methods=['GET'])
def api_favorites_list():
    ids = load_favorites()
    cards = get_favorite_snapshots(force_refresh=_force_refresh())
    return jsonify({'ids': ids, 'indicators': cards})


@bp.route('/api/favorites', methods=['POST'])
def api_favorites_add():
    payload = request.get_json(silent=True) or {}
    indicator_id = payload.get('id') or request.form.get('id')
    if not indicator_id:
        return jsonify({'error': 'id가 필요합니다.'}), 400
    if get_indicator(indicator_id) is None:
        return jsonify({'error': '지표를 찾을 수 없습니다.'}), 404

    ids = add_favorite(indicator_id)
    return jsonify({'ids': ids, 'added': indicator_id})


@bp.route('/api/favorites/<indicator_id>', methods=['DELETE'])
def api_favorites_remove(indicator_id: str):
    ids = remove_favorite(indicator_id)
    return jsonify({'ids': ids, 'removed': indicator_id})


@bp.route('/api/favorites/compare')
def api_favorites_compare():
    period = request.args.get('period', '1y')
    ids = load_favorites()
    if len(ids) < 1:
        return jsonify({'error': '즐겨찾기가 비어 있습니다.', 'series': []}), 400

    payload = compare_favorites(ids, period)
    chart = build_compare_chart(payload.get('series', []))
    return jsonify({'compare': payload, 'chart': chart})


@bp.route('/api/favorites/correlation')
def api_favorites_correlation():
    period = request.args.get('period', '1y')
    ids = load_favorites()
    if len(ids) < 2:
        return jsonify({'error': '상관계수는 즐겨찾기 2개 이상 필요합니다.'}), 400

    payload = correlation_favorites(ids, period)
    chart = build_correlation_heatmap(payload.get('labels', []), payload.get('matrix', []))
    return jsonify({'correlation': payload, 'chart': chart})


@bp.route('/api/custom-cards/<category>')
def api_custom_cards_list(category: str):
    if category not in CUSTOMIZABLE_CATEGORIES:
        return jsonify({'error': '지원하지 않는 카테고리입니다.'}), 400
    return jsonify({'category': category, 'items': load_custom_entries(category)})


@bp.route('/api/custom-cards/<category>/search')
def api_custom_cards_search(category: str):
    if category not in CUSTOMIZABLE_CATEGORIES:
        return jsonify({'error': '지원하지 않는 카테고리입니다.'}), 400
    query = request.args.get('q', '')
    results = search_category_listings(category, query)
    return jsonify({'category': category, 'query': query, 'results': results})


@bp.route('/api/custom-cards/<category>', methods=['POST'])
def api_custom_cards_add(category: str):
    if category not in CUSTOMIZABLE_CATEGORIES:
        return jsonify({'error': '지원하지 않는 카테고리입니다.'}), 400

    payload = request.get_json(silent=True) or {}
    symbol = payload.get('symbol') or request.form.get('symbol')
    name = payload.get('name') or request.form.get('name')
    if not symbol:
        return jsonify({'error': 'symbol이 필요합니다.'}), 400

    if category == 'etf_us' and not name:
        from app.services.custom_cards import validate_us_etf_ticker

        validated = validate_us_etf_ticker(symbol)
        if not validated:
            return jsonify({'error': '유효한 미국 ETF 티커가 아닙니다.'}), 400
        symbol, name = validated

    if not name:
        return jsonify({'error': 'name이 필요합니다.'}), 400

    try:
        result = add_custom_card(category, symbol=symbol, name=name)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    snap = get_indicator_snapshot(result['entry']['id'])
    return jsonify({'added': result['entry'], 'indicator': snap})


@bp.route('/api/custom-cards/<category>/<indicator_id>', methods=['DELETE'])
def api_custom_cards_remove(category: str, indicator_id: str):
    if category not in CUSTOMIZABLE_CATEGORIES:
        return jsonify({'error': '지원하지 않는 카테고리입니다.'}), 400
    try:
        result = remove_custom_card(category, indicator_id)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    clear_cache(f'snapshot:{indicator_id}')
    clear_cache(f'series:{indicator_id}')
    return jsonify(result)


@bp.route('/api/simulation/coverage')
def api_simulation_coverage():
    scope = normalize_scope(request.args.get('scope'))
    return jsonify(get_simulation_coverage(scope))


@bp.route('/api/simulation')
def api_simulation():
    start_date = request.args.get('start_date', default_start_date())
    scope = normalize_scope(request.args.get('scope'))
    payload = run_simulation(start_date, scope=scope, force_refresh=_force_refresh())
    if payload.get('error'):
        return jsonify(payload), 400
    return jsonify(payload)


@bp.route('/api/refresh', methods=['POST'])
def api_refresh():
    category = request.json.get('category') if request.is_json else None
    prefix = f'snapshot:' if category is None else None
    clear_cache(prefix)
    if category:
        for item in list_indicators(category):
            clear_cache(f"snapshot:{item['id']}")
            clear_cache(f"series:{item['id']}")
    else:
        clear_cache()
    return jsonify({'ok': True})
