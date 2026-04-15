from typing import Dict, List


def build_case_report(review_result: Dict) -> str:
    overview = review_result.get("overview", {})
    reviewed = review_result.get("reviewed_laws", [])
    additions = review_result.get("additional_suggestions", [])
    lines: List[str] = []
    lines.append("# Case Report")
    lines.append("")
    lines.append("## 사건 개요")
    lines.append(f"- 식별된 쟁점 수: {len(overview.get('issues', []))}")
    lines.append(f"- 식별된 관련법령 수: {len(overview.get('law_references', []))}")
    lines.append(f"- 검토 완료 법령 수: {len(reviewed)}")
    lines.append(f"- 추가 제안 법령 수: {len(additions)}")
    lines.append("")
    lines.append("## 쟁점")
    for issue in overview.get("issues", []):
        lines.append(f"- {issue}")
    lines.append("")
    lines.append("## 기준일")
    for issue, dates in overview.get("basis_dates_by_issue", {}).items():
        joined = ", ".join(dates) if dates else "추가 확인 필요"
        lines.append(f"- {issue}: {joined}")
    lines.append("")
    lines.append("## 검토결과 요약")
    for item in reviewed:
        lines.append(f"- {item.get('reference')}: {item.get('status')} / {item.get('reason')}")
    if additions:
        lines.append("")
        lines.append("## 추가 검토 제안")
        for item in additions:
            lines.append(f"- {item.get('suggestion')}: {item.get('reason')}")
    return "\n".join(lines)
