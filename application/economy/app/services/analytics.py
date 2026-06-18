from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.indicators import get_indicator, get_series

COMPARE_COLORS = [
    '#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed',
    '#db2777', '#0891b2', '#4d7c0f', '#ea580c', '#6366f1',
]


def _series_to_frame(indicator_id: str, period: str) -> pd.Series | None:
    indicator = get_indicator(indicator_id)
    if indicator is None:
        return None

    payload = get_series(indicator_id, period)
    points = payload.get('points') or []
    if not points:
        return None

    series = pd.Series(
        {point['date']: float(point['close']) for point in points},
        name=indicator_id,
        dtype=float,
    )
    series.index = pd.to_datetime(series.index)
    return series.sort_index()


def build_aligned_frame(indicator_ids: list[str], period: str) -> pd.DataFrame:
    frames: list[pd.Series] = []
    for indicator_id in indicator_ids:
        series = _series_to_frame(indicator_id, period)
        if series is not None and not series.empty:
            frames.append(series)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, axis=1, join='inner').dropna(how='any')
    return df.sort_index()


def rebase_to_100(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    first = df.iloc[0]
    rebased = df.div(first).mul(100.0)
    return rebased.dropna(how='any')


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or df.shape[1] < 2:
        return pd.DataFrame()
    return df.corr(method='pearson', min_periods=2)


def _indicator_name(indicator_id: str) -> str:
    indicator = get_indicator(indicator_id)
    return indicator['name'] if indicator else indicator_id


def compare_favorites(indicator_ids: list[str], period: str = '1y') -> dict[str, Any]:
    aligned = build_aligned_frame(indicator_ids, period)
    rebased = rebase_to_100(aligned)

    series_payload: list[dict[str, Any]] = []
    if not rebased.empty:
        for indicator_id in rebased.columns:
            series_payload.append({
                'id': indicator_id,
                'name': _indicator_name(indicator_id),
                'points': [
                    {'date': idx.strftime('%Y-%m-%d'), 'close': round(float(value), 4)}
                    for idx, value in rebased[indicator_id].items()
                ],
            })

    return {
        'period': period,
        'base': 100,
        'start_date': rebased.index[0].strftime('%Y-%m-%d') if not rebased.empty else None,
        'series': series_payload,
    }


def correlation_favorites(indicator_ids: list[str], period: str = '1y') -> dict[str, Any]:
    aligned = build_aligned_frame(indicator_ids, period)
    corr = correlation_matrix(aligned)
    labels = [_indicator_name(str(col)) for col in corr.columns]

    matrix: list[list[float | None]] = []
    for row_label in corr.index:
        row_values: list[float | None] = []
        for col_label in corr.columns:
            value = corr.loc[row_label, col_label]
            row_values.append(None if pd.isna(value) else round(float(value), 4))
        matrix.append(row_values)

    pairs: list[dict[str, Any]] = []
    for i, left in enumerate(corr.index):
        for j, right in enumerate(corr.columns):
            if j <= i:
                continue
            value = corr.iloc[i, j]
            if pd.notna(value):
                pairs.append({
                    'a': _indicator_name(str(left)),
                    'b': _indicator_name(str(right)),
                    'value': round(float(value), 4),
                })

    return {
        'period': period,
        'labels': labels,
        'matrix': matrix,
        'pairs': sorted(pairs, key=lambda item: abs(item['value']), reverse=True),
        'sample_size': int(len(aligned)),
    }
