# EventRadar

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

컨퍼런스, 전시회, 제품 출시, 세일 이벤트 관련 뉴스를 자동 수집하고 이벤트 영향도를 분석하는 레이더 프로젝트입니다.

## 프로젝트 목표

- **이벤트 뉴스 자동 수집**: CES, MWC, WWDC 등 주요 행사와 전시, 런칭, 세일 관련 뉴스를 일일 수집
- **영향도 분석**: MCP `event_impact` 도구로 이벤트 카테고리별 언급 빈도와 영향력 자동 분석
- **참여 우선순위 제안**: 컨퍼런스, 전시, 런칭, 페스티벌, 세일 카테고리별 트렌드 리포트 생성
- **일정 추적**: 행사 관련 뉴스를 시간순으로 추적하여 준비 및 참여 타이밍 지원
- **AI 연동 검색**: MCP 서버를 통해 AI 어시스턴트에서 이벤트 정보를 자연어로 검색

## 주요 기능

1. **RSS 자동 수집**: TechCrunch, The Verge, Eventbrite Blog 등에서 이벤트 관련 기사 수집
2. **엔티티 매칭**: 컨퍼런스, 전시/박람회, 출시/런칭, 페스티벌, 세일/할인 5개 카테고리
3. **DuckDB 저장**: UPSERT 시맨틱으로 중복 없는 기사 저장
4. **JSONL 원본 보존**: `data/raw/YYYY-MM-DD/{source}.jsonl`
5. **SQLite FTS5 검색**: 전문검색으로 빠른 이벤트 검색
6. **자연어 쿼리**: "최근 1주 CES 관련 5개" 같은 한국어/영어 검색
7. **HTML 리포트**: 이벤트 카테고리별 통계가 포함된 자동 리포트
8. **MCP 서버**: search, recent_updates, sql, top_trends, event_impact

## 빠른 시작

```bash
pip install -r requirements.txt
python main.py --category event --recent-days 7
```

## 프로젝트 구조

```
EventRadar/
├── eventradar/
│   ├── collector.py       # RSS 수집
│   ├── analyzer.py        # 엔티티 키워드 매칭
│   ├── storage.py         # DuckDB 스토리지
│   ├── reporter.py        # HTML 리포트
│   ├── raw_logger.py      # JSONL 원본 기록
│   ├── search_index.py    # SQLite FTS5
│   ├── nl_query.py        # 자연어 쿼리 파서
│   └── mcp_server/        # MCP 서버 (5개 도구)
├── config/categories/event.yaml
├── tests/
├── .github/workflows/
└── main.py
```

## MCP 서버 도구

| 도구 | 설명 |
|------|------|
| `search` | FTS5 기반 자연어 검색 |
| `recent_updates` | 최근 수집 기사 조회 |
| `sql` | 읽기 전용 SQL 쿼리 |
| `top_trends` | 엔티티 언급 빈도 트렌드 |
| `event_impact` | 이벤트 카테고리별 영향도 분석 |

## 테스트

```bash
pytest tests/ -v
```
