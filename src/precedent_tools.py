from typing import Dict, Optional

from .tools import get_credentials, make_request_with_retry, parse_xml_response


precedent_cache = {}
precedent_detail_cache = {}
admin_case_cache = {}


def search_precedents(query: str, page: int = 1, page_size: int = 10, arguments: Optional[dict] = None) -> Dict:
    cache_key = (query, page, page_size)
    if cache_key in precedent_cache:
        return precedent_cache[cache_key]

    credentials = get_credentials(arguments)
    api_key = credentials["LAW_API_KEY"]
    base_url = credentials["LAW_API_URL"]
    if not api_key:
        result = {"error": "API 키가 설정되지 않았습니다. LAW_API_KEY 환경 변수를 설정해주세요."}
        precedent_cache[cache_key] = result
        return result

    url = f"{base_url}/precSearch.do"
    params = {
        "OC": api_key,
        "target": "prec",
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
            precedent_cache[cache_key] = result
            return result
        items = []
        for prec in root.findall('.//prec'):
            items.append({
                "판례일련번호": prec.findtext("판례일련번호", ""),
                "사건명": prec.findtext("사건명", ""),
                "사건번호": prec.findtext("사건번호", ""),
                "선고일자": prec.findtext("선고일자", ""),
                "법원명": prec.findtext("법원명", ""),
                "판결유형": prec.findtext("판결유형", ""),
                "판시사항": prec.findtext("판시사항", ""),
                "판결요지": prec.findtext("판결요지", ""),
            })
        result = {"total": int(root.findtext('.//totalCnt', '0')), "page": page, "page_size": page_size, "precedents": items}
        precedent_cache[cache_key] = result
        return result
    except Exception as e:
        result = {"error": f"판례 검색 중 오류 발생: {str(e)}"}
        precedent_cache[cache_key] = result
        return result


def get_precedent_detail(precedent_id: str, arguments: Optional[dict] = None) -> Dict:
    cache_key = (precedent_id,)
    if cache_key in precedent_detail_cache:
        return precedent_detail_cache[cache_key]

    credentials = get_credentials(arguments)
    api_key = credentials["LAW_API_KEY"]
    base_url = credentials["LAW_API_URL"]
    if not api_key:
        result = {"error": "API 키가 설정되지 않았습니다."}
        precedent_detail_cache[cache_key] = result
        return result

    url = f"{base_url}/precService.do"
    params = {"OC": api_key, "target": "prec", "type": "XML", "ID": precedent_id}
    try:
        response = make_request_with_retry(url, params)
        root = parse_xml_response(response.text)
        if root is None:
            result = {"error": "응답 파싱 실패"}
            precedent_detail_cache[cache_key] = result
            return result
        detail = {
            "판례일련번호": root.findtext('.//판례일련번호', ''),
            "사건명": root.findtext('.//사건명', ''),
            "사건번호": root.findtext('.//사건번호', ''),
            "선고일자": root.findtext('.//선고일자', ''),
            "법원명": root.findtext('.//법원명', ''),
            "판시사항": root.findtext('.//판시사항', ''),
            "판결요지": root.findtext('.//판결요지', ''),
            "참조조문": root.findtext('.//참조조문', ''),
            "참조판례": root.findtext('.//참조판례', ''),
            "전문": root.findtext('.//전문', ''),
        }
        precedent_detail_cache[cache_key] = detail
        return detail
    except Exception as e:
        result = {"error": f"판례 상세 조회 중 오류 발생: {str(e)}"}
        precedent_detail_cache[cache_key] = result
        return result


def search_tax_tribunal_cases(query: str, page: int = 1, page_size: int = 10, arguments: Optional[dict] = None) -> Dict:
    cache_key = (query, page, page_size)
    if cache_key in admin_case_cache:
        return admin_case_cache[cache_key]

    credentials = get_credentials(arguments)
    api_key = credentials["LAW_API_KEY"]
    base_url = credentials["LAW_API_URL"]
    if not api_key:
        result = {"error": "API 키가 설정되지 않았습니다. LAW_API_KEY 환경 변수를 설정해주세요."}
        admin_case_cache[cache_key] = result
        return result

    # 국가법령정보센터 행정심판/재결례 검색 target 시도
    url = f"{base_url}/admRulSearch.do"
    params = {
        "OC": api_key,
        "target": "admrul",
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
            admin_case_cache[cache_key] = result
            return result
        items = []
        for item in root.findall('.//admrul'):
            items.append({
                "일련번호": item.findtext("일련번호", ""),
                "사건명": item.findtext("사건명", ""),
                "사건번호": item.findtext("사건번호", ""),
                "재결일자": item.findtext("재결일자", ""),
                "재결기관": item.findtext("재결기관", ""),
                "재결요지": item.findtext("재결요지", ""),
            })
        result = {"total": int(root.findtext('.//totalCnt', '0')), "page": page, "page_size": page_size, "decisions": items}
        admin_case_cache[cache_key] = result
        return result
    except Exception as e:
        result = {"error": f"조세심판원 선결정례 검색 중 오류 발생: {str(e)}", "decisions": []}
        admin_case_cache[cache_key] = result
        return result
