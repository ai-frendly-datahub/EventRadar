# EventRadar

행사/이벤트(컨퍼런스, 전시, 런칭, 페스티벌, 세일) 관련 RSS를 수집하고,
키워드 기반 엔티티 매칭 후 DuckDB 저장과 HTML 리포트 생성을 수행하는 경량 Radar 프로젝트입니다.

## Quick Start

```bash
pip install -r requirements.txt
python main.py --category event --recent-days 7
```

- 리포트 출력: `reports/event_report.html`
- 기본 DB 경로: `data/radar_data.duckdb`

## Test

```bash
pytest tests/ -v
```
