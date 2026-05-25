def run_ai_analysis(payload: dict) -> dict:
    """[已注释重构] 返回默认的AI分析结果"""
    return {
        "summary": "AI分析功能已暂时关闭",
        "level": "normal",
        "risks": [],
        "suggestions": ["AI分析功能正在重构中，敬请期待"],
        "input": payload,
    }


# def _num(payload, key):
#     value = payload.get(key)
#     if value is None or value == "":
#         return None
#     try:
#         return float(value)
#     except (TypeError, ValueError):
#         return None