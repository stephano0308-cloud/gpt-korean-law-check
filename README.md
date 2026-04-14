# gpt-korean-law-check

조세사건 관련법령 검토를 위한 GPT용 FastAPI 서버입니다.

주요 기능:
- HWPX 텍스트 추출
- 사건 문서 분석(쟁점, 날짜 맥락, 관련법령 추출)
- 관련법령 검토(기준일, 부칙, 연혁 검토 인터페이스 포함)
- GPT Action/OpenAPI용 HTTP 라우터 제공

## 실행

```bash
pip install -r requirements.txt
uvicorn src.gpt_api:app --host 0.0.0.0 --port 8000
```

## 주요 엔드포인트
- `GET /health`
- `POST /extract-hwpx-text`
- `POST /analyze-case-document`
- `POST /review-related-laws`

## 환경 변수
- `LAW_API_KEY`: 국가법령정보센터 Open API 키
- `LAW_API_URL`: 기본값 `https://www.law.go.kr/DRF`

## 비고
현재 버전은 공식 법령 상세 본문과 부칙 문구를 활용한 실무형 휴리스틱 검토기입니다. 연혁법령 특정 버전 고정 조회는 후속 확장 대상입니다.
