# EVENTRADAR

RSS 피드와 웹 크롤링을 통해 다양한 이벤트 정보를 수집하고, 카테고리별 분류 및 트렌드 분석을 수행합니다.

## STRUCTURE

```
EventRadar/
├── eventradar/
│   ├── collector.py              # collect_sources() — RSS 피드 및 웹 크롤링
│   ├── analyzer.py               # apply_entity_rules() — 이벤트 유형별 키워드 매칭 (콘서트, 전시, 세미나, 스포츠 등)
│   ├── reporter.py               # generate_report() — Jinja2 HTML
│   ├── storage.py                # RadarStorage — DuckDB upsert/query/retention
│   ├── models.py                 # Source, Article, EntityDefinition, CategoryConfig
│   ├── config_loader.py          # YAML 로딩
│   ├── logger.py                 # structlog 구조화 로깅
│   ├── notifier.py               # Email/Webhook 알림
│   ├── raw_logger.py             # JSONL 원시 로깅
│   ├── search_index.py           # SQLite FTS5 전문 검색
│   ├── nl_query.py               # 자연어 쿼리 파서
│   ├── common/                   # 공유 유틸리티
│   └── mcp_server/               # MCP 서버 (server.py + tools.py)
├── config/
│   ├── config.yaml               # database_path, report_dir, raw_data_dir, search_db_path
│   └── categories/event.yaml  # 소스 + 엔티티 정의
├── data/                         # DuckDB, search_index.db, raw/ JSONL
├── reports/                      # 생성된 HTML 리포트
├── tests/unit/                   # pytest 단위 테스트
├── main.py                       # CLI 엔트리포인트
└── .github/workflows/radar-crawler.yml
```

## ENTITIES

| Entity | Examples |
|--------|----------|
| Conference | conference, summit, forum, 학회 |
| Exhibition | exhibition, expo, trade show, 박람회 |
| Festival | festival, carnival, celebration, 축제 |
| Performance | concert, theater, live, 공연 |

## DEVIATIONS FROM TEMPLATE

- 행사일, 티켓 오픈일, 수집일을 별도 필드로 유지한다.
- 공식 행사 캘린더, 티켓 availability, venue calendar, exhibitor/sponsor 신호를 분리한다.
- 일반 문화/연예 뉴스는 행사·공연·전시 신호가 있을 때만 리포트에 반영한다.

## COMMANDS

```bash
python main.py --category event --recent-days 7
python main.py --category event --per-source-limit 50 --keep-days 90
```
