import re
from typing import Dict, List, Optional, Set

try:
    from kiwipiepy import Kiwi
except Exception:  # pragma: no cover
    Kiwi = None

LEGAL_TERMS: Set[str] = {
    '처분청','과세관청','경정청구','심판청구','조세심판원','대법원','국세기본법',
    '소득세법','법인세법','부가가치세법','조세특례제한법','상속세','증여세',
    '과세표준','부과제척기간','양도소득세','세액','납세의무','부칙','적용례','경과조치',
    '청구인','처분','쟁점','판단','검토내용','관련법령','선결정례','판례'
}

_IGNORE_RE = [
    re.compile(p) for p in [
        r'^\d+$', r'^\d{4}\.\d{1,2}\.\d{1,2}\.?$', r'^제?\d+[조항호목]$',
        r'^[A-Za-z0-9]+$', r'^[A-Za-z0-9.\-_]+$', r'^[가-힣]\.$', r'^\([가-힣]\)$'
    ]
]


def _is_korean(text: str) -> bool:
    return any('\uAC00' <= c <= '\uD7A3' for c in text)


def _has_jamo(text: str) -> bool:
    return any('\u3131' <= c <= '\u3163' for c in text)


def _context(text: str, start: int, length: int, window: int = 20) -> str:
    s = max(0, start - window)
    e = min(len(text), start + length + window)
    ctx = text[s:e]
    if s > 0:
        ctx = '...' + ctx
    if e < len(text):
        ctx = ctx + '...'
    return ctx


class KoreanSpellChecker:
    def __init__(self, extra_words: Optional[Set[str]] = None):
        self.available = Kiwi is not None
        self.kiwi = Kiwi() if self.available else None
        self.user_dict: Set[str] = set(LEGAL_TERMS)
        if extra_words:
            self.user_dict |= extra_words
        if self.available:
            for word in self.user_dict:
                try:
                    self.kiwi.add_user_word(word, 'NNP', 0)
                except Exception:
                    pass

    def _skip(self, word: str) -> bool:
        if len(word) <= 1:
            return True
        if word in self.user_dict:
            return True
        if _has_jamo(word):
            return False
        for pattern in _IGNORE_RE:
            if pattern.match(word):
                return True
        return False

    def check_text(self, text: str) -> Dict:
        if not text or not text.strip():
            return {"available": self.available, "results": [], "summary": {"count": 0}}
        if not self.available:
            return {
                "available": False,
                "results": [],
                "summary": {"count": 0},
                "message": "kiwipiepy가 설치되지 않아 맞춤법 검사를 수행하지 못했습니다.",
            }

        results: List[Dict] = []
        seen = set()

        # 1) 단독 자모 삽입
        for m in re.finditer(r'([가-힣])([\u3131-\u3163]+)([가-힣])', text):
            value = m.group()
            key = (value, m.start())
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "word": value,
                "reason": "한글 사이 단독 자음/모음 삽입 의심",
                "context": _context(text, m.start(), len(value)),
                "suggestions": [],
                "start": m.start(),
            })

        # 2) 반복 글자
        for m in re.finditer(r'([가-힣])\1{2,}', text):
            value = m.group()
            key = (value, m.start())
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "word": value,
                "reason": "동일 글자 과다 반복 의심",
                "context": _context(text, m.start(), len(value)),
                "suggestions": [m.group(1)],
                "start": m.start(),
            })

        # 3) Kiwi OOV 기반
        try:
            analyzed = self.kiwi.analyze(text, typos='basic')
        except Exception as exc:
            return {
                "available": True,
                "results": results,
                "summary": {"count": len(results)},
                "message": f"형태소 분석 중 오류가 발생했습니다: {exc}",
            }

        if analyzed:
            for tok in analyzed[0][0]:
                word = tok.form
                if self._skip(word):
                    continue
                is_oov = getattr(tok, 'oov', False)
                if is_oov and _is_korean(word):
                    key = (word, getattr(tok, 'start', -1))
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({
                        "word": word,
                        "reason": "미등록 단어 또는 오탈자 의심",
                        "context": _context(text, getattr(tok, 'start', 0), getattr(tok, 'len', len(word))),
                        "suggestions": [],
                        "start": getattr(tok, 'start', 0),
                    })
                if _has_jamo(word):
                    key = (word, getattr(tok, 'start', -1))
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({
                        "word": word,
                        "reason": "단독 자음/모음 포함 토큰 의심",
                        "context": _context(text, getattr(tok, 'start', 0), getattr(tok, 'len', len(word))),
                        "suggestions": [],
                        "start": getattr(tok, 'start', 0),
                    })

        results = sorted(results, key=lambda x: x.get('start', 0))
        return {
            "available": True,
            "results": results,
            "summary": {
                "count": len(results),
                "top_words": [item['word'] for item in results[:10]],
            },
        }
