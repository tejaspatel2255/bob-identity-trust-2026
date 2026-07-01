"""
Generates a one-page audit PDF for a Setu risk event.
Uses reportlab — pure Python, zero system dependencies.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

def generate_case_pdf(event: dict) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    NAVY  = HexColor("#0A0E1A")
    CYAN  = HexColor("#00D4FF")
    RED   = HexColor("#FF3B5C")
    AMBER = HexColor("#FFB800")
    GREEN = HexColor("#00E5A0")
    GRAY  = HexColor("#6B84A8")
    DARK  = HexColor("#1A1A1A")

    # Header band
    c.setFillColor(NAVY)
    c.rect(0, height - 30*mm, width, 30*mm, fill=True, stroke=False)
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20*mm, height - 13*mm, "SETU — IDENTITY TRUST AUDIT REPORT")
    c.setFillColor(HexColor("#E8F0FE"))
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, height - 21*mm,
                 f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}   |   Case ID: {event.get('id','N/A')}")

    y = height - 42*mm

    def section_title(text, y_pos):
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20*mm, y_pos, text)
        c.setStrokeColor(CYAN)
        c.setLineWidth(0.8)
        c.line(20*mm, y_pos - 2*mm, width - 20*mm, y_pos - 2*mm)
        return y_pos - 10*mm

    def kv(label, value, y_pos):
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 9)
        c.drawString(22*mm, y_pos, label)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(72*mm, y_pos, str(value))
        return y_pos - 7*mm

    # Case Identification
    y = section_title("CASE IDENTIFICATION", y)
    y = kv("Entity ID:", event.get("entity_id", "N/A"), y)
    y = kv("Entity Type:", event.get("entity_type", "N/A"), y)
    y = kv("Customer ID:", event.get("customer_id", "N/A"), y)
    y = kv("Timestamp:", event.get("timestamp", "N/A"), y)
    y -= 4*mm

    # Risk Assessment
    y = section_title("RISK ASSESSMENT", y)
    score = event.get("risk_score", 0)
    action = event.get("action", {})
    if isinstance(action, dict):
        action_name = action.get("action", "N/A")
        level = action.get("level", "N/A")
        route_to = action.get("route_to") or "None"
    else:
        action_name = str(action)
        level = event.get("action_level", "N/A")
        route_to = event.get("route_to") or "None"

    score_color = GREEN if score < 31 else AMBER if score < 66 else RED
    c.setFillColor(GRAY); c.setFont("Helvetica", 9)
    c.drawString(22*mm, y, "Risk Score:")
    c.setFillColor(score_color); c.setFont("Helvetica-Bold", 15)
    c.drawString(72*mm, y, f"{score:.1f} / 100  ({level})")
    y -= 9*mm
    y = kv("Action Taken:", action_name, y)
    y = kv("Route To:", route_to, y)
    conf = event.get("confidence", {})
    if conf:
        y = kv("Model Confidence:",
                f"{conf.get('confidence_label','N/A')} ({conf.get('confidence_pct','N/A')}%)", y)
        y = kv("Confidence Note:", conf.get("reasoning",""), y)
    y -= 4*mm

    # SHAP Attributions
    y = section_title("CONTRIBUTING FACTORS (SHAP ATTRIBUTION)", y)
    for attr in event.get("shap_attributions", [])[:6]:
        feat = attr.get("feature","").replace("_"," ").title()
        contrib = attr.get("contribution", 0)
        bar_w = min(abs(contrib) * 70*mm, 70*mm)
        c.setFillColor(DARK); c.setFont("Helvetica", 9)
        c.drawString(22*mm, y, feat)
        c.setFillColor(RED if contrib > 0 else GREEN)
        c.rect(72*mm, y - 1*mm, bar_w, 3*mm, fill=True, stroke=False)
        c.setFillColor(GRAY); c.setFont("Helvetica", 8)
        c.drawString(72*mm + bar_w + 2*mm, y, f"{contrib:+.3f}")
        y -= 7*mm
    y -= 3*mm

    # AI Explanation
    y = section_title("AI-GENERATED EXPLANATION", y)
    explanation = event.get("explanation", "No explanation available.")
    c.setFillColor(HexColor("#0F1629"))
    c.rect(20*mm, y - 18*mm, width - 40*mm, 20*mm, fill=True, stroke=False)
    c.setStrokeColor(CYAN); c.setLineWidth(0.5)
    c.rect(20*mm, y - 18*mm, width - 40*mm, 20*mm, fill=False, stroke=True)
    c.setFillColor(HexColor("#E8F0FE")); c.setFont("Helvetica-Oblique", 9)
    words = explanation.split()
    line = ""; text_y = y - 6*mm
    for word in words:
        test = f"{line} {word}".strip()
        if c.stringWidth(test, "Helvetica-Oblique", 9) > (width - 50*mm):
            c.drawString(25*mm, text_y, line)
            text_y -= 5*mm; line = word
        else:
            line = test
    if line:
        c.drawString(25*mm, text_y, line)
    y -= 22*mm

    # Audit Footer
    y -= 5*mm
    c.setFillColor(GRAY); c.setFont("Helvetica", 8)
    c.drawString(22*mm, y,
        f"LLM Provider: {event.get('provider_used','N/A')}   |   "
        f"Model: {event.get('model_id','N/A')}   |   "
        f"Fallback Used: {event.get('fallback_used', False)}")
    y -= 5*mm
    c.drawString(22*mm, y,
        "Auto-generated by Setu Identity Trust Graph for compliance audit. "
        "Not a substitute for human investigation.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
