"""
Generate Islam_Saiful_quadchart.pdf directly using ReportLab.
Run with: conda run -n csc7644 --no-capture-output python generate_quadchart_pdf.py
"""

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas


def draw_quad_chart():
    """Draw a professional quad chart on a single landscape PDF page."""
    output_path = "/home/saiful/Applied_LLM_Development/Midterm project/AINEWSAgentic/Islam_Saiful_quadchart.pdf"
    page_w, page_h = landscape(letter)  # 11 x 8.5 inches

    c = canvas.Canvas(output_path, pagesize=landscape(letter))

    # Margins
    margin = 0.5 * inch
    content_w = page_w - 2 * margin
    content_h = page_h - 2 * margin

    # Layout coordinates
    left = margin
    right = page_w - margin
    mid_x = page_w / 2
    top = page_h - margin
    bottom = margin

    # Title area
    title_h = 0.55 * inch
    title_top = top
    title_bottom = top - title_h

    # BLUF area
    bluf_h = 0.50 * inch
    bluf_top = title_bottom
    bluf_bottom = bluf_top - bluf_h

    # Quadrant area
    quad_top = bluf_bottom
    quad_mid_y = (quad_top + bottom) / 2

    # Colors
    title_bg = HexColor("#1B3A5C")  # dark navy
    bluf_bg = HexColor("#E8EEF4")   # light blue-gray
    line_color = HexColor("#1B3A5C")
    heading_color = HexColor("#1B3A5C")

    # ===== TITLE BAR =====
    c.setFillColor(title_bg)
    c.rect(left, title_bottom, content_w, title_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(
        mid_x, title_bottom + 0.17 * inch,
        "AI News Agentic System: Automated News Curation & Summarization"
    )

    # ===== BLUF BAR =====
    c.setFillColor(bluf_bg)
    c.rect(left, bluf_bottom, content_w, bluf_h, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 8.5)
    bluf_text = (
        "BLUF: We build an agentic AI system using LangGraph that autonomously fetches, "
        "summarizes, and delivers curated AI news via a multi-node pipeline with Tavily "
        "search integration, Groq-hosted LLMs (Llama 3, Gemma 2), and a Streamlit web interface."
    )
    # Wrap BLUF text
    text_obj = c.beginText(left + 0.15 * inch, bluf_top - 0.18 * inch)
    text_obj.setFont("Helvetica-Bold", 8.5)
    text_obj.setLeading(12)
    # Simple word-wrap
    max_width = content_w - 0.3 * inch
    words = bluf_text.split()
    line = ""
    for word in words:
        test = line + " " + word if line else word
        if c.stringWidth(test, "Helvetica-Bold", 8.5) < max_width:
            line = test
        else:
            text_obj.textLine(line)
            line = word
    if line:
        text_obj.textLine(line)
    c.drawText(text_obj)

    # ===== DIVIDER LINES =====
    c.setStrokeColor(line_color)
    c.setLineWidth(1.5)
    # Vertical center line
    c.line(mid_x, quad_top, mid_x, bottom)
    # Horizontal center line
    c.line(left, quad_mid_y, right, quad_mid_y)
    # Border
    c.rect(left, bottom, content_w, quad_top - bottom, fill=0, stroke=1)

    # ===== QUADRANT HELPER =====
    def draw_quadrant(x, y_top, width, height, heading, bullet_texts):
        """Draw heading + bullet points inside a quadrant area."""
        # Heading
        c.setFillColor(heading_color)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 0.12 * inch, y_top - 0.22 * inch, heading)

        # Bullet points
        c.setFillColor(black)
        c.setFont("Helvetica", 7.8)
        text_x = x + 0.22 * inch
        text_max_w = width - 0.4 * inch
        y = y_top - 0.45 * inch
        line_leading = 10.5

        for bullet in bullet_texts:
            # Draw bullet character
            c.drawString(x + 0.12 * inch, y, "•")
            # Wrap text
            words = bullet.split()
            line = ""
            for word in words:
                test = line + " " + word if line else word
                if c.stringWidth(test, "Helvetica", 7.8) < text_max_w:
                    line = test
                else:
                    c.drawString(text_x, y, line)
                    y -= line_leading
                    line = word
            if line:
                c.drawString(text_x, y, line)
                y -= line_leading
            y -= 2  # extra spacing between bullets

    quad_w = (right - left) / 2
    quad_h_upper = quad_top - quad_mid_y
    quad_h_lower = quad_mid_y - bottom

    # ===== UPPER LEFT: Background & Motivation =====
    draw_quadrant(
        left, quad_top, quad_w, quad_h_upper,
        "Background & Motivation",
        [
            "AI news is scattered across hundreds of sources; professionals waste "
            "significant time manually scanning for relevant updates each day.",
            "Traditional RSS feeds and aggregators (Google News, Feedly) lack intelligent "
            "filtering and summarization — users still must read full articles.",
            "LLM-powered agentic systems can automate the complete pipeline: search, "
            "filter, summarize, and deliver — dramatically reducing information overload.",
            "This project is motivated by the need for a hands-free, reliable AI news "
            "briefing tool for researchers and technology practitioners.",
        ]
    )

    # ===== UPPER RIGHT: Data and Resources =====
    draw_quadrant(
        mid_x, quad_top, quad_w, quad_h_upper,
        "Data and Resources",
        [
            "Tavily Search API: Real-time web search with news-specific topic filtering "
            "and configurable time ranges (daily/weekly/monthly), up to 20 results per query.",
            "Groq Cloud API: Low-latency LLM inference using Llama 3 (8B, 70B) and "
            "Gemma 2 (9B) for fast, cost-effective summarization.",
            "All data is fetched live from public web sources via Tavily; no pre-collected "
            "datasets are required.",
            "Outputs stored as structured Markdown files (daily_summary.md, "
            "weekly_summary.md, monthly_summary.md) for easy consumption.",
        ]
    )

    # ===== LOWER LEFT: Possible Technical Approach =====
    draw_quadrant(
        left, quad_mid_y, quad_w, quad_h_lower,
        "Possible Technical Approach",
        [
            "Agentic Architecture: LangGraph StateGraph with three nodes — fetch_news, "
            "summarize_news, save_result — connected via directed edges.",
            "Tool Integration: Tavily search tool bound to chatbot nodes using LangGraph's "
            "ToolNode with conditional routing (tools_condition).",
            "Prompting: Structured ChatPromptTemplate enforcing Markdown output with dates, "
            "concise summaries, and source URLs.",
            "Three Use Cases: (1) Basic Chatbot, (2) Web-augmented Chatbot with search, "
            "(3) AI News pipeline with automated curation.",
            "User Interface: Streamlit web app with model selection, API key input, "
            "and time-frame filtering via sidebar controls.",
        ]
    )

    # ===== LOWER RIGHT: Impact & References =====
    draw_quadrant(
        mid_x, quad_mid_y, quad_w, quad_h_lower,
        "Impact & References",
        [
            "Demonstrates production-ready agentic patterns: tool orchestration, stateful "
            "graph execution, and multi-step LLM reasoning.",
            "Saves 30-60 min/day for AI practitioners needing curated news briefings.",
            "Extensible to other domains: finance, healthcare, legal news curation.",
            "References:",
            "  LangGraph Docs. (2024). LangChain. https://langchain-ai.github.io/langgraph/",
            "  Tavily AI Search API. (2024). https://tavily.com/",
            "  Groq Cloud. (2024). https://console.groq.com/",
        ]
    )

    c.save()
    print(f"[OK] Quad chart PDF saved: {output_path}")


if __name__ == "__main__":
    draw_quad_chart()
