from typing import Dict, List


def _bold_if_changed(user_text: str, reviewed_text: str) -> str:
    if not user_text:
        return f"**{reviewed_text}**"
    return reviewed_text if user_text.strip() == reviewed_text.strip() else f"**{reviewed_text}**"


def build_comparison_rows(document_refs: List[Dict], reviewed_laws: List[Dict], additional_suggestions: List[Dict]) -> List[Dict]:
    rows: List[Dict] = []
    reviewed_index = {item.get('reference'): item for item in reviewed_laws}
    for ref in document_refs:
        user_side = ref.get('display') or ref.get('law_name')
        reviewed = reviewed_index.get(ref.get('display'))
        if reviewed:
            reviewed_side = reviewed.get('formatted_article_label') or reviewed.get('reference')
            rows.append({
                'left': user_side,
                'right': _bold_if_changed(user_side, reviewed_side),
            })
        else:
            rows.append({'left': user_side, 'right': '추가 확인 필요'})
    for item in additional_suggestions:
        suggestion = item.get('suggestion')
        rows.append({'left': '기재 없음', 'right': f"**{suggestion}**"})
    return rows


def build_markdown_output(review_result: Dict) -> str:
    overview = review_result.get('overview', {})
    rows = build_comparison_rows(
        overview.get('law_references', []),
        review_result.get('reviewed_laws', []),
        review_result.get('additional_suggestions', []),
    )
    lines: List[str] = []
    lines.append('## 관련 법령 비교표')
    lines.append('')
    lines.append('| 사용자 파일상 내용 정리 | GPT 검토 결과 정리 |')
    lines.append('|---|---|')
    for row in rows:
        left = str(row.get('left', '')).replace('\n', '<br>')
        right = str(row.get('right', '')).replace('\n', '<br>')
        lines.append(f'| {left} | {right} |')
    lines.append('')
    lines.append('## 관련 법령 정리본')
    for item in review_result.get('reviewed_laws', []):
        history = item.get('history_detail_output') or {}
        label = history.get('적용연혁표시') or item.get('formatted_article_label') or item.get('reference')
        lines.append(f"- {label}")
        addendum = item.get('addendum_detail_output') or {}
        if addendum.get('부칙존재여부'):
            lines.append("  - 부칙 검토: 있음")
            for text in addendum.get('시행일', [])[:2]:
                lines.append(f"  - 시행일: {text}")
            for text in addendum.get('적용례', [])[:2]:
                lines.append(f"  - 적용례: {text}")
            for text in addendum.get('경과조치', [])[:2]:
                lines.append(f"  - 경과조치: {text}")
    return '\n'.join(lines)
