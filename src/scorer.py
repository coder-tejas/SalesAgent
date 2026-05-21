import json


def score_lead(
    industry: str,
    employee_count: int,
    funding_stage: str,
    location: str,
    tech_stack: list,
    recent_signals: list,
    target_industries: list,
    min_employees: int,
    max_employees: int,
    funding_stages: list,
    target_locations: list,
    target_tech: list,
) -> dict:
    """
    Rule-based scoring fallback when LLM call fails.
    Returns the same JSON structure as the LLM prompt.
    """
    scores = {}

    industry_fit = 0
    if industry:
        for target in target_industries:
            if target.lower() in industry.lower():
                industry_fit = 10
                break
        if industry_fit == 0 and any(t.lower() in industry.lower() for t in ["software", "technology", "platform"]):
            industry_fit = 6
    scores["industry_fit"] = {"score": industry_fit, "reason": f"Industry: {industry}" if industry else "Unknown industry"}

    size_fit = 0
    if employee_count > 0:
        if min_employees <= employee_count <= max_employees:
            size_fit = 10
        elif employee_count < min_employees:
            size_fit = max(1, 10 - (min_employees - employee_count) // 10)
        else:
            size_fit = max(1, 10 - (employee_count - max_employees) // 100)
    scores["size_fit"] = {"score": size_fit, "reason": f"Employees: {employee_count}"}

    funding_fit = 0
    if funding_stage:
        for stage in funding_stages:
            if stage.lower() in funding_stage.lower():
                funding_fit = 10
                break
        if funding_fit == 0 and funding_stage.lower() in ["seed", "series a"]:
            funding_fit = 5
        elif funding_stage.lower() in ["series d+", "public"]:
            funding_fit = 4
    scores["funding_fit"] = {"score": funding_fit, "reason": f"Funding: {funding_stage}" if funding_stage else "Unknown funding"}

    signal_strength = 0
    if recent_signals:
        signal_strength = min(10, len(recent_signals) * 3)
    scores["signal_strength"] = {"score": signal_strength, "reason": f"Signals: {len(recent_signals)} found"}

    tech_fit = 0
    if tech_stack:
        matches = sum(1 for t in target_tech if any(t.lower() in tech.lower() for tech in tech_stack))
        tech_fit = min(10, matches * 5)
    scores["tech_fit"] = {"score": tech_fit, "reason": f"Tech stack: {', '.join(tech_stack) if tech_stack else 'Unknown'}"}

    total_score = sum(s["score"] for s in scores.values())

    if total_score >= 70:
        grade = "A"
        qualified = True
    elif total_score >= 45:
        grade = "B"
        qualified = True
    else:
        grade = "C"
        qualified = False

    disqualification_reason = ""
    if not qualified:
        reasons = []
        if scores["industry_fit"]["score"] < 5:
            reasons.append("Industry mismatch")
        if scores["size_fit"]["score"] < 5:
            reasons.append("Company size outside target range")
        if scores["funding_fit"]["score"] < 5:
            reasons.append("Funding stage not aligned")
        if scores["tech_fit"]["score"] < 5:
            reasons.append("No relevant tech stack detected")
        disqualification_reason = "; ".join(reasons) if reasons else "Below threshold score"

    pain_points = []
    if signal_strength < 5:
        pain_points.append("Limited recent business activity or market signals")
    if tech_fit < 5:
        pain_points.append("May lack modern tech infrastructure or tooling")
    if not pain_points:
        pain_points.append("Needs further discovery to identify pain points")

    outreach_angle = "Value-driven outreach focusing on operational efficiency and growth acceleration"
    if industry_fit >= 8 and signal_strength >= 5:
        outreach_angle = "Growth-focused outreach highlighting industry-specific success stories"
    elif tech_fit <= 3:
        outreach_angle = "Technology modernization outreach emphasizing infrastructure optimization"

    return {
        "scores": scores,
        "total_score": total_score,
        "grade": grade,
        "qualified": qualified,
        "disqualification_reason": disqualification_reason,
        "pain_points": pain_points,
        "outreach_angle": outreach_angle,
    }
