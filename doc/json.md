# JSON 파일 핸들링 가이드

JSON(JavaScript Object Notation)은 데이터를 **키-값** 형태로 저장·교환하는 텍스트 형식입니다.  
Python에서는 표준 라이브러리 `json` 모듈로 대부분의 작업을 처리할 수 있습니다.

---

## 1. JSON 기본 구조

| 타입 | Python 대응 | 예시 |
|------|-------------|------|
| 객체(object) | `dict` | `{"name": "홍길동", "age": 30}` |
| 배열(array) | `list` | `[1, 2, 3]` |
| 문자열 | `str` | `"hello"` |
| 숫자 | `int`, `float` | `42`, `3.14` |
| 불리언 | `bool` | `true`, `false` |
| null | `None` | `null` |

```json
{
  "camera_id": 35,
  "location": {
    "lat": 35.237677,
    "lon": 129.013767
  },
  "tags": ["단속", "과속"],
  "active": true
}
```

---

## 2. Python `json` 모듈 4가지 함수

| 함수 | 입력 | 출력 | 용도 |
|------|------|------|------|
| `json.load()` | 파일 객체 | Python 객체 | **JSON 파일 읽기** |
| `json.loads()` | 문자열 | Python 객체 | **JSON 문자열 → Python** |
| `json.dump()` | Python 객체 → 파일 | - | **JSON 파일 쓰기** |
| `json.dumps()` | Python 객체 | 문자열 | **Python → JSON 문자열** |

> `load` / `dump` → **파일**, `loads` / `dumps` → **문자열**

---

## 3. JSON 파일 읽기

### 3.1 기본 읽기

```python
import json
from pathlib import Path

path = Path('data/cameras.json')

with path.open(encoding='utf-8') as f:
    data = json.load(f)

print(type(data))   # dict 또는 list
print(data['camera_id'])
```

### 3.2 `pathlib` + 존재 확인

```python
from pathlib import Path
import json

path = Path('data/cameras.json')

if not path.exists():
    raise FileNotFoundError(f'파일 없음: {path}')

with path.open(encoding='utf-8') as f:
    data = json.load(f)
```

### 3.3 여러 JSON 파일 한꺼번에 읽기

```python
import json
from pathlib import Path

folder = Path('data')
records = []

for file in folder.glob('*.json'):
    with file.open(encoding='utf-8') as f:
        records.append(json.load(f))
```

---

## 4. JSON 파일 쓰기

### 4.1 기본 쓰기

```python
import json
from pathlib import Path

data = {
    'name': '무인교통단속카메라',
    'count': 43062,
    'regions': ['부산', '서울'],
}

path = Path('output/result.json')
path.parent.mkdir(parents=True, exist_ok=True)

with path.open('w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 4.2 자주 쓰는 옵션

| 옵션 | 설명 |
|------|------|
| `ensure_ascii=False` | 한글 등 비ASCII 문자를 그대로 저장 |
| `indent=2` | 보기 좋게 들여쓰기 (개발·학습용) |
| `indent=None` | 한 줄로 압축 (용량 최소화) |

```python
json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 5. 문자열 ↔ Python 변환

API 응답이나 DB에서 받은 JSON **문자열**을 다룰 때 사용합니다.

```python
import json

# 문자열 → Python
text = '{"city": "부산", "year": 2025}'
obj = json.loads(text)
print(obj['city'])  # 부산

# Python → 문자열
obj = {'city': '부산', 'year': 2025}
text = json.dumps(obj, ensure_ascii=False)
print(text)  # {"city": "부산", "year": 2025}
```

---

## 6. 중첩 데이터 접근

```python
import json

with open('data/response.json', encoding='utf-8') as f:
    data = json.load(f)

# 중첩 키 접근
items = data['response']['body']['items']

# 키가 없을 때 기본값
items = data.get('response', {}).get('body', {}).get('items', [])

# 단일 객체 vs 리스트 통일 (API에서 자주 발생)
if isinstance(items, dict):
    items = [items]

for item in items:
    print(item.get('latitude'), item.get('longitude'))
```

---

## 7. API 응답 JSON 처리

`requests`로 API를 호출할 때 `.json()` 메서드를 사용합니다.

```python
import requests

url = 'https://api.example.com/data'
params = {'pageNo': 1, 'numOfRows': 100, 'type': 'json'}

response = requests.get(url, params=params)
response.raise_for_status()   # HTTP 오류 시 예외 발생

data = response.json()
items = data['response']['body'].get('items', [])
```

응답을 파일로 저장해 두고 싶다면:

```python
import json

with open('api_response.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 8. pandas와 JSON

표 형태 데이터는 pandas가 편리합니다.

```python
import pandas as pd

# JSON 파일 → DataFrame
df = pd.read_json('data/cameras.json')

# JSON Lines (.jsonl) — 한 줄에 하나의 JSON 객체
df = pd.read_json('data/cameras.jsonl', lines=True)

# DataFrame → JSON 파일
df.to_json('output/cameras.json', orient='records', force_ascii=False, indent=2)
```

| `orient` | 결과 형태 |
|----------|-----------|
| `records` | `[{...}, {...}]` — 행 단위 리스트 (가장 흔함) |
| `index` | `{인덱스: {...}}` |
| `columns` | `{컬럼: [값들]}` |
| `values` | `[[값들]]` |

---

## 9. 에러 처리

```python
import json
from pathlib import Path

path = Path('data/cameras.json')

try:
    with path.open(encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f'파일을 찾을 수 없습니다: {path}')
except json.JSONDecodeError as e:
    print(f'JSON 형식 오류: {e.msg} (line {e.lineno}, col {e.colno})')
```

### 자주 나는 오류

| 오류 | 원인 | 해결 |
|------|------|------|
| `JSONDecodeError` | 따옴표 누락, 마지막 쉼표(trailing comma) | [jsonlint.com](https://jsonlint.com) 등으로 검증 |
| `UnicodeDecodeError` | 인코딩 불일치 | `encoding='utf-8'` 또는 `encoding='cp949'` 지정 |
| `TypeError` | `set`, `datetime` 등 JSON 미지원 타입 | 변환 후 저장 (아래 참고) |

### JSON에 저장할 수 없는 타입 변환

```python
import json
from datetime import datetime

def json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'직렬화 불가: {type(obj)}')

data = {'created_at': datetime.now()}
text = json.dumps(data, default=json_default, ensure_ascii=False)
```

---

## 10. JSON Lines (.jsonl)

대용량 로그·데이터는 **한 줄에 JSON 하나** 형식을 많이 씁니다.

```python
import json

# 쓰기
records = [{'id': 1, 'city': '부산'}, {'id': 2, 'city': '서울'}]
with open('data/log.jsonl', 'w', encoding='utf-8') as f:
    for row in records:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')

# 읽기
rows = []
with open('data/log.jsonl', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            rows.append(json.loads(line))
```

---

## 11. 실무 팁

1. **항상 `encoding='utf-8'` 명시** — 한글 깨짐 방지
2. **`ensure_ascii=False`** — 한글이 `\uXXXX`로 이스케이프되지 않게
3. **`with` 문 사용** — 파일 자동 닫기
4. **`pathlib.Path`** — 경로 처리를 OS 독립적으로
5. **원본 보존** — API 응답은 가공 전 `raw.json`으로 저장해 두면 디버깅에 유리
6. **스키마 확인** — 키 이름·타입이 바뀌는 API는 `.get()`으로 안전하게 접근

---

## 12. 한 번에 정리 — 읽기 · 수정 · 저장

```python
import json
from pathlib import Path

path = Path('data/cameras.json')

# 1) 읽기
with path.open(encoding='utf-8') as f:
    data = json.load(f)

# 2) 수정
data['updated'] = True
if 'cameras' in data:
    data['cameras'].append({'id': 99, 'city': '대구'})

# 3) 저장
out = Path('output/cameras_updated.json')
out.parent.mkdir(parents=True, exist_ok=True)

with out.open('w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'저장 완료: {out}')
```

---

## 참고

- [Python json 공식 문서](https://docs.python.org/3/library/json.html)
- [JSON 소개 (MDN)](https://developer.mozilla.org/ko/docs/Learn_web_development/Core/Scripting/JSON)
- 프로젝트 내 API JSON 처리 예: `folium/basic.ipynb` 6.1절 (`response.json()`)
