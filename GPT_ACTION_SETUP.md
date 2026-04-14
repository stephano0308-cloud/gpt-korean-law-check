# GPT Action 설정 가이드

이 문서는 `gpt-korean-law-check` 서버를 ChatGPT의 Action으로 연결하는 절차를 설명합니다.

## 1. 서버 배포
먼저 FastAPI 서버를 외부 HTTPS URL로 배포합니다.

예시 실행:

```bash
pip install -r requirements.txt
uvicorn src.gpt_api:app --host 0.0.0.0 --port 8000
```

배포 후 예시 URL:

- `https://your-server-domain.com/health`
- `https://your-server-domain.com/docs`
- `https://your-server-domain.com/openapi.json`

## 2. OpenAPI 스키마 URL 준비
저장소의 `openapi.yaml` 파일에서 아래 값을 실제 서버 URL로 바꿉니다.

```yaml
servers:
  - url: https://your-server-domain.com
```

배포 서버에서도 같은 파일을 정적으로 노출하거나, GPT Action 설정 화면에 파일 내용을 직접 붙여넣으면 됩니다.

## 3. ChatGPT Action 추가
Custom GPT 설정 화면에서 Action 추가 후, `openapi.yaml` 내용을 붙여넣습니다.

핵심 엔드포인트:
- `GET /health`
- `POST /extract-hwpx-text`
- `POST /analyze-case-document`
- `POST /review-related-laws`

## 4. 권장 GPT 지시문
아래 지시문을 Custom GPT Instructions에 넣는 것을 권장합니다.

```text
너는 조세사건 관련법령 검토 보조 GPT다.

사용자가 업로드한 HWPX 또는 사건 문서 텍스트를 바탕으로 다음 작업을 수행한다.
1. 문서가 HWPX이면 extractHwpxText 액션으로 텍스트를 추출한다.
2. analyzeCaseDocument 액션으로 사건의 날짜, 쟁점, 관련법령 기재를 구조화한다.
3. reviewRelatedLaws 액션으로 파일에 기재된 관련법령의 유지 가능, 수정 필요, 추가 필요 여부를 검토한다.
4. 결과는 한국어로 다음 순서에 따라 정리한다.
   - 사건 요약
   - 쟁점별 기준일
   - 파일상 관련법령 검토 결과
   - 추가 필요 법령
   - 부칙/연혁 검토 의견
   - 조사서 반영용 수정 문안
5. 확인되지 않은 내용은 추정하지 말고 “추가 확인 필요”라고 표시한다.
```

## 5. 추천 호출 순서

### 문서 텍스트가 있는 경우
1. `analyzeCaseDocument`
2. `reviewRelatedLaws`

### HWPX 파일만 있는 경우
1. `extractHwpxText`
2. `analyzeCaseDocument`
3. `reviewRelatedLaws`

## 6. 주의사항
- 현재 버전은 연혁법령 특정 버전 고정 조회가 미구현입니다.
- 따라서 결과에 표시되는 연혁 검토 의견은 현행 본문 fallback 기반입니다.
- 후속 구현 시 `history_tools.py`를 확장하면 같은 Action 구조를 유지한 채 정밀도를 높일 수 있습니다.
