import os
import logging
import time
import xml.etree.ElementTree as ET
from typing import Dict, Optional

import certifi
import requests
from cachetools import TTLCache

DEFAULT_LAW_API_URL = "https://www.law.go.kr/DRF"

logger = logging.getLogger("gpt-korean-law-check")
level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
logger.setLevel(level)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.propagate = True

law_cache = TTLCache(maxsize=100, ttl=86400)
detail_cache = TTLCache(maxsize=100, ttl=86400)
failure_cache = TTLCache(maxsize=200, ttl=300)


def _resolve_verify():
    if os.environ.get("LAW_SSL_VERIFY", "").lower() in ("false", "0", "no"):
        return False
    bundle = os.environ.get("LAW_CA_BUNDLE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if bundle and os.path.exists(bundle):
        return bundle
    return certifi.where()


VERIFY = _resolve_verify()


def get_credentials(arguments: Optional[dict] = None) -> dict:
    api_key = ""
    api_url = DEFAULT_LAW_API_URL
    if isinstance(arguments, dict) and "env" in arguments and isinstance(arguments["env"], dict):
        env = arguments["env"]
        api_key = env.get("LAW_API_KEY", "")
        api_url = env.get("LAW_API_URL", api_url)
    if not api_key:
        api_key = os.environ.get("LAW_API_KEY", "")
    api_url = os.environ.get("LAW_API_URL", api_url)
    return {"LAW_API_KEY": api_key, "LAW_API_URL": api_url}


def make_request_with_retry(url: str, params: dict, max_retries: int = 3, timeout: int = 30) -> requests.Response:
    last_exception = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout, verify=VERIFY)
            response.raise_for_status()
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(attempt + 1)
            else:
                raise
        except requests.exceptions.RequestException:
            raise
    if last_exception:
        raise last_exception
    raise requests.exceptions.RequestException("모든 재시도가 실패했습니다.")


def parse_xml_response(xml_text: str):
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError:
        return None


def search_law(query: str, page: int = 1, page_size: int = 10, arguments: Optional[dict] = None) -> Dict:
    cache_key = (query, page, page_size)
    if cache_key in law_cache:
        return law_cache[cache_key]
    if cache_key in failure_cache:
        return failure_cache[cache_key]

    credentials = get_credentials(arguments)
    api_key = credentials["LAW_API_KEY"]
    base_url = credentials["LAW_API_URL"]
    if not api_key:
        result = {"error": "API 키가 설정되지 않았습니다. LAW_API_KEY 환경 변수를 설정해주세요."}
        failure_cache[cache_key] = result
        return result

    url = f"{base_url}/lawSearch.do"
    params = {
        "OC": api_key,
        "target": "law",
        "type": "XML",
        "query": query,
        "display": min(page_size, 50),
        "page": page,
    }
    try:
        response = make_request_with_retry(url, params)
        root = parse_xml_response(response.text)
        if root is None:
            result = {"error": "응답 파싱 실패"}
            failure_cache[cache_key] = result
            return result
        laws = []
        for law in root.findall(".//law"):
            laws.append({
                "법령ID": law.findtext("법령ID", ""),
                "법령명": law.findtext("법령명한글", ""),
                "법령명_약칭": law.findtext("법령약칭명", ""),
                "법령구분": law.findtext("법령구분명", ""),
                "소관부처": law.findtext("소관부처명", ""),
                "공포일자": law.findtext("공포일자", ""),
                "시행일자": law.findtext("시행일자", ""),
                "제개정구분": law.findtext("제개정구분명", ""),
            })
        result = {
            "total": int(root.findtext(".//totalCnt", "0")),
            "page": page,
            "page_size": page_size,
            "laws": laws,
        }
        law_cache[cache_key] = result
        return result
    except Exception as e:
        result = {"error": f"법령 검색 중 오류 발생: {str(e)}"}
        failure_cache[cache_key] = result
        return result


def get_law_detail(law_id: str, arguments: Optional[dict] = None) -> Dict:
    cache_key = (law_id,)
    if cache_key in detail_cache:
        return detail_cache[cache_key]
    if cache_key in failure_cache:
        return failure_cache[cache_key]

    credentials = get_credentials(arguments)
    api_key = credentials["LAW_API_KEY"]
    base_url = credentials["LAW_API_URL"]
    if not api_key:
        result = {"error": "API 키가 설정되지 않았습니다."}
        failure_cache[cache_key] = result
        return result

    url = f"{base_url}/lawService.do"
    params = {
        "OC": api_key,
        "target": "law",
        "type": "XML",
        "MST": law_id,
    }
    try:
        response = make_request_with_retry(url, params)
        root = parse_xml_response(response.text)
        if root is None:
            result = {"error": "응답 파싱 실패"}
            failure_cache[cache_key] = result
            return result
        law_info = {
            "법령ID": root.findtext(".//법령ID", ""),
            "법령명": root.findtext(".//법령명한글", ""),
            "법령구분": root.findtext(".//법령구분명", ""),
            "소관부처": root.findtext(".//소관부처명", ""),
            "공포일자": root.findtext(".//공포일자", ""),
            "시행일자": root.findtext(".//시행일자", ""),
        }
        articles = []
        for article in root.findall(".//조문"):
            articles.append({
                "조문번호": article.findtext("조문번호", ""),
                "조문제목": article.findtext("조문제목", ""),
                "조문내용": article.findtext("조문내용", ""),
            })
        law_info["조문"] = articles
        law_info["조문수"] = len(articles)
        detail_cache[cache_key] = law_info
        return law_info
    except Exception as e:
        result = {"error": f"법령 상세 조회 중 오류 발생: {str(e)}"}
        failure_cache[cache_key] = result
        return result
