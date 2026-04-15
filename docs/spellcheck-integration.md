# Spellcheck Integration

`hwpx-typo-checker` 저장소의 구조를 참고하여 `gpt-korean-law-check`에 맞춤법/오탈자 검토 기능을 보조 단계로 추가했습니다.

## 추가된 파일
- `src/spell_checker.py`
- `src/review_with_spelling.py`
- `src/gpt_api_spellcheck.py`

## 핵심 기능
- HWPX 또는 텍스트 문서의 오탈자/명백한 맞춤법 오류 후보 탐지
- 법령 검토와 맞춤법 검토를 함께 반환하는 통합 리뷰 엔드포인트
- `kiwipiepy`가 없으면 오류 대신 `missing_dependency` 상태를 반환

## 엔드포인트
- `POST /check-spelling`
- `POST /review-document`

## 비고
- 현재 구현은 원 저장소의 전체 GUI/CSV 저장 구조를 그대로 이식한 것이 아니라, GPT/Action 연동에 필요한 핵심 검사 로직만 경량화하여 반영한 버전입니다.
- 실제 검출 정확도를 높이려면 배포 환경에 `kiwipiepy` 설치가 필요합니다.
