from __future__ import annotations

import plotly.graph_objects as go

from app.services.analytics import COMPARE_COLORS

KOREAN_DATE_XAXIS = {
    'title': '날짜',
    'showgrid': True,
    'gridcolor': '#e2e8f0',
    'type': 'date',
    'tickformat': '%Y.%m.%d',
    'hoverformat': '%Y년 %m월 %d일',
}


def korean_date_xaxis(**extra) -> dict:
    axis = dict(KOREAN_DATE_XAXIS)
    axis.update(extra)
    return axis


def build_line_chart(points: list[dict], *, name: str, unit: str = '') -> dict:
    if not points:
        fig = go.Figure()
        fig.update_layout(title=f'{name} — 데이터 없음', template='plotly_white')
        return fig.to_dict()

    dates = [p['date'] for p in points]
    closes = [p['close'] for p in points]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=closes,
            mode='lines',
            name=name,
            line={'width': 2, 'color': '#2563eb'},
            hovertemplate='%{x|%Y년 %m월 %d일}<br>%{y:,.4f}<extra></extra>',
        )
    )
    y_title = unit or '값'
    fig.update_layout(
        title={'text': name, 'x': 0.02, 'xanchor': 'left'},
        template='plotly_white',
        margin={'l': 48, 'r': 24, 't': 48, 'b': 40},
        hovermode='x unified',
        xaxis=korean_date_xaxis(),
        yaxis={'title': y_title, 'showgrid': True, 'gridcolor': '#e2e8f0'},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'x': 0},
    )
    return fig.to_dict()


def build_compare_chart(series_list: list[dict], *, title: str | None = None) -> dict:
    fig = go.Figure()
    if not series_list:
        fig.update_layout(template='plotly_white', margin={'l': 48, 'r': 24, 't': 24, 'b': 40})
        fig.add_annotation(
            text='비교할 데이터가 없습니다.',
            xref='paper', yref='paper', x=0.5, y=0.5,
            showarrow=False, font={'size': 14, 'color': '#64748b'},
        )
        return fig.to_dict()

    active_series = [series for series in series_list if series.get('points')]
    for index, series in enumerate(active_series):
        points = series.get('points') or []
        color = COMPARE_COLORS[index % len(COMPARE_COLORS)]
        fig.add_trace(
            go.Scatter(
                x=[point['date'] for point in points],
                y=[point['close'] for point in points],
                mode='lines',
                name=series.get('name') or series.get('id'),
                line={'width': 2, 'color': color},
                hovertemplate='%{x|%Y년 %m월 %d일}<br>%{y:.2f}<extra></extra>',
            )
        )

    legend_rows = max(1, (len(active_series) + 2) // 3)
    top_margin = 28 + legend_rows * 24

    layout: dict = {
        'template': 'plotly_white',
        'margin': {'l': 48, 'r': 24, 't': top_margin, 'b': 40},
        'hovermode': 'x unified',
        'xaxis': korean_date_xaxis(),
        'yaxis': {'title': '지수 (시작=100)', 'showgrid': True, 'gridcolor': '#e2e8f0'},
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.01,
            'x': 0,
            'xanchor': 'left',
            'bgcolor': 'rgba(255,255,255,0.85)',
        },
    }
    if title:
        layout['title'] = {'text': title, 'x': 0.02, 'xanchor': 'left', 'y': 0.98, 'yanchor': 'top'}
        layout['margin']['t'] = top_margin + 28
        layout['legend']['y'] = 1.12

    fig.update_layout(**layout)
    return fig.to_dict()


def build_correlation_heatmap(labels: list[str], matrix: list[list[float | None]], *, title: str | None = None) -> dict:
    fig = go.Figure()
    if not labels or not matrix:
        fig.update_layout(template='plotly_white', margin={'l': 80, 'r': 24, 't': 24, 'b': 80})
        fig.add_annotation(
            text='상관계수를 계산할 데이터가 없습니다.',
            xref='paper', yref='paper', x=0.5, y=0.5,
            showarrow=False, font={'size': 14, 'color': '#64748b'},
        )
        return fig.to_dict()

    fig.add_trace(
        go.Heatmap(
            z=matrix,
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            colorscale='RdBu',
            reversescale=True,
            text=[[f'{value:.2f}' if value is not None else '' for value in row] for row in matrix],
            texttemplate='%{text}',
            hovertemplate='%{y} · %{x}<br>r = %{z:.3f}<extra></extra>',
        )
    )
    layout: dict = {
        'template': 'plotly_white',
        'margin': {'l': 80, 'r': 24, 't': 24, 'b': 80},
        'xaxis': {'side': 'bottom', 'tickangle': -30},
        'yaxis': {'autorange': 'reversed'},
    }
    if title:
        layout['title'] = {'text': title, 'x': 0.02, 'xanchor': 'left'}
        layout['margin']['t'] = 48

    fig.update_layout(**layout)
    return fig.to_dict()
