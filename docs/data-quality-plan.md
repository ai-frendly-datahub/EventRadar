# Data Quality Plan

- 생성 시각: `2026-04-23T14:45:24.863320+00:00`
- 우선순위: `P1`
- 데이터 품질 점수: `70`
- 가장 약한 축: `운영 깊이`
- Governance: `medium`
- Primary Motion: `intelligence`

## 현재 이슈

- 비활성 고가치 source 3개가 있어 freshness와 traceability가 떨어짐
- 가장 약한 품질 축은 운영 깊이(35)

## 필수 신호

- 공식 행사 일정과 venue calendar
- 티켓 오픈·잔여석·매진 상태
- 스폰서·참가사·연사 같은 B2B 전환 신호

## 품질 게이트

- 행사일·티켓 오픈일·수집일을 별도 필드로 유지
- 동일 행사의 지역/회차/온라인 여부를 canonical key로 분리
- 미디어 소개 기사와 공식 등록/티켓 source를 분리

## 다음 구현 순서

- official calendar와 ticket availability source를 우선 추가
- venue id와 event occurrence id 정규화 규칙을 추가
- 참가사/스폰서 entity를 리드 발굴용 필드로 추출

## 운영 규칙

- 원문 URL, 수집일, 이벤트 발생일은 별도 필드로 유지한다.
- 공식 source와 커뮤니티/시장 source를 같은 신뢰 등급으로 병합하지 않는다.
- collector가 인증키나 네트워크 제한으로 skip되면 실패를 숨기지 말고 skip 사유를 기록한다.
- 이 문서는 `scripts/build_data_quality_review.py --write-repo-plans`로 재생성한다.
