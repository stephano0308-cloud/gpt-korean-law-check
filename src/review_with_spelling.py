from typing import Dict, Optional

from .spell_checker import KoreanSpellChecker
from .tax_case_review import review_related_laws


def review_document_with_spelling(document_text: str, extra_words: Optional[set] = None, arguments: Optional[dict] = None) -> Dict:
    law_review = review_related_laws(document_text, arguments=arguments)
    checker = KoreanSpellChecker(extra_words=extra_words)
    spelling_review = checker.check_text(document_text)
    return {
        "law_review": law_review,
        "spelling_review": spelling_review,
        "summary": {
            "reviewed_law_count": len(law_review.get("reviewed_laws", [])),
            "additional_law_count": len(law_review.get("additional_suggestions", [])),
            "spelling_issue_count": spelling_review.get("summary", {}).get("count", 0),
        },
    }
