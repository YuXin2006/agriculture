def run_ai_analysis(payload: dict) -> dict:
    """基于规则生成 AI 分析建议（无需外部 API Key）。"""
    soil = _num(payload, "soil_moisture")
    temp = _num(payload, "temperature")
    co2 = _num(payload, "co2")
    light = _num(payload, "light")
    humidity = _num(payload, "humidity")

    risks = []
    suggestions = []

    if soil is not None:
        if soil < 45:
            risks.append("土壤湿度偏低，作物可能出现萎蔫")
            suggestions.append("建议立即启动滴灌，目标湿度 55%-65%")
        elif soil > 75:
            risks.append("土壤湿度过高，根系透气不足")
            suggestions.append("建议减少灌溉频次，并检查排水沟是否通畅")
        else:
            suggestions.append("土壤湿度处于适宜区间，可维持当前灌溉策略")

    if temp is not None:
        if temp > 30:
            risks.append("温度偏高，蒸腾作用增强")
            suggestions.append("建议在午间开启遮阳网或雾化降温")
        elif temp < 15:
            risks.append("温度偏低，生长速度可能放缓")
            suggestions.append("建议检查保温措施，夜间可适当加温")

    if co2 is not None:
        if co2 < 380:
            suggestions.append("CO₂ 浓度偏低，白天可适当通风后补施气肥")
        elif co2 > 1000:
            risks.append("CO₂ 浓度偏高，可能影响人员作业")
            suggestions.append("建议加强通风换气")

    if light is not None:
        if light < 5000:
            suggestions.append("光照不足，可考虑补光或调整种植密度")
        elif light > 15000:
            suggestions.append("光照较强，注意叶片灼伤并适时遮阳")

    if humidity is not None:
        if humidity > 80:
            risks.append("空气湿度偏高，病害风险上升")
            suggestions.append("建议加强通风除湿，并巡检叶面病害")

    if not risks:
        summary = "当前环境整体稳定，未发现明显异常风险。"
        level = "normal"
    elif len(risks) == 1:
        summary = "检测到 1 项潜在风险，建议优先处理。"
        level = "attention"
    else:
        summary = f"检测到 {len(risks)} 项潜在风险，建议尽快采取综合措施。"
        level = "warning"

    if not suggestions:
        suggestions.append("继续保持现有监测频率（建议 5 分钟/次）")

    return {
        "summary": summary,
        "level": level,
        "risks": risks,
        "suggestions": suggestions,
        "input": payload,
    }


def _num(payload, key):
    value = payload.get(key)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
