# Precedent Comparison Integration

조세사건 문서의 쟁점과 유사한 조세심판원 선결정례 및 대법원 판례를 검색하고, 사용자 파일의 판단과 공통점/차이점을 비교분석하는 기능을 추가했습니다.

## 추가된 파일
- `src/precedent_tools.py`
- `src/precedent_compare.py`
- `src/gpt_api_precedent.py`

## 엔드포인트
- `POST /search-supreme-court-precedents`
- `POST /search-tax-tribunal-decisions`
- `POST /compare-with-precedents`

## 검색 우선순위
1. 국가법령정보센터 API 기반 공식 검색
2. 케이스노트/유렉스 등 보조 검색은 후속 확장 대상

## 비교분석 출력
- 유사 조세심판원 선결정례 목록
- 유사 대법원 판례 목록
- 사용자 파일의 최종 판단 vs 선례의 판단 방향 비교표
- 공통점 / 차이점 요약

## 주의사항
- 조세심판원 선결정례 검색은 국가법령정보센터의 행정심판/재결례 검색 target에 의존하므로, 실제 서비스 환경에서 응답 구조를 확인하며 보정이 필요할 수 있습니다.
- 보조 검색원(케이스노트, 유렉스)은 현재 서버 코드에 연동되어 있지 않습니다.
