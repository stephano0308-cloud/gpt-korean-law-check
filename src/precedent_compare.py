from typing import Dict, List, Optional

from .precedent_tools import get_precedent_detail, search_precedents, search_tax_tribunal_cases
from .tax_case_review import summarize_case


def _build_query(overview: Dict) -> str:
    issues = overview.get("issues", [])[:2]
    refs = overview.get("law_references", [])[:3]
    parts: List[str] = []
    for issue in issues:
        parts.append(issue)
    for ref in refs:
        if ref.get("law_name"):
            parts.append(ref["law_name"])
        if ref.get("article"):
            parts.append(f"제{ref['article']}조")
    return " ".join(dict.fromkeys(parts))


def _shorten(text: str, max_len: int = 250) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    return text if len(text) <= max_len else text[:max_len] + "…"


def _compare_direction(user_judgment: str, precedent_text: str) -> Dict:
    if not precedent_text:
        return {"공통점": "관련 선례 추가 확인 필요", "차이점": "관련 선례 추가 확인 필요"}
    user_has_invalid = any(token in user_judgment for token in ["무효", "취소", "환급", "감면"])
    prec_has_invalid = any(token in precedent_text for token in ["무효", "취소", "환급", "감면"])
    if user_has_invalid == prec_has_invalid:
        common = "핵심 결론의 방향이 대체로 유사합니다."
        diff = "세부 사실관계와 적용 법리는 추가 비교가 필요합니다."
    else:
        common = "핵심 쟁점 자체는 유사합니다."
        diff = "**사용자 문서의 판단 방향과 선례의 결론 방향이 다를 가능성이 있습니다.**"
    return {"공통점": common, "차이점": diff}


def compare_with_precedents(document_text: str, user_final_judgment: Optional[str] = None, arguments: Optional[dict] = None) -> Dict:
    overview = summarize_case(document_text)
    query = _build_query(overview)

    supreme = search_precedents(query, page=1, page_size=5, arguments=arguments)
    tribunal = search_tax_tribunal_cases(query, page=1, page_size=5, arguments=arguments)

    supreme_items = supreme.get("precedents", [])[:3]
    tribunal_items = tribunal.get("decisions", [])[:3]

    detailed_supreme = []
    for item in supreme_items:
        pid = item.get("판례일련번호")
        detail = get_precedent_detail(pid, arguments=arguments) if pid else {}
        detailed_supreme.append({
            "사건번호": item.get("사건번호"),
            "사건명": item.get("사건명"),
            "선고일자": item.get("선고일자"),
            "법원명": item.get("법원명"),
            "판시사항": _shorten(detail.get("판시사항") or item.get("판시사항")),
            "판결요지": _shorten(detail.get("판결요지") or item.get("판결요지")),
            "판례일련번호": pid,
        })

    summarized_tribunal = []
    for item in tribunal_items:
        summarized_tribunal.append({
            "사건번호": item.get("사건번호"),
            "사건명": item.get("사건명"),
            "재결일자": item.get("재결일자"),
            "재결기관": item.get("재결기관"),
            "재결요지": _shorten(item.get("재결요지")),
            "일련번호": item.get("일련번호"),
        })

    comparison_rows = []
    issues = overview.get("issues", []) or ["적용법령 적정성"]
    judgment_text = user_final_judgment or document_text[-1000:]
    for issue in issues[:3]:
        tribunal_text = summarized_tribunal[0].get("재결요지", "") if summarized_tribunal else ""
        supreme_text = detailed_supreme[0].get("판결요지", "") if detailed_supreme else ""
        tribunal_cmp = _compare_direction(judgment_text, tribunal_text)
        supreme_cmp = _compare_direction(judgment_text, supreme_text)
        comparison_rows.append({
            "비교항목": issue,
            "사용자파일판단": _shorten(judgment_text, 180),
            "조세심판원선결정례": tribunal_text or "관련 선결정례 추가 확인 필요",
            "대법원판례": supreme_text or "관련 판례 추가 확인 필요",
            "공통점": tribunal_cmp["공통점"] if tribunal_text else supreme_cmp["공통점"],
            "차이점": tribunal_cmp["차이점"] if tribunal_text else supreme_cmp["차이점"],
        })

    return {
        "query": query,
        "overview": overview,
        "similar_tax_tribunal_decisions": summarized_tribunal,
        "similar_supreme_court_cases": detailed_supreme,
        "precedent_comparison": comparison_rows,
        "limitations": [
            "조세심판원 선결정례 검색은 국가법령정보센터 행정심판/재결례 검색 target에 의존합니다.",
            "보조 검색원(케이스노트, 유렉스)은 현재 서버 코드에 미연동이며 후속 확장 대상입니다.",
        ],
    }
