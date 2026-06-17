# Python 데이터 시각화 가이드

**matplotlib · seaborn · plotly · geopandas · folium** 5개 라이브러리의 핵심 기능과 함수 사용법을 정리합니다.  
각 함수 표에서 **필수** 파라미터는 `★`로 표시했습니다.

### 라이브러리 공식 사이트

| 라이브러리 | 공식 문서 | Python 가이드 | PyPI | GitHub |
|------------|-----------|---------------|------|--------|
| **matplotlib** | [matplotlib.org](https://matplotlib.org/stable/) | [API Reference](https://matplotlib.org/stable/api/index.html) | [pypi](https://pypi.org/project/matplotlib/) | [repo](https://github.com/matplotlib/matplotlib) |
| **seaborn** | [seaborn.pydata.org](https://seaborn.pydata.org/) | [API Reference](https://seaborn.pydata.org/api.html) | [pypi](https://pypi.org/project/seaborn/) | [repo](https://github.com/mwaskom/seaborn) |
| **plotly** | [plotly.com/python](https://plotly.com/python/) | [API Reference](https://plotly.com/python-api-reference/) | [pypi](https://pypi.org/project/plotly/) | [repo](https://github.com/plotly/plotly.py) |
| **geopandas** | [geopandas.org](https://geopandas.org/) | [Documentation](https://geopandas.org/en/stable/docs.html) | [pypi](https://pypi.org/project/geopandas/) | [repo](https://github.com/geopandas/geopandas) |
| **folium** | [python-visualization.github.io/folium](https://python-visualization.github.io/folium/) | [Plugins](https://python-visualization.github.io/folium/plugins.html) | [pypi](https://pypi.org/project/folium/) | [repo](https://github.com/python-visualization/folium) |

> folium 의존성: [branca](https://pypi.org/project/branca/) · 지도 엔진: [Leaflet.js](https://leafletjs.com/)

---

## 목차

1. [공통 개념](#1-공통-개념)
2. [설치](#2-설치)
3. [matplotlib](#3-matplotlib)
4. [seaborn](#4-seaborn)
5. [plotly](#5-plotly)
6. [geopandas](#6-geopandas)
7. [folium](#7-folium)
8. [라이브러리 선택 가이드](#8-라이브러리-선택-가이드)
9. [빠른 참조 — 필수 파라미터만](#9-빠른-참조--필수-파라미터만)

---

## 1. 공통 개념

| 용어 | 설명 |
|------|------|
| **Figure** | 전체 캔버스 (도화지) |
| **Axes** | 실제 그래프가 그려지는 축 (좌표평면) |
| **Artist** | 선·점·도형 등 그려지는 객체 |
| **Series / DataFrame** | pandas 1차원·2차원 데이터 |

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()   # Figure + Axes 생성
ax.plot([1, 2, 3], [4, 5, 6])
plt.show()
```

---

## 2. 설치

```bash
pip install matplotlib seaborn plotly geopandas folium pandas numpy branca
```

Colab에는 matplotlib, seaborn, plotly가 기본 포함됩니다. geopandas·folium은 별도 설치가 필요할 수 있습니다.

```python
# plotly 노트북 인라인 표시
import plotly.io as pio
pio.renderers.default = 'colab'   # Colab
# pio.renderers.default = 'notebook'  # Jupyter
```

---

## 3. matplotlib

> **공식 문서:** https://matplotlib.org/stable/ · **API:** https://matplotlib.org/stable/api/index.html · **갤러리:** https://matplotlib.org/stable/gallery/index.html

정적 2D 그래프의 기본 라이브러리입니다.

### 3.1 기본 흐름

```
Figure 생성 → Axes 생성 → Artist 추가 → 축/제목 설정 → show/savefig
```

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig = plt.figure(figsize=(6, 5))   # ★ 없어도 되지만 크기 지정 권장
ax = fig.add_subplot(111)          # 또는 plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_title('제목')
plt.show()
```

### 3.2 Figure / Axes 생성 함수

| 함수 | 필수 입력 | 반환 | 설명 |
|------|-----------|------|------|
| `plt.figure(figsize, dpi)` | 없음 | `Figure` | 빈 캔버스 |
| `plt.subplots(nrows, ncols, figsize)` | 없음 | `(Figure, Axes)` | 서브플롯 한 번에 생성 |
| `fig.add_subplot(nrows, ncols, index)` | `index` ★ | `Axes` | 기존 Figure에 축 추가 |
| `plt.gca()` | 없음 | `Axes` | 현재 Axes 가져오기 |
| `plt.gcf()` | 없음 | `Figure` | 현재 Figure 가져오기 |

```python
# 서브플롯 1행 2열
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].plot([1, 2], [3, 4])
axes[1].bar(['A', 'B'], [3, 7])
plt.tight_layout()
plt.show()
```

### 3.3 선·점·막대 — pyplot / Axes 메서드

| 함수 | 필수 파라미터 | 주요 옵션 | 용도 |
|------|---------------|-----------|------|
| `ax.plot(x, y)` | `y` ★ (`x` 생략 시 인덱스) | `color`, `label`, `linewidth`, `marker` | 선 그래프 |
| `ax.scatter(x, y)` | `y` ★ | `s`(크기), `c`(색), `alpha` | 산점도 |
| `ax.bar(x, height)` | `height` ★ | `width`, `color`, `label` | 막대(세로) |
| `ax.barh(y, width)` | `width` ★ | `height`, `color` | 막대(가로) |
| `ax.hist(x)` | `x` ★ | `bins`, `color`, `edgecolor` | 히스토그램 |
| `ax.pie(x)` | `x` ★ (비율 리스트) | `labels`, `autopct`, `explode` | 파이 차트 |
| `ax.boxplot(x)` | `x` ★ | `labels`, `vert` | 박스플롯 |
| `ax.fill_between(x, y1, y2)` | `y1` ★ | `alpha`, `color` | 영역 채우기 |
| `ax.stackplot(x, y)` | `y` ★ (시리즈들) | `labels`, `colors` | 누적 영역 |
| `ax.step(x, y)` | `y` ★ | `where` | 계단형 그래프 |
| `ax.errorbar(x, y, yerr)` | `y` ★ | `xerr`, `fmt`, `capsize` | 오차 막대 |
| `ax.vlines(x, ymin, ymax)` | `x`, `ymin`, `ymax` ★ | `colors`, `linestyles` | 수직선 |
| `ax.hlines(y, xmin, xmax)` | `y`, `xmin`, `xmax` ★ | `colors` | 수평선 |
| `ax.axvline(x)` | `x` ★ | `color`, `linestyle` | 기준 수직선 |
| `ax.axhline(y)` | `y` ★ | `color`, `linestyle` | 기준 수평선 |

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(x, y, label='sin', color='blue')
ax.scatter([1, 2, 3], [0.8, 0.9, 0.1], s=50, c='red')
ax.axhline(0, color='gray', linestyle='--')
ax.legend()
ax.grid(True, alpha=0.3)
plt.show()
```

### 3.4 이미지·등고선

| 함수 | 필수 파라미터 | 주요 옵션 | 용도 |
|------|---------------|-----------|------|
| `ax.imshow(Z)` | `Z` ★ (2D 배열) | `cmap`, `aspect`, `origin` | 이미지/히트맵 |
| `ax.contour(X, Y, Z)` | `Z` ★ | `levels`, `colors` | 등고선 |
| `ax.contourf(X, Y, Z)` | `Z` ★ | `levels`, `cmap`, `alpha` | 채운 등고선 |
| `plt.colorbar(mappable, ax)` | `mappable` ★ | `label`, `shrink` | 컬러바 |

```python
import numpy as np

Z = np.random.rand(10, 10)
fig, ax = plt.subplots()
im = ax.imshow(Z, cmap='viridis')
plt.colorbar(im, ax=ax)
plt.show()
```

### 3.5 patches — 도형 객체

| 클래스 | 필수 파라미터 | 설명 |
|--------|---------------|------|
| `patches.Rectangle(xy, width, height)` | `xy`, `width`, `height` ★ | 사각형 |
| `patches.Circle(xy, radius)` | `xy`, `radius` ★ | 원 |
| `patches.Polygon(xy)` | `xy` ★ (꼭짓점 좌표) | 다각형 |
| `patches.Wedge(center, r, theta1, theta2)` | `center`, `r`, `theta1`, `theta2` ★ | 부채꼴 |
| `patches.FancyArrow(x, y, dx, dy)` | `x`, `y`, `dx`, `dy` ★ | 화살표 |

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots()
ax.add_patch(patches.Rectangle((1, 1), 4, 3, fill=False, edgecolor='blue'))
ax.add_patch(patches.Circle((3, 3), 1, fill=False, edgecolor='red'))
ax.set_xlim(0, 8)
ax.set_ylim(0, 8)
plt.show()
```

### 3.6 축·텍스트·범례

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `ax.set_xlabel(label)` | `label` ★ | X축 라벨 |
| `ax.set_ylabel(label)` | `label` ★ | Y축 라벨 |
| `ax.set_title(label)` | `label` ★ | 제목 |
| `ax.set_xlim(left, right)` | 없음 | X축 범위 |
| `ax.set_ylim(bottom, top)` | 없음 | Y축 범위 |
| `ax.legend()` | 없음 (`label` 지정된 Artist 필요) | 범례 |
| `ax.text(x, y, s)` | `x`, `y`, `s` ★ | 텍스트 |
| `ax.annotate(text, xy, xytext)` | `text`, `xy` ★ | 주석 화살표 |
| `ax.tick_params(axis, labelsize)` | 없음 | 눈금 스타일 |
| `plt.xticks(ticks, labels)` | 없음 | X 눈금 라벨 |
| `plt.yticks(ticks, labels)` | 없음 | Y 눈금 라벨 |
| `ax.grid(visible)` | 없음 | 격자 |
| `plt.tight_layout()` | 없음 | 여백 자동 조정 |

### 3.7 스타일·저장

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `plt.style.use(style)` | `style` ★ | `'ggplot'`, `'seaborn-v0_8'` 등 |
| `plt.rcParams['key']` | - | 전역 폰트·크기 설정 |
| `fig.savefig(fname)` | `fname` ★ | PNG, PDF, SVG 등 저장 |

```python
plt.rcParams['font.family'] = 'Malgun Gothic'   # Windows 한글
plt.rcParams['axes.unicode_minus'] = False       # 마이너스 기호

fig.savefig('output.png', dpi=150, bbox_inches='tight')
```

### 3.8 pandas 연동

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `df.plot()` | 없음 | 컬럼별 선 그래프 |
| `df.plot(kind='bar')` | `kind` | bar, barh, hist, box, kde, area, pie, scatter |
| `df.plot(x, y, kind='scatter')` | `x`, `y` (scatter 시) ★ | 산점도 |
| `df.plot(subplots=True)` | 없음 | 컬럼별 서브플롯 |

```python
df.plot(x='lon', y='lat', kind='scatter', figsize=(8, 5))
plt.show()
```

---

## 4. seaborn

> **공식 문서:** https://seaborn.pydata.org/ · **API:** https://seaborn.pydata.org/api.html · **예제 갤러리:** https://seaborn.pydata.org/examples/index.html

matplotlib 위의 통계 시각화 라이브러리입니다. **DataFrame + 컬럼명** 기반이 기본입니다.

### 4.1 전역 설정

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `sns.set_theme(style, palette)` | 없음 | 테마·팔레트 |
| `sns.set_palette(palette)` | `palette` ★ | 색상 팔레트 |
| `sns.color_palette(palette, n_colors)` | `palette` ★ | 팔레트 리스트 반환 |

```python
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style='whitegrid', palette='pastel')
```

### 4.2 Figure 레벨 (서브플롯 + 한 번에 그리기)

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `sns.FacetGrid(data, col, row)` | `data` ★ | 조건별 서브플롯 그리드 |
| `sns.PairGrid(data)` | `data` ★ | 변수 쌍 조합 그리드 |
| `sns.JointGrid(data, x, y)` | `data`, `x`, `y` ★ | 산점도 + 주변 분포 |
| `sns.catplot(kind, data, x, y)` | `kind`, `data`, `x`, `y` ★ | 범주형 plot 통합 |
| `sns.relplot(kind, data, x, y)` | `kind`, `data`, `x`, `y` ★ | 관계형 plot 통합 |
| `sns.displot(kind, data)` | `data` ★ | 분포 plot 통합 |
| `sns.lmplot(data, x, y)` | `data`, `x`, `y` ★ | 회귀선 + 산점도 |
| `sns.pairplot(data)` | `data` ★ | 변수 쌍 산점도 행렬 |

```python
import seaborn as sns

tips = sns.load_dataset('tips')
g = sns.FacetGrid(tips, col='time', row='sex')
g.map(sns.scatterplot, 'total_bill', 'tip')
plt.show()
```

### 4.3 관계형 (Relational)

| 함수 | 필수 파라미터 | 주요 옵션 | 용도 |
|------|---------------|-----------|------|
| `sns.scatterplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `size`, `style` | 산점도 |
| `sns.lineplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `style`, `markers` | 선 그래프 |
| `sns.relplot(kind, data, x, y)` | `kind`, `data`, `x`, `y` ★ | `col`, `row`, `hue` | scatter/line 통합 |

```python
sns.scatterplot(data=df, x='lon', y='lat', hue='division', size='size', sizes=(20, 200))
plt.show()
```

### 4.4 분포형 (Distribution)

| 함수 | 필수 파라미터 | 주요 옵션 | 용도 |
|------|---------------|-----------|------|
| `sns.histplot(data, x)` | `data`, `x` ★ | `bins`, `hue`, `kde`, `element` | 히스토그램 |
| `sns.kdeplot(data, x)` | `data`, `x` ★ | `fill`, `hue`, `bw_adjust` | 밀도 곡선 |
| `sns.ecdfplot(data, x)` | `data`, `x` ★ | `hue` | 누적 분포 |
| `sns.rugplot(data, x)` | `data`, `x` ★ | `height` | 러그(눈금) |
| `sns.displot(kind, data, x)` | `data`, `x` ★ | `kind='hist'/'kde'/'ecdf'` | 분포 통합 |
| `sns.jointplot(data, x, y)` | `data`, `x`, `y` ★ | `kind='scatter'/'hist'/'kde'` | 2변수 분포 |
| `sns.pairplot(data)` | `data` ★ | `hue`, `diag_kind` | 변수 쌍 행렬 |

```python
sns.histplot(data=df, x='size', bins=20, kde=True)
plt.show()
```

### 4.5 범주형 (Categorical)

| 함수 | 필수 파라미터 | 주요 옵션 | 용도 |
|------|---------------|-----------|------|
| `sns.countplot(data, x)` | `data`, `x` ★ | `hue`, `order` | 빈도 막대 |
| `sns.barplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `estimator`, `errorbar` | 집계 막대 |
| `sns.boxplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `order` | 박스플롯 |
| `sns.violinplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `split`, `inner` | 바이올린 |
| `sns.stripplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `jitter`, `dodge` | 점 분포 |
| `sns.swarmplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `dodge` | 벌집 점 |
| `sns.boxenplot(data, x, y)` | `data`, `x`, `y` ★ | `hue` | 확장 박스 |
| `sns.pointplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `markers` | 점+선 |
| `sns.catplot(kind, data, x, y)` | `kind`, `data`, `x`, `y` ★ | `col`, `row` | 범주형 통합 |

```python
sns.boxplot(data=df, x='division', y='size')
plt.show()
```

### 4.6 행렬·회귀

| 함수 | 필수 파라미터 | 주요 옵션 | 용도 |
|------|---------------|-----------|------|
| `sns.heatmap(data)` | `data` ★ (2D) | `annot`, `cmap`, `fmt`, `vmin`, `vmax` | 히트맵 |
| `sns.clustermap(data)` | `data` ★ | `method`, `cmap`, `standard_scale` | 클러스터 히트맵 |
| `sns.regplot(data, x, y)` | `data`, `x`, `y` ★ | `order`, `ci`, `scatter_kws` | 회귀 산점도 |
| `sns.lmplot(data, x, y)` | `data`, `x`, `y` ★ | `hue`, `col`, `row` | 회귀 + FacetGrid |
| `sns.residplot(data, x, y)` | `data`, `x`, `y` ★ | `lowess` | 잔차 플롯 |

```python
corr = df.corr(numeric_only=True)
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
plt.show()
```

### 4.7 스타일·색상

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `sns.set_style(style)` | `style` ★ | `darkgrid`, `whitegrid`, `dark`, `white`, `ticks` |
| `sns.set_context(context)` | `context` ★ | `paper`, `notebook`, `talk`, `poster` |
| `sns.despine(ax)` | 없음 | 위·오른쪽 테두리 제거 |
| `sns.move_legend(ax, loc)` | `ax` ★ | 범례 위치 이동 |

---

## 5. plotly

> **공식 문서:** https://plotly.com/python/ · **API:** https://plotly.com/python-api-reference/ · **Plotly Express:** https://plotly.com/python/plotly-express/ · **차트 갤러리:** https://plotly.com/python/

인터랙티브(확대·호버·슬라이더) 시각화 라이브러리입니다.

### 5.1 두 가지 API

| API | 특징 | 언제 쓰나 |
|-----|------|-----------|
| **Plotly Express (`px`)** | 한 줄로 빠른 차트 | 탐색·대시보드 |
| **Graph Objects (`go`)** | 세밀한 제어 | 커스텀 레이아웃 |

```python
import plotly.express as px
import plotly.graph_objects as go
```

### 5.2 Plotly Express — 관계형

| 함수 | 필수 파라미터 | 주요 옵션 | 용도 |
|------|---------------|-----------|------|
| `px.scatter(data, x, y)` | `data`, `x`, `y` ★ | `color`, `size`, `hover_data`, `facet_col` | 산점도 |
| `px.line(data, x, y)` | `data`, `x`, `y` ★ | `color`, `line_group`, `markers` | 선 그래프 |
| `px.area(data, x, y)` | `data`, `x`, `y` ★ | `color`, `line_group` | 영역 |
| `px.scatter_geo(data, lat, lon)` | `data`, `lat`, `lon` ★ | `color`, `size`, `scope` | 지도 산점도 |
| `px.scatter_map(data, lat, lon)` | `data`, `lat`, `lon` ★ | `color`, `size`, `zoom` | 타일 지도 산점도 |
| `px.line_geo(data, lat, lon)` | `data`, `lat`, `lon` ★ | `color` | 지도 선 |
| `px.density_map(data, lat, lon, z)` | `data`, `lat`, `lon`, `z` ★ | `radius`, `zoom` | 밀도 지도 |

```python
import plotly.express as px

fig = px.scatter(
    df, x='lon', y='lat',
    color='division',
    size='size',
    hover_data=['direction'],
    title='군대 배치 산점도',
)
fig.show()
```

### 5.3 Plotly Express — 분포·범주

| 함수 | 필수 파라미터 | 주요 옵션 | 용도 |
|------|---------------|-----------|------|
| `px.histogram(data, x)` | `data`, `x` ★ | `nbins`, `color`, `barmode` | 히스토그램 |
| `px.density_contour(data, x, y)` | `data`, `x`, `y` ★ | `color` | 밀도 등고선 |
| `px.density_heatmap(data, x, y)` | `data`, `x`, `y` ★ | `nbinsx`, `nbinsy` | 2D 밀도 |
| `px.box(data, x, y)` | `data`, `x`, `y` ★ | `color`, `points` | 박스플롯 |
| `px.violin(data, x, y)` | `data`, `x`, `y` ★ | `color`, `box` | 바이올린 |
| `px.strip(data, x, y)` | `data`, `x`, `y` ★ | `color` | 스트립 |
| `px.bar(data, x, y)` | `data`, `x` ★ | `y`, `color`, `barmode` | 막대 |
| `px.pie(data, names, values)` | `data`, `names`, `values` ★ | `hole`, `color` | 파이·도넛 |
| `px.sunburst(data, names, values)` | `data`, `names`, `values` ★ | `parents` | 선버스트 |
| `px.treemap(data, names, values)` | `data`, `names`, `values` ★ | `parents` | 트리맵 |
| `px.funnel(data, x, y)` | `data`, `x`, `y` ★ | `color` | 퍼널 |
| `px.parallel_coordinates(data, dimensions)` | `data`, `dimensions` ★ | `color` | 평행 좌표 |
| `px.parallel_categories(data, dimensions)` | `data`, `dimensions` ★ | `color` | 평행 범주 |

```python
fig = px.histogram(df, x='size', nbins=30, color='division')
fig.show()
```

### 5.4 Plotly Express — 행렬·시계열·재무

| 함수 | 필수 파라미터 | 용도 |
|------|---------------|------|
| `px.imshow(Z)` | `Z` ★ (배열 또는 wide DataFrame) | 이미지·히트맵 |
| `px.imshow(data)` | `data` ★ | 상관행렬 등 |
| `px.scatter_matrix(data, dimensions)` | `data`, `dimensions` ★ | 산점도 행렬 |
| `px.line(data, x, y)` | `data`, `x`, `y` ★ | 시계열 |
| `px.area(data, x, y)` | `data`, `x`, `y` ★ | 누적 시계열 |
| `px.bar(data, x, y)` | `data`, `x` ★ | 시계열 막대 |
| `px.timeline(data, x_start, x_end, y)` | `data`, `x_start`, `x_end`, `y` ★ | 간트 |
| `px.candlestick(data, x, open, high, low, close)` | `data`, `x`, `open`, `high`, `low`, `close` ★ | 캔들 |
| `px.funnel(data, x, y)` | `data`, `x`, `y` ★ | 퍼널 |

### 5.5 Graph Objects — 기본 trace

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `go.Figure(data, layout)` | 없음 | 빈 Figure |
| `go.Scatter(x, y)` | `y` ★ | 선·산점 (`mode='lines+markers'`) |
| `go.Bar(x, y)` | `y` ★ | 막대 |
| `go.Histogram(x)` | `x` ★ | 히스토그램 |
| `go.Box(y)` | `y` ★ | 박스 |
| `go.Violin(y)` | `y` ★ | 바이올린 |
| `go.Pie(labels, values)` | `labels`, `values` ★ | 파이 |
| `go.Heatmap(z)` | `z` ★ | 히트맵 |
| `go.Contour(z)` | `z` ★ | 등고선 |
| `go.Scattergeo(lat, lon)` | `lat`, `lon` ★ | 지리 산점도 |
| `go.Choropleth(locations, z)` | `locations`, `z` ★ | 단색 지도 |
| `go.Scattermapbox(lat, lon)` | `lat`, `lon` ★ | Mapbox 산점도 |
| `fig.add_trace(trace)` | `trace` ★ | trace 추가 |
| `fig.add_hline(y)` | `y` ★ | 수평 기준선 |
| `fig.add_vline(x)` | `x` ★ | 수직 기준선 |
| `fig.update_layout(**kwargs)` | 없음 | 제목·축·범례 |
| `fig.update_xaxes(**kwargs)` | 없음 | X축 설정 |
| `fig.update_yaxes(**kwargs)` | 없음 | Y축 설정 |
| `fig.show()` | 없음 | 표시 |
| `fig.write_html(path)` | `path` ★ | HTML 저장 |
| `fig.write_image(path)` | `path` ★ | PNG 등 (kaleido 필요) |

```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6], mode='lines+markers', name='A'))
fig.add_trace(go.Bar(x=['X', 'Y'], y=[3, 7], name='B'))
fig.update_layout(title='복합 차트', barmode='group')
fig.show()
```

### 5.6 레이아웃 자주 쓰는 옵션

```python
fig.update_layout(
    title='제목',
    xaxis_title='X축',
    yaxis_title='Y축',
    legend_title='범례',
    width=900,
    height=500,
    template='plotly_white',   # plotly, ggplot2, seaborn, simple_white 등
    hovermode='closest',
)
```

### 5.7 서브플롯

```python
from plotly.subplots import make_subplots
import plotly.graph_objects as go

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('산점도', '막대', '히스토그램', '박스'),
    specs=[[{}, {}], [{}, {}]],
)
fig.add_trace(go.Scatter(x=[1, 2], y=[3, 4]), row=1, col=1)
fig.add_trace(go.Bar(x=['A', 'B'], y=[5, 2]), row=1, col=2)
fig.show()
```

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `make_subplots(rows, cols)` | `rows`, `cols` ★ | 서브플롯 Figure |
| `fig.add_trace(trace, row, col)` | `trace`, `row`, `col` ★ | 위치 지정 추가 |

---

## 6. geopandas

> **공식 문서:** https://geopandas.org/en/stable/docs.html · **API Reference:** https://geopandas.org/en/stable/docs/reference.html · **Gallery:** https://geopandas.org/en/stable/gallery/index.html

지리 공간 데이터(점·선·면)를 다루고 지도 위에 그리는 라이브러리입니다.

### 6.1 핵심 구조

| 객체 | 설명 |
|------|------|
| `GeoDataFrame` | `geometry` 컬럼을 가진 DataFrame |
| `GeoSeries` | geometry 1차원 시리즈 |
| `shapely` geometry | Point, LineString, Polygon 등 |

```python
import geopandas as gpd
from shapely.geometry import Point

gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df['lon'], df['lat']),
    crs='EPSG:4326',
)
```

### 6.2 파일 읽기·쓰기

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `gpd.read_file(filename)` | `filename` ★ | GeoJSON, Shapefile, GPKG 등 |
| `gdf.to_file(filename, driver)` | `filename` ★ | 저장 (`driver='GeoJSON'`) |
| `gpd.read_file(url)` | `url` ★ | URL에서 직접 읽기 |

```python
kor = gpd.read_file('SIDO_MAP_2022.json')
cameras = gpd.read_file('cameras.geojson')
kor.to_file('output.geojson', driver='GeoJSON')
```

### 6.3 좌표계 (CRS)

| 함수 / 속성 | 필수 | 설명 |
|-------------|------|------|
| `gdf.crs` | - | 현재 좌표계 |
| `gdf.set_crs(epsg)` | `epsg` ★ | CRS 최초 지정 |
| `gdf.to_crs(epsg)` | `epsg` ★ | 좌표계 변환 |
| `gdf.estimate_utm_crs()` | - | UTM CRS 추정 |

```python
# WGS84 (위경도) — folium·plotly map용
gdf = gdf.set_crs('EPSG:4326')

# 한국 중부원점 (미터 단위)
gdf_proj = gdf.to_crs('EPSG:5179')
```

| EPSG | 설명 |
|------|------|
| `4326` | WGS84 (위도·경도) — **지도 시각화 기본** |
| `5179` | Korea 2000 / Central Belt (미터) |
| `5186` | Korea 2000 / East Belt |

### 6.4 geometry 생성

| 함수 | 필수 파라미터 | 설명 |
|------|---------------|------|
| `gpd.points_from_xy(x, y)` | `x`, `y` ★ | Point 리스트 |
| `gpd.points_from_xy(x, y, z)` | `x`, `y` ★ | 3D Point |
| `shapely.geometry.Point(x, y)` | `x`, `y` ★ | 단일 점 |
| `shapely.geometry.LineString(coords)` | `coords` ★ | 선 |
| `shapely.geometry.Polygon(shell)` | `shell` ★ | 다각형 |
| `gpd.GeoSeries.from_wkt(wkt)` | `wkt` ★ | WKT 문자열 → geometry |
| `gpd.GeoSeries.from_geojson(geo)` | `geo` ★ | GeoJSON → geometry |

```python
from shapely.geometry import Point, Polygon

gdf = gpd.GeoDataFrame(
    {'name': ['서울', '부산']},
    geometry=[Point(126.98, 37.57), Point(129.08, 35.18)],
    crs='EPSG:4326',
)
```

### 6.5 공간 연산

| 함수 / 메서드 | 필수 | 설명 |
|---------------|------|------|
| `gdf.buffer(distance)` | `distance` ★ | 버퍼(영역 확장) |
| `gdf.centroid` | - | 중심점 |
| `gdf.area` | - | 면적 (투영 좌표계에서) |
| `gdf.length` | - | 길이 |
| `gdf.bounds` | - | xmin, ymin, xmax, ymax |
| `gdf.distance(other)` | `other` ★ | 거리 |
| `gdf.within(other)` | `other` ★ | 포함 여부 |
| `gdf.contains(other)` | `other` ★ | 포함 관계 |
| `gdf.intersects(other)` | `other` ★ | 교차 여부 |
| `gdf.union(other)` | `other` ★ | 합집합 |
| `gdf.intersection(other)` | `other` ★ | 교집합 |
| `gdf.dissolve(by)` | `by` ★ | 컬럼 기준 병합 |
| `gdf.sjoin(left, right, how, predicate)` | `left`, `right` ★ | 공간 조인 |
| `gdf.clip(mask)` | `mask` ★ | 영역 자르기 |
| `gdf.explode()` | - | MultiPolygon 분리 |
| `gdf.simplify(tolerance)` | `tolerance` ★ | 단순화 |

```python
# 시도별 카메라 수 집계 후 경계와 조인
sido = gpd.read_file('SIDO_MAP_2022.json')
points = gpd.GeoDataFrame(
    df, geometry=gpd.points_from_xy(df['경도'], df['위도']), crs='EPSG:4326'
)
joined = gpd.sjoin(points, sido, how='left', predicate='within')
counts = joined.groupby('시도명').size()
```

### 6.6 시각화 — `.plot()`

| 메서드 | 필수 | 주요 옵션 | 설명 |
|--------|------|-----------|------|
| `gdf.plot()` | 없음 | `column`, `cmap`, `legend`, `edgecolor` | 기본 지도 |
| `gdf.plot(column)` | `column` ★ | `cmap`, `legend`, `scheme` | choropleth |
| `gdf.plot(markersize)` | 없음 | `color`, `alpha` | 점 크기 |
| `gdf.plot(ax)` | `ax` ★ | matplotlib Axes 위에 그리기 |
| `gdf.explore()` | 없음 | `column`, `tooltip`, `tiles` | **인터랙티브 folium 지도** |

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 10))
kor.plot(ax=ax, column='카메라수', cmap='Blues', legend=True, edgecolor='black')
plt.title('시도별 카메라 수')
plt.show()
```

```python
# folium 기반 인터랙티브 (geopandas ≥ 0.10)
kor.explore(column='카메라수', cmap='Blues', legend=True, tiles='CartoDB positron')
```

### 6.7 `.plot()` 주요 파라미터

| 파라미터 | 설명 |
|----------|------|
| `column` | 색상 매핑 컬럼 (choropleth) |
| `cmap` | matplotlib 컬러맵 (`'viridis'`, `'Blues'` 등) |
| `legend` | 범례 표시 |
| `scheme` | 분류 방식 (`'quantiles'`, `'equal_interval'`, `'fisher_jenks'`) |
| `edgecolor` | 경계선 색 |
| `facecolor` | 면 색 (단색) |
| `markersize` | 점 크기 |
| `alpha` | 투명도 |
| `figsize` | Figure 크기 |
| `ax` | matplotlib Axes |

### 6.8 folium 연동

```python
import folium
import json

m = folium.Map(location=[36.24, 128.10], zoom_start=7)

folium.GeoJson(
    kor.to_json(),
    name='시도 경계',
    tooltip=folium.GeoJsonTooltip(fields=['시도명', '카메라수']),
).add_to(m)

m.save('map.html')
```

| folium 함수 | 필수 | 설명 |
|-------------|------|------|
| `folium.GeoJson(data)` | `data` ★ | GeoJSON 또는 dict |
| `folium.Choropleth(geo_data, data, columns)` | `geo_data`, `data`, `columns` ★ | 단계구분도 |
| `folium.CircleMarker(location, radius)` | `location` ★ | 원형 마커 |

### 6.9 contextily — 배경 타일 (선택)

```python
import contextily as cx

ax = gdf.to_crs(epsg=3857).plot(figsize=(10, 10), alpha=0.5)
cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik)
```

---

## 7. folium

> **공식 문서:** https://python-visualization.github.io/folium/ · **Plugins:** https://python-visualization.github.io/folium/plugins.html · **Getting Started:** https://python-visualization.github.io/folium/getting_started.html · **Leaflet.js:** https://leafletjs.com/

**Leaflet.js** 기반의 인터랙티브 **웹 지도** 라이브러리입니다.  
마커·히트맵·GeoJSON·레이어 제어 등을 HTML로 출력하며, Colab·Jupyter에서 iframe으로 표시합니다.

> 실습 노트북: [folium/basic.ipynb](../folium/basic.ipynb)

### 7.1 기본 구조

```
Map 생성 → 레이어/마커 추가 → .add_to(m) → show / save
```

```python
import folium as fm

m = fm.Map(location=[37.49, 127.02], zoom_start=13)
fm.Marker(location=[37.49, 127.02], popup='서울').add_to(m)
m.save('map.html')
```

### 7.2 Map — 지도 객체

| 파라미터 | 필수 | 기본값 | 설명 |
|----------|------|--------|------|
| `location` | ★ | - | `[위도, 경도]` 중심 좌표 |
| `zoom_start` | | `1` | 초기 확대 수준 (클수록 가까이) |
| `tiles` | | `'OpenStreetMap'` | 타일 레이어 URL 또는 이름 |
| `width` | | `'100%'` | 지도 너비 |
| `height` | | `'100%'` | 지도 높이 |
| `control_scale` | | `False` | 축척 표시 |
| `zoom_control` | | `True` | 줌 버튼 |

```python
m = fm.Map(
    location=[36.24, 128.10],
    zoom_start=7,
    tiles='CartoDB positron',
    width='100%',
    height='600px',
    control_scale=True,
)
```

**타일 미리보기:** [leaflet-providers](https://leaflet-extras.github.io/leaflet-providers/preview)

| tiles 값 | 스타일 |
|----------|--------|
| `'OpenStreetMap'` | 기본 OSM |
| `'CartoDB positron'` | 밝은 회색 |
| `'CartoDB dark_matter'` | 다크 |
| `'Stamen Terrain'` | 지형 |

### 7.3 Marker — 마커

| 클래스 / 파라미터 | 필수 | 설명 |
|-------------------|------|------|
| `fm.Marker(location)` | `location` ★ | `[위도, 경도]` |
| `popup` | | 클릭 시 팝업 (str 또는 `Popup`) |
| `tooltip` | | 마우스 오버 텍스트 |
| `icon` | | `Icon`, `DivIcon`, `AwesomeMarkers` |
| `.add_to(m)` | `m` ★ | 지도에 추가 |

```python
fm.Marker(
    location=[37.4904, 127.0162],
    popup='서울교육대학교',
    tooltip='교대',
    icon=fm.Icon(color='red', icon='home'),
).add_to(m)
```

### 7.4 Icon · Popup · Tooltip

| 클래스 | 필수 파라미터 | 설명 |
|--------|---------------|------|
| `fm.Icon(color, icon)` | `color` ★ | `red`, `blue`, `green` 등 + `home`, `star`, `flag` |
| `fm.Popup(html, max_width)` | `html` ★ | HTML 팝업 |
| `fm.Tooltip(text)` | `text` ★ | 호버 텍스트 |
| `branca.element.IFrame(html, width, height)` | `html` ★ | iframe 팝업 |

```python
import branca

html = '<h3>제목</h3><p>설명</p>'
iframe = branca.element.IFrame(html, width=300, height=200)
popup = fm.Popup(iframe, max_width=320)

fm.Marker(location=[37.49, 127.02], popup=popup).add_to(m)
```

### 7.5 선·면 — PolyLine · Polygon · GeoJson

| 클래스 | 필수 파라미터 | 주요 옵션 | 용도 |
|--------|---------------|-----------|------|
| `fm.PolyLine(locations)` | `locations` ★ | `color`, `weight`, `opacity` | 선 (좌표 리스트) |
| `fm.Polygon(locations)` | `locations` ★ | `fill`, `fill_color`, `fill_opacity` | 다각형 |
| `fm.GeoJson(data)` | `data` ★ | `name`, `style_function`, `tooltip` | GeoJSON dict·파일 |
| `fm.Circle(location, radius)` | `location`, `radius` ★ | `color`, `fill` | 원 (반경 m) |
| `fm.CircleMarker(location, radius)` | `location`, `radius` ★ | `color`, `fill` | 원형 마커 (픽셀) |

```python
# 직선
fm.PolyLine(
    locations=[[37.49, 127.02], [37.50, 127.03]],
    color='red', weight=3,
).add_to(m)

# GeoJSON (시도 경계 등)
fm.GeoJson(
    data=geojson_dict,
    name='시도 경계',
    tooltip=fm.GeoJsonTooltip(fields=['시도명'], aliases=['시도']),
).add_to(m)
```

| GeoJson 보조 클래스 | 필수 | 설명 |
|---------------------|------|------|
| `fm.GeoJsonTooltip(fields)` | `fields` ★ | 호버 필드 |
| `fm.GeoJsonPopup(fields)` | `fields` ★ | 클릭 팝업 필드 |
| `style_function` | `lambda feat: {...}` | feature별 스타일 |

### 7.6 레이어 제어 — FeatureGroup · LayerControl

| 클래스 | 필수 | 설명 |
|--------|------|------|
| `fm.FeatureGroup(name)` | | 마커·도형 그룹 |
| `fm.LayerControl()` | | 우측 상단 레이어 토글 |

```python
group1 = fm.FeatureGroup(name='그룹1').add_to(m)
group2 = fm.FeatureGroup(name='그룹2').add_to(m)

fm.Marker([37.49, 127.02], icon=fm.Icon(color='red')).add_to(group1)
fm.Marker([37.50, 127.03], icon=fm.Icon(color='blue')).add_to(group2)

fm.LayerControl().add_to(m)
```

### 7.7 plugins — 확장 기능

`from folium.plugins import ...` 로 불러옵니다.

#### MarkerCluster — 대량 마커

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `MarkerCluster()` | 없음 | 클러스터 그룹 생성 |
| `.add_to(m)` | `m` ★ | 지도에 추가 |

```python
from folium.plugins import MarkerCluster

cluster = MarkerCluster().add_to(m)
for _, row in df.iterrows():
    fm.Marker(
        location=[row['위도'], row['경도']],
        popup=row['설치장소'],
    ).add_to(cluster)
```

#### HeatMap — 정적 히트맵

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `data` | ★ | `[[lat, lon], ...]` 또는 `[[lat, lon, weight], ...]` |
| `radius` | | 점 크기 (기본 25) |
| `max_zoom` | | 최대 줌 |
| `gradient` | | 색상 그라데이션 dict |

```python
from folium.plugins import HeatMap

HeatMap(
    data=df[['위도', '경도']].values.tolist(),
    radius=10,
    max_zoom=13,
).add_to(m)
```

#### HeatMapWithTime — 시간 애니메이션 히트맵

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `data` | ★ | 프레임별 `[[lat, lon], ...]` 리스트의 리스트 |
| `index` | ★ | 각 프레임 라벨 (연도 등) |
| `auto_play` | | 자동 재생 (기본 False) |
| `radius` | | 점 크기 |
| `max_opacity` | | 최대 불투명도 |

```python
from folium.plugins import HeatMapWithTime

heat_data = []   # 연도별 좌표 리스트
year_labels = []

for y in years:
    subset = df[df['설치연도'] <= y]   # 누적
    heat_data.append(subset[['위도', '경도']].values.tolist())
    year_labels.append(str(y))

HeatMapWithTime(
    data=heat_data,
    index=year_labels,
    auto_play=True,
    radius=14,
).add_to(m)
```

#### MiniMap — 미니맵

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `position` | | `'bottomright'` 등 |
| `toggle_display` | | 클릭 접기/펼치기 |
| `zoom_level_offset` | | 메인 대비 줌 차이 (기본 -5) |

```python
from folium.plugins import MiniMap

MiniMap(toggle_display=True).add_to(m)
```

#### MeasureControl — 거리·면적 재기

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `position` | | `'topright'` |
| `primary_length_unit` | | `'meters'`, `'kilometers'` |
| `primary_area_unit` | | `'sqmeters'`, `'hectares'` |

```python
from folium.plugins import MeasureControl

MeasureControl(
    position='topright',
    primary_length_unit='meters',
    primary_area_unit='sqmeters',
).add_to(m)
```

#### MousePosition — 마우스 좌표 표시

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `position` | | `'bottomleft'` |
| `separator` | | 위도·경도 구분자 |
| `num_digits` | | 소수점 자릿수 |
| `prefix` | | 접두 라벨 |

```python
from folium.plugins import MousePosition

MousePosition(
    position='bottomleft',
    separator=' | ',
    prefix='좌표: ',
    num_digits=6,
).add_to(m)
```

#### Draw — 그리기 도구

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `export` | | GeoJSON보내기 버튼 |
| `position` | | `'topleft'` |
| `draw_options` | | 선·다각형·원 등 활성화 |
| `edit_options` | | 편집·삭제 |

```python
from folium.plugins import Draw

Draw(
    export=True,
    position='topleft',
    draw_options={'polyline': True, 'polygon': True, 'circle': True},
    edit_options={'edit': True, 'remove': True},
).add_to(m)
```

#### 기타 plugins

| 클래스 | 용도 |
|--------|------|
| `AntPath` | 움직이는 점선 경로 |
| `Bezier` | 베지어 곡선 |
| `BoatMarker` | 방향 표시 마커 |
| `DualMap` | 동기화된 이중 지도 |
| `FastMarkerCluster` | 대량 마커 (고속) |
| `FloatImage` | 이미지 오버레이 |
| `Fullscreen` | 전체화면 버튼 |
| `HeatMapWithTime` | 시간 히트맵 |
| `LocateControl` | 현재 위치 |
| `MarkerCluster` | 마커 클러스터 |
| `MiniMap` | 미니맵 |
| `MousePosition` | 좌표 표시 |
| `OverView` | 미니맵(구버전) |
| `PolyLineTextPath` | 선 위 텍스트 |
| `ScrollZoomToggler` | 스크롤 줌 토글 |
| `Search` | 레이어 검색 |
| `SemiCircle` | 반원 |
| `SideBySideLayers` | 레이어 비교 슬라이더 |
| `TagFilterButton` | 태그 필터 |
| `Terminator` | 주야 구분선 |
| `TimeSliderChoropleth` | 시간 choropleth |
| `TimestampedGeoJson` | 시간 GeoJSON |
| `TreeLayerControl` | 트리 레이어 |
| `VectorUrlTileLayer` | 벡터 타일 |

### 7.8 Choropleth — 단계구분도

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `geo_data` | ★ | GeoJSON URL·dict·문자열 |
| `data` | ★ | pandas Series 또는 dict |
| `columns` | ★ | `[key_col, value_col]` 또는 None |
| `key_on` | ★ | GeoJSON feature 키 (`'feature.properties.name'`) |
| `fill_color` | | `'YlOrRd'`, `'Blues'` 등 |
| `legend_name` | | 범례 제목 |

```python
import json

with open('SIDO_MAP_2022.json', encoding='utf-8') as f:
    geo_data = json.load(f)

sido_df = df.groupby('시도명').size().reset_index(name='카메라수')

fm.Choropleth(
    geo_data=geo_data,
    data=sido_df,
    columns=['시도명', '카메라수'],
    key_on='feature.properties.시도명',
    fill_color='YlOrRd',
    legend_name='카메라 수',
).add_to(m)
```

### 7.9 저장 · 노트북 표시

| 메서드 / 함수 | 필수 | 설명 |
|---------------|------|------|
| `m.save(filename)` | `filename` ★ | HTML 파일 저장 |
| `m.get_root().render()` | | HTML 문자열 반환 |
| `m._repr_html_()` | | Jupyter/Colab 인라인 표시 |

**Colab / VS Code 노트북용 헬퍼:**

```python
import base64
from pathlib import Path
from IPython.display import IFrame, display

def show_map(m, width=600, height=400, file='map.html'):
    html = m.get_root().render()
    path = Path(file)
    path.write_text(html, encoding='utf-8')
    if len(html) < 500_000:
        encoded = base64.b64encode(html.encode()).decode()
        display(IFrame(src=f'data:text/html;base64,{encoded}', width=width, height=height))
    else:
        display(IFrame(src=path.name, width=width, height=height))
        print(f'지도 크기 {len(html)/1024/1024:.1f}MB → {path.name} 저장 후 표시')
```

> 대용량 지도(히트맵·MarkerCluster)는 2MB 이상일 수 있어 파일로 저장 후 iframe 로드합니다.

### 7.10 pandas · geopandas 연동

```python
import geopandas as gpd

# CSV → 마커
for _, row in df.iterrows():
    fm.Marker([row['위도'], row['경도']], popup=row['시도명']).add_to(m)

# GeoDataFrame → GeoJson
gdf = gpd.read_file('SIDO_MAP_2022.json')
fm.GeoJson(
    gdf.to_json(),
    tooltip=fm.GeoJsonTooltip(fields=['시도명']),
).add_to(m)

# geopandas 인터랙티브 (folium 래퍼)
gdf.explore(column='카메라수', cmap='Blues', legend=True)
```

### 7.11 외부 GeoJSON URL

```python
import requests

world = requests.get(
    'https://raw.githubusercontent.com/python-visualization/folium-example-data/main/world_countries.json'
).json()

m = fm.Map(location=[20, 0], zoom_start=2)
fm.GeoJson(world, name='세계').add_to(m)
fm.LayerControl().add_to(m)
```

### 7.12 자주 하는 실수

| 증상 | 원인 | 해결 |
|------|------|------|
| 지도가 빈 화면 | iframe 용량 한도 | `show_map`으로 파일 저장 후 표시 |
| 마커 위치가 바다 | 위도·경도 순서 바뀜 | `[lat, lon]` 순서 확인 |
| GeoJSON 안 보임 | 좌표계 불일치 | WGS84 (`EPSG:4326`) 사용 |
| Choropleth 색 없음 | `key_on`과 data 키 불일치 | properties 키 이름 확인 |
| 한글 깨짐 | 팝업 인코딩 | UTF-8 HTML 사용 |

---

## 8. 라이브러리 선택 가이드

| 목적 | 추천 | 이유 |
|------|------|------|
| 논문·보고서 정적 그래프 | **matplotlib** | 세밀한 제어, PDF 저장 |
| 통계 EDA·분포·범주 비교 | **seaborn** | DataFrame 친화, 통계 plot 풍부 |
| 대시보드·인터랙티브 | **plotly** | 호버·줌·HTML 공유 |
| 지도·행정구역·공간 조인 | **geopandas** | geometry·CRS·choropleth |
| 지도 위 마커·히트맵 | **folium** (+ geopandas) | Leaflet 기반 웹 지도 |

### 조합 예시

```python
# 1) seaborn으로 EDA → matplotlib으로 저장
sns.histplot(data=df, x='size')
plt.savefig('hist.png')

# 2) geopandas로 공간 집계 → plotly choropleth
import plotly.express as px
fig = px.choropleth_map(
    kor, geojson=kor.geometry.__geo_interface__,
    locations=kor.index, color='카메라수',
)

# 3) geopandas → folium
kor.explore(column='카메라수')
```

# 4) folium으로 공공데이터 지도
from folium.plugins import HeatMap

m = fm.Map(location=[36.24, 128.10], zoom_start=7)
HeatMap(df[['위도', '경도']].values.tolist(), radius=10).add_to(m)
m.save('map.html')
```

---

## 9. 빠른 참조 — 필수 파라미터만

### matplotlib

```python
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, y)                          # y ★
ax.scatter(x, y)                       # y ★
ax.bar(x, height)                      # height ★
ax.hist(x)                             # x ★
ax.set_xlabel('label')                 # label ★
ax.set_title('title')                  # title ★
fig.savefig('out.png')                 # fname ★
```

### seaborn

```python
sns.scatterplot(data=df, x='col1', y='col2')   # data, x, y ★
sns.histplot(data=df, x='col1')                # data, x ★
sns.boxplot(data=df, x='cat', y='val')           # data, x, y ★
sns.heatmap(data_2d)                             # data ★
sns.heatmap(corr_matrix, annot=True)
```

### plotly express

```python
px.scatter(df, x='col1', y='col2')             # df, x, y ★
px.line(df, x='date', y='value')               # df, x, y ★
px.bar(df, x='cat', y='count')                 # df, x ★
px.histogram(df, x='col1')                     # df, x ★
px.imshow(matrix)                              # matrix ★
px.scatter_map(df, lat='lat', lon='lon')       # df, lat, lon ★
fig.show()
fig.write_html('chart.html')                   # path ★
```

### plotly graph_objects

```python
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y))            # y ★
fig.add_trace(go.Bar(x=cats, y=vals))          # y ★
fig.update_layout(title='제목')
fig.show()
```

### geopandas

```python
gdf = gpd.read_file('file.geojson')            # filename ★
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat))  # x,y ★
gdf = gdf.set_crs('EPSG:4326')                 # crs ★
gdf = gdf.to_crs('EPSG:5179')                  # epsg ★
gdf.plot(column='value', legend=True)          # column ★ (choropleth)
gdf.to_file('out.geojson', driver='GeoJSON')   # filename ★
gdf.explore(column='value')                    # 인터랙티브
```

### folium

```python
import folium as fm
from folium.plugins import HeatMap, MarkerCluster, MiniMap

m = fm.Map(location=[lat, lon], zoom_start=13)  # location ★
fm.Marker(location=[lat, lon], popup='text').add_to(m)  # location ★
fm.PolyLine(locations=[[lat1, lon1], [lat2, lon2]]).add_to(m)  # locations ★
fm.GeoJson(geojson_dict).add_to(m)               # data ★
HeatMap(data=[[lat, lon], ...]).add_to(m)      # data ★
MarkerCluster().add_to(m)
fm.LayerControl().add_to(m)
m.save('map.html')                               # filename ★
```

---

## 프로젝트 예시 데이터

| 파일 | 경로 | 활용 |
|------|------|------|
| army.csv | `visualization/matplotlib/` | scatter, bubble map |
| nightingale-rose-data.csv | `visualization/matplotlib/` | 극좌표·로즈 차트 |
| 전국무인교통단속카메라표준데이터.csv | `folium/` | 지도·히트맵·choropleth |
| SIDO_MAP_2022.json | `folium/` | 시도 경계 GeoJSON |
| 포항시 인구 CSV | `folium/포항시인구분포/` | 지역별 인구 시각화 |

```python
import pandas as pd

df = pd.read_csv('visualization/matplotlib/army.csv')
# columns: lon, lat, size, direction, division
```

---

## 참고

### 공식 문서

| 라이브러리 | 문서 | API / 가이드 |
|------------|------|--------------|
| matplotlib | https://matplotlib.org/stable/ | https://matplotlib.org/stable/api/index.html |
| seaborn | https://seaborn.pydata.org/ | https://seaborn.pydata.org/api.html |
| plotly | https://plotly.com/python/ | https://plotly.com/python-api-reference/ |
| geopandas | https://geopandas.org/ | https://geopandas.org/en/stable/docs.html |
| folium | https://python-visualization.github.io/folium/ | https://python-visualization.github.io/folium/plugins.html |

### PyPI · GitHub

| 라이브러리 | PyPI | GitHub |
|------------|------|--------|
| matplotlib | https://pypi.org/project/matplotlib/ | https://github.com/matplotlib/matplotlib |
| seaborn | https://pypi.org/project/seaborn/ | https://github.com/mwaskom/seaborn |
| plotly | https://pypi.org/project/plotly/ | https://github.com/plotly/plotly.py |
| geopandas | https://pypi.org/project/geopandas/ | https://github.com/geopandas/geopandas |
| folium | https://pypi.org/project/folium/ | https://github.com/python-visualization/folium |

### 관련 자료

- [branca](https://pypi.org/project/branca/) — folium HTML/iframe 유틸
- [Leaflet.js](https://leafletjs.com/) — folium 지도 엔진
- [leaflet-providers](https://leaflet-extras.github.io/leaflet-providers/preview) — 타일 레이어 미리보기
- [Shapely](https://shapely.readthedocs.io/) — geopandas geometry 엔진
- JSON 파일 로드: [json.md](./json.md)
- folium 실습 노트북: [basic.ipynb](../folium/basic.ipynb)
