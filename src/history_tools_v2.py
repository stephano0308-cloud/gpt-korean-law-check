from typing import Dict, List, Optional

from .tools import get_law_detail, search_law


class HistoryResolutionError(Exception):
    pass


def resolve_law_candidates(law_name: str, arguments: Optional[dict] = None) -> Dict:
    response = search_law(law_name, page=1, page_size=20, arguments=arguments)
    candidates = response.get("laws", []) if isinstance(response, dict) else []
    return {
        "query": law_name,
        "count": len(candidates),
        "candidates": candidates,
    }


def _extract_promulgation_display(candidate: Dict) -> Optional[str]:
    promulgation_date = candidate.get("공포일자") or ""
    promulgation_no = candidate.get("공포번호") or ""
    if promulgation_date and promulgation_no:
        return f"{promulgation_date} 공포 제{promulgation_no}호"
    if promulgation_date:
        return f"{promulgation_date} 공포"
    return None


def _build_version_label(candidate: Dict, effective_date: Optional[str]) -> str:
    law_name = candidate.get("법령명") or candidate.get("법령명_약칭") or "법령명 확인 필요"
    promulgation_date = candidate.get("공포일자")
    promulgation_no = candidate.get("공포번호")
    if promulgation_date and promulgation_no:
        return f"{law_name}({promulgation_date} 공포 법령 제{promulgation_no}호, 시행일자 {effective_date or '확인 필요'})"
    if effective_date:
        return f"{law_name}(시행일자 {effective_date})"
    return f"{law_name}(처분 당시 적용 연혁본 추가 확인 필요)"


def _extract_addendum_summary(detail: Dict) -> Dict:
    result = {
        "has_addendum": False,
        "addendum_articles": [],
        "effective_date_rules": [],
        "application_rules": [],
        "transition_rules": [],
    }
    for article in detail.get("조문", []):
        article_no = article.get("조문번호", "")
        title = article.get("조문제목", "")
        content = article.get("조문내용", "")
        text = " ".join(filter(None, [article_no, title, content]))
        if "부칙" not in text:
            continue
        result["has_addendum"] = True
        result["addendum_articles"].append({
            "조문번호": article_no or "부칙",
            "조문제목": title or None,
            "조문내용": content or None,
        })
        if "시행" in text and text not in result["effective_date_rules"]:
            result["effective_date_rules"].append(text[:500])
        if any(token in text for token in ["적용", "최초로"]) and text not in result["application_rules"]:
            result["application_rules"].append(text[:500])
        if any(token in text for token in ["종전의 규정", "경과조치"]) and text not in result["transition_rules"]:
            result["transition_rules"].append(text[:500])
    return result


def resolve_current_law_detail(law_name: str, arguments: Optional[dict] = None) -> Dict:
    candidates = resolve_law_candidates(law_name, arguments=arguments)
    if not candidates["candidates"]:
        raise HistoryResolutionError(f"법령 검색 결과 없음: {law_name}")
    selected = candidates["candidates"][0]
    law_id = selected.get("법령ID")
    detail = get_law_detail(law_id, arguments=arguments)
    return {
        "selected_candidate": selected,
        "selected_law_id": law_id,
        "selected_law_name": detail.get("법령명") or law_name,
        "current_effective_date": detail.get("시행일자"),
        "current_promulgation_display": _extract_promulgation_display(selected),
        "current_version_label": _build_version_label(selected, detail.get("시행일자")),
        "addendum_summary": _extract_addendum_summary(detail),
        "detail": detail,
        "history_mode": "current-detail-fallback",
    }


def analyze_history_applicability(law_name: str, basis_dates: Optional[List[str]] = None, arguments: Optional[dict] = None) -> Dict:
    basis_dates = basis_dates or []
    current = resolve_current_law_detail(law_name, arguments=arguments)
    addendum_summary = current.get("addendum_summary") or {}
    return {
        "law_name": law_name,
        "basis_dates": basis_dates,
        "history_status": "연혁 직접확정 불가",
        "history_mode": current.get("history_mode"),
        "selected_law_id": current.get("selected_law_id"),
        "selected_law_name": current.get("selected_law_name"),
        "current_effective_date": current.get("current_effective_date"),
        "current_promulgation_display": current.get("current_promulgation_display"),
        "current_version_label": current.get("current_version_label"),
        "candidate_count": len(resolve_law_candidates(law_name, arguments=arguments).get("candidates", [])),
        "review_note": "공식 연혁버전 특정 조회가 아직 구현되지 않아 현행 상세 본문을 기준으로 검토했습니다. 처분 당시 적용본 확정은 후속 연혁 API 구현이 필요합니다.",
        "history_detail_output": {
            "적용연혁표시": current.get("current_version_label"),
            "시행일자": current.get("current_effective_date"),
            "공포표시": current.get("current_promulgation_display"),
            "부칙존재여부": addendum_summary.get("has_addendum", False),
            "부칙세부내역": addendum_summary.get("addendum_articles", []),
            "시행일규칙": addendum_summary.get("effective_date_rules", []),
            "적용례": addendum_summary.get("application_rules", []),
            "경과조치": addendum_summary.get("transition_rules", []),
        },
    }
