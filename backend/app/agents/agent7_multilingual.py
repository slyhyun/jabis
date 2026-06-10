"""
Agent 7: 다국어 변환
- 수정된 한국어 카피 → 영어, 중국어 번역 (LLM)
- 번역본 의무표시 보존 검증 (※ 문구 포함 여부)
- 문화권별 부적절 표현 체크 (LLM)
"""
import os
from openai import OpenAI

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    return _client


# ============================================================
# 번역 프롬프트
# ============================================================

_LANG_CONFIG = {
    "en": {
        "name": "English",
        "region": "영미권",
        "caution": (
            "- Use formal financial English (e.g. 'annual interest rate', 'principal protection')\n"
            "- Keep all mandatory disclosure markers (※) and their content\n"
            "- Avoid overly aggressive marketing language common in Korean ads"
        ),
    },
    "zh": {
        "name": "简体中文",
        "region": "중국어권",
        "caution": (
            "- 使用正式金融用语（如「年利率」、「本金保障」）\n"
            "- 保留所有必要披露标记（※）及其内容\n"
            "- 避免在中国金融广告中被视为夸大或不当的表达"
        ),
    },
}

# 문화권별 부적절 표현 패턴 (LLM 체크 보조용)
_CULTURAL_CAUTIONS = {
    "en": [
        "guaranteed returns",
        "risk-free",
        "100% safe",
        "no loss",
    ],
    "zh": [
        "保本",
        "零风险",
        "绝对安全",
        "稳赚",
    ],
}


def _build_translation_prompt(korean_copy: str, lang: str) -> str:
    cfg = _LANG_CONFIG[lang]
    cautions = "\n".join(f"  - {c}" for c in _CULTURAL_CAUTIONS[lang])

    return f"""당신은 금융 광고 전문 번역가입니다.
아래 한국어 금융 광고 카피를 {cfg['name']}로 번역하세요.

[원본 한국어 카피]
{korean_copy}

[번역 지침]
{cfg['caution']}
- 마케팅 톤과 의도를 유지하되 {cfg['region']} 소비자에게 자연스럽게 표현
- 아래 표현이 번역본에 포함되지 않도록 주의:
{cautions}

번역본만 출력하세요. 설명이나 주석 없이."""


def _build_culture_check_prompt(translated: str, lang: str) -> str:
    cfg = _LANG_CONFIG[lang]
    cautions = "\n".join(f"  - {c}" for c in _CULTURAL_CAUTIONS[lang])

    return f"""당신은 {cfg['region']} 금융 광고 규제 전문가입니다.
아래 {cfg['name']} 번역본에서 문화권별 부적절 표현을 검토하세요.

[번역본]
{translated}

[체크 항목]
- 해당 문화권에서 금융 광고에 부적절한 표현 포함 여부
- 아래 금지 표현 포함 여부:
{cautions}
- 의무표시(※) 문구가 번역본에 보존되었는지

[출력 형식 - JSON]
{{
  "has_issues": true/false,
  "issues": ["발견된 문제점 목록 (없으면 빈 배열)"],
  "disclosure_preserved": true/false
}}"""


# ============================================================
# LLM 호출
# ============================================================

def _translate(korean_copy: str, lang: str) -> str:
    prompt = _build_translation_prompt(korean_copy, lang)
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Agent 7] 번역 오류 ({lang}): {e}")
        return ""


def _culture_check(translated: str, lang: str) -> dict:
    if not translated:
        return {"has_issues": True, "issues": ["번역 실패"], "disclosure_preserved": False}

    prompt = _build_culture_check_prompt(translated, lang)
    try:
        import json
        client = _get_client()
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[Agent 7] 문화권 체크 오류 ({lang}): {e}")
        # fallback: ※ 포함 여부만 체크
        return {
            "has_issues": False,
            "issues": [],
            "disclosure_preserved": "※" in translated,
        }


# ============================================================
# Agent 7 메인 함수
# ============================================================

def run_agent7(revised_copy: str, product_type: str) -> dict:
    """
    Agent 7: 다국어 변환
    - revised_copy: Agent 5/6에서 확정된 수정 카피
    - product_type: 상품 유형
    """
    print(f"[Agent 7] 다국어 변환 시작")

    results = {}
    for lang in ["en", "zh"]:
        lang_name = _LANG_CONFIG[lang]["name"]
        print(f"[Agent 7] {lang_name} 번역 중...")

        translated = _translate(revised_copy, lang)
        check = _culture_check(translated, lang)

        results[lang] = {
            "text": translated,
            "has_issues": check.get("has_issues", False),
            "issues": check.get("issues", []),
            "disclosure_preserved": check.get("disclosure_preserved", False),
        }

        status = "이슈 있음" if check.get("has_issues") else "통과"
        print(f"[Agent 7] {lang_name} 완료 — 문화권 체크: {status}")

    print(f"[Agent 7] 완료")
    return {"multilingual": results}


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    test_copy = (
        "JB 주거래 우대 정기예금 우대조건 충족 시 최고 연 5.0% (세전).\n"
        "※ 가입대상: 만 17세 이상 개인 (비대면 전용)\n"
        "※ 이 예금은 예금자보호법에 따라 1인당 최고 5천만원까지 보호됩니다.\n"
        "※ 중도해지 시 약정금리보다 낮은 금리가 적용될 수 있습니다."
    )

    result = run_agent7(test_copy, "예금")

    for lang, data in result["multilingual"].items():
        lang_name = _LANG_CONFIG[lang]["name"]
        print(f"\n{'='*55}")
        print(f"[{lang_name}]")
        print(data["text"] if data["text"] else "(번역 실패 - API 키 필요)")
        print(f"문화권 이슈: {data['has_issues']} | 의무표시 보존: {data['disclosure_preserved']}")
        if data["issues"]:
            for issue in data["issues"]:
                print(f"  - {issue}")
