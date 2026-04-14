import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from .hwpx_parser import extract_hwpx_text
from .tax_case_review import review_related_laws, summarize_case

load_dotenv()

app = FastAPI(
    title="GPT Korean Law Check API",
    version="1.0.0",
    description="조세사건 관련법령 검토를 위한 GPT용 FastAPI 서버",
    servers=[
        {"url": "https://gpt-korean-law-check-production.up.railway.app"}
    ],
)


class ExtractHwpxRequest(BaseModel):
    hwpx_base64: str = Field(..., description="base64 인코딩된 HWPX 파일")


class AnalyzeCaseDocumentRequest(BaseModel):
    document_text: str = Field(..., description="사건 문서 텍스트")


class ReviewRelatedLawsRequest(BaseModel):
    document_text: str = Field(..., description="사건 문서 텍스트")
    include_law_text: bool = Field(False, description="조문 본문 포함 여부")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "GPT Korean Law Check API",
        "law_api_key": "configured" if os.environ.get("LAW_API_KEY") else "missing",
    }


@app.post("/extract-hwpx-text")
async def extract_hwpx_text_route(request: ExtractHwpxRequest) -> dict:
    return await asyncio.to_thread(extract_hwpx_text, hwpx_base64=request.hwpx_base64)


@app.post("/analyze-case-document")
async def analyze_case_document_route(request: AnalyzeCaseDocumentRequest) -> dict:
    return await asyncio.to_thread(summarize_case, request.document_text)


@app.post("/review-related-laws")
async def review_related_laws_route(request: ReviewRelatedLawsRequest) -> dict:
    result = await asyncio.to_thread(review_related_laws, request.document_text)
    if not request.include_law_text:
        for item in result.get("reviewed_laws", []):
            item.pop("article_text", None)
    return result
