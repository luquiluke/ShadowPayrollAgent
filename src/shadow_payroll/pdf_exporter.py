"""
PDF export functionality for shadow payroll reports.

Uses ReportLab Platypus for professional, multi-page PDF generation
with charts, tables, branding, and disclaimers.
"""

import logging
from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .config import config
from .scenarios import normalize_line_items, ScenarioData

logger = logging.getLogger(__name__)

# Color constants (light backgrounds for print-friendly PDFs)
BLUE = HexColor("#2d8cf0")
DARK_BG = HexColor("#2d3642")
LIGHT_ROW = HexColor("#f8f9fa")
WHITE = colors.white
GREEN_BG = HexColor("#d4edda")
RED_BG = HexColor("#f8d7da")
TEXT_DARK = HexColor("#1a1a2e")
LIGHT_BLUE_BG = HexColor("#e8f4fd")


def _ensure_dict_line_items(scenarios: list[dict]) -> list[dict]:
    """Ensure all scenario line_items are in {label: amount} dict format.

    normalize_line_items expects dict format, but scenarios may contain
    the raw list-of-CostLineItem-dicts format from model_dump().
    """
    prepared = []
    for s in scenarios:
        result = s.get("result", {})
        li = result.get("line_items", {})
        if isinstance(li, list):
            s = dict(s)
            s["result"] = dict(result)
            s["result"]["line_items"] = {
                item["label"]: item.get("amount_usd", 0.0)
                for item in li
                if isinstance(item, dict)
            }
        prepared.append(s)
    return prepared


class PDFExporter:
    """Generate professional PDF reports for shadow payroll cost analysis."""

    def __init__(self, company_name: str | None = None):
        self.company_name = company_name or config.PDF_COMPANY_NAME
        self._setup_styles()

    def _setup_styles(self) -> None:
        """Configure paragraph styles using ReportLab built-in fonts."""
        base = getSampleStyleSheet()
        self.styles = {
            "title": ParagraphStyle(
                "pdf_title",
                parent=base["Title"],
                fontName="Helvetica-Bold",
                fontSize=22,
                textColor=TEXT_DARK,
                spaceAfter=12,
                alignment=TA_CENTER,
            ),
            "heading": ParagraphStyle(
                "pdf_heading",
                parent=base["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=14,
                textColor=TEXT_DARK,
                spaceBefore=16,
                spaceAfter=8,
            ),
            "subheading": ParagraphStyle(
                "pdf_subheading",
                parent=base["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=TEXT_DARK,
                spaceBefore=10,
                spaceAfter=4,
            ),
            "body": ParagraphStyle(
                "pdf_body",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=10,
                textColor=TEXT_DARK,
                leading=14,
                spaceAfter=6,
            ),
            "mono": ParagraphStyle(
                "pdf_mono",
                parent=base["Normal"],
                fontName="Courier",
                fontSize=10,
                textColor=TEXT_DARK,
                alignment=TA_RIGHT,
            ),
            "disclaimer": ParagraphStyle(
                "pdf_disclaimer",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=9,
                textColor=HexColor("#555555"),
                leading=13,
                spaceAfter=4,
            ),
            "small": ParagraphStyle(
                "pdf_small",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=8,
                textColor=HexColor("#888888"),
                alignment=TA_CENTER,
            ),
            "center_body": ParagraphStyle(
                "pdf_center_body",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=10,
                textColor=TEXT_DARK,
                alignment=TA_CENTER,
                spaceAfter=6,
            ),
        }

    def generate(
        self, scenarios: list[dict], metadata: dict[str, Any] | None = None
    ) -> BytesIO:
        """Generate a complete PDF report.

        Args:
            scenarios: List of ScenarioData dicts (same format as session state).
            metadata: Optional dict with ``model_name`` and ``timestamp``.

        Returns:
            BytesIO buffer containing the PDF.
        """
        metadata = metadata or {}
        scenarios = _ensure_dict_line_items(scenarios)
        buf = BytesIO()

        # Build document with header/footer
        doc = BaseDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=1.0 * inch,
            bottomMargin=0.75 * inch,
        )

        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="main",
        )

        template = PageTemplate(
            id="all_pages",
            frames=[frame],
            onPage=self._header_footer,
        )
        doc.addPageTemplates([template])

        # Build story (flowables)
        story: list = []

        # 1. Executive summary
        story.extend(self._build_executive_summary(scenarios, metadata))

        # 2. Comparison section (2+ scenarios)
        if len(scenarios) >= 2:
            story.append(Spacer(1, 16))
            story.append(Paragraph("Scenario Comparison", self.styles["heading"]))
            story.append(Spacer(1, 8))
            chart = self._build_comparison_chart(scenarios)
            story.append(chart)
            story.append(Spacer(1, 12))
            table = self._build_comparison_table(scenarios)
            story.append(table)

        # 3. Per-scenario detail pages
        for scenario in scenarios:
            story.append(PageBreak())
            story.extend(self._build_scenario_detail(scenario))

        # 4. Disclaimer page
        story.append(PageBreak())
        story.extend(self._build_disclaimer_page())

        doc.build(story)
        buf.seek(0)
        logger.info("PDF report generated (%d bytes, %d scenarios)", len(buf.getvalue()), len(scenarios))
        return buf

    # --- Private builders ---

    def _build_executive_summary(
        self, scenarios: list[dict], metadata: dict[str, Any]
    ) -> list:
        """Build cover / executive summary flowables."""
        elements: list = []

        elements.append(Paragraph("Shadow Payroll Cost Analysis", self.styles["title"]))
        elements.append(Spacer(1, 4))

        # Date
        date_str = datetime.now().strftime(config.PDF_DATE_FORMAT)
        elements.append(Paragraph(date_str, self.styles["center_body"]))

        # Company name
        elements.append(
            Paragraph(self.company_name, self.styles["center_body"])
        )
        elements.append(Spacer(1, 16))

        # Summary paragraph
        if len(scenarios) == 1:
            s = scenarios[0]
            inp = s.get("input_data", {})
            country = inp.get("host_country", "the host country")
            duration = inp.get("duration_months", "N/A")
            elements.append(
                Paragraph(
                    f"Cost analysis for a {duration}-month assignment to {country}.",
                    self.styles["body"],
                )
            )
        elif len(scenarios) >= 2:
            names = [s.get("name", "Unknown") for s in scenarios]
            totals = [
                (s.get("name", "?"), s.get("result", {}).get("total_employer_cost_usd", 0))
                for s in scenarios
            ]
            cheapest = min(totals, key=lambda t: t[1])
            listing = ", ".join(names[:-1]) + f" and {names[-1]}"
            elements.append(
                Paragraph(
                    f"Comparative cost analysis across {len(scenarios)} scenarios: "
                    f"{listing}. {cheapest[0]} is the most cost-effective option "
                    f"at USD {cheapest[1]:,.0f} total employer cost.",
                    self.styles["body"],
                )
            )

        # Generation metadata
        model = metadata.get("model_name", "")
        ts = metadata.get("timestamp", "")
        if model or ts:
            meta_parts = []
            if model:
                meta_parts.append(f"Model: {model}")
            if ts:
                meta_parts.append(f"Generated: {ts}")
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(" | ".join(meta_parts), self.styles["small"]))

        return elements

    def _build_comparison_chart(self, scenarios: list[dict]) -> Drawing:
        """Build a VerticalBarChart comparing total employer cost across scenarios."""
        drawing = Drawing(450, 200)

        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 30
        chart.width = 370
        chart.height = 140

        # Data: one data series with one value per scenario
        values = [
            s.get("result", {}).get("total_employer_cost_usd", 0) for s in scenarios
        ]
        chart.data = [values]

        # Category names
        chart.categoryAxis.categoryNames = [
            s.get("name", f"Scenario {i+1}") for i, s in enumerate(scenarios)
        ]
        chart.categoryAxis.labels.fontName = "Helvetica"
        chart.categoryAxis.labels.fontSize = 8
        chart.categoryAxis.labels.angle = 0

        # Value axis
        chart.valueAxis.valueMin = 0
        chart.valueAxis.labelTextFormat = "$%s"
        chart.valueAxis.labels.fontName = "Courier"
        chart.valueAxis.labels.fontSize = 8

        # Bar styling
        chart.bars[0].fillColor = BLUE
        chart.bars[0].strokeColor = None

        # Add value labels above bars
        for i, val in enumerate(values):
            label = String(
                chart.x + (i + 0.5) * (chart.width / len(values)),
                chart.y + chart.height + 5,
                f"${val:,.0f}",
                fontSize=8,
                fontName="Courier",
                textAnchor="middle",
                fillColor=TEXT_DARK,
            )
            drawing.add(label)

        drawing.add(chart)
        return drawing

    def _build_comparison_table(self, scenarios: list[dict]) -> Table:
        """Build a color-coded comparison table with min/max highlighting."""
        labels, matrix = normalize_line_items(scenarios)

        # Header row
        header = ["Cost Category"] + [s.get("name", "?") for s in scenarios]
        data = [header]

        for label_idx, label in enumerate(labels):
            row = [label]
            for s_idx in range(len(scenarios)):
                val = matrix[s_idx][label_idx]
                row.append(f"${val:,.0f}")
            data.append(row)

        # Total row
        totals = [
            s.get("result", {}).get("total_employer_cost_usd", 0) for s in scenarios
        ]
        total_row = ["Total Employer Cost"] + [f"${t:,.0f}" for t in totals]
        data.append(total_row)

        # Build table
        col_widths = [150] + [100] * len(scenarios)
        table = Table(data, colWidths=col_widths)

        # Base style
        style_cmds: list = [
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            # Data cells
            ("FONTNAME", (1, 1), (-1, -1), "Courier"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            # Total row
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 1.5, TEXT_DARK),
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]

        # Alternating row backgrounds
        for row_idx in range(1, len(data) - 1):
            if row_idx % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), LIGHT_ROW))

        # Min/max highlighting for data rows (skip header and total)
        num_scenarios = len(scenarios)
        for label_idx in range(len(labels)):
            row_idx = label_idx + 1  # +1 for header
            row_values = [matrix[s_idx][label_idx] for s_idx in range(num_scenarios)]
            min_val = min(row_values)
            max_val = max(row_values)
            if min_val == max_val:
                continue
            for s_idx, val in enumerate(row_values):
                col_idx = s_idx + 1  # +1 for label column
                if val == min_val:
                    style_cmds.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), GREEN_BG))
                elif val == max_val:
                    style_cmds.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), RED_BG))

        # Min/max for total row
        total_row_idx = len(data) - 1
        min_total = min(totals)
        max_total = max(totals)
        if min_total != max_total:
            for s_idx, val in enumerate(totals):
                col_idx = s_idx + 1
                if val == min_total:
                    style_cmds.append(("BACKGROUND", (col_idx, total_row_idx), (col_idx, total_row_idx), GREEN_BG))
                elif val == max_total:
                    style_cmds.append(("BACKGROUND", (col_idx, total_row_idx), (col_idx, total_row_idx), RED_BG))

        table.setStyle(TableStyle(style_cmds))
        return table

    def _build_scenario_detail(self, scenario: dict) -> list:
        """Build per-scenario detail page flowables."""
        elements: list = []
        name = scenario.get("name", "Scenario")
        inp = scenario.get("input_data", {})
        result = scenario.get("result", {})

        elements.append(Paragraph(name, self.styles["heading"]))
        elements.append(Spacer(1, 8))

        # Input summary table
        elements.append(Paragraph("Assignment Details", self.styles["subheading"]))
        input_rows = [
            ["Parameter", "Value"],
            ["Annual Salary (USD)", f"${inp.get('salary_usd', 0):,.0f}"],
            ["Duration (months)", str(inp.get("duration_months", "N/A"))],
            ["Home Country", str(inp.get("home_country", "N/A"))],
            ["Host Country", str(inp.get("host_country", "N/A"))],
            ["Housing Benefit (USD)", f"${inp.get('housing_usd', 0):,.0f}"],
            ["Education Benefit (USD)", f"${inp.get('school_usd', 0):,.0f}"],
            ["Spouse", "Yes" if inp.get("has_spouse") else "No"],
            ["Children", str(inp.get("num_children", 0))],
        ]

        input_table = Table(input_rows, colWidths=[200, 200])
        input_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (1, 1), (1, -1), "Courier"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(input_table)
        elements.append(Spacer(1, 12))

        # Cost breakdown table
        line_items = result.get("line_items", {})
        local_currency = result.get("local_currency", "Local")

        elements.append(Paragraph("Cost Breakdown", self.styles["subheading"]))

        cost_rows = [["Cost Item", "USD", local_currency]]

        if isinstance(line_items, dict):
            # Already in label->amount format (bridged)
            for label, amount_usd in line_items.items():
                cost_rows.append([label, f"${float(amount_usd):,.0f}", "N/A"])
        elif isinstance(line_items, list):
            # Original list of CostLineItem dicts
            for item in line_items:
                if isinstance(item, dict):
                    cost_rows.append([
                        item.get("label", ""),
                        f"${item.get('amount_usd', 0):,.0f}",
                        f"{item.get('amount_local', 0):,.0f}",
                    ])

        # Total row
        total_usd = result.get("total_employer_cost_usd", 0)
        total_local = result.get("total_employer_cost_local", 0)
        cost_rows.append(["Total Employer Cost", f"${total_usd:,.0f}", f"{total_local:,.0f}"])

        cost_table = Table(cost_rows, colWidths=[200, 100, 100])
        cost_style_cmds: list = [
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (1, 1), (-1, -1), "Courier"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 1.5, TEXT_DARK),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]

        # Alternating rows
        for row_idx in range(1, len(cost_rows) - 1):
            if row_idx % 2 == 0:
                cost_style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), LIGHT_ROW))

        cost_table.setStyle(TableStyle(cost_style_cmds))
        elements.append(cost_table)
        elements.append(Spacer(1, 12))

        # Cost rating
        cost_rating = result.get("cost_rating") or result.get("overall_rating")
        if isinstance(cost_rating, dict):
            rating_level = cost_rating.get("overall_rating", cost_rating.get("level", "N/A"))
            bench_low = cost_rating.get("benchmark_low_usd", cost_rating.get("typical_range_low_usd", 0))
            bench_high = cost_rating.get("benchmark_high_usd", cost_rating.get("typical_range_high_usd", 0))

            color_map = {"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"}
            rating_color = color_map.get(rating_level, "#888888")

            elements.append(Paragraph("Cost Rating", self.styles["subheading"]))
            elements.append(
                Paragraph(
                    f'<font color="{rating_color}"><b>{rating_level}</b></font> '
                    f"&mdash; Regional benchmark: USD {bench_low:,.0f} &ndash; USD {bench_high:,.0f}",
                    self.styles["body"],
                )
            )
            elements.append(Spacer(1, 8))

        # AI Insights
        insights = result.get("insights_text") or result.get("insights_paragraph", "")
        if insights:
            elements.append(Paragraph("AI Insights", self.styles["subheading"]))
            elements.append(Paragraph(str(insights), self.styles["body"]))
            elements.append(Spacer(1, 8))

        # PE Risk section
        pe_risk = result.get("pe_risk")
        if isinstance(pe_risk, dict):
            elements.extend(self._build_pe_section(pe_risk))

        return elements

    def _build_pe_section(self, pe_risk: dict) -> list:
        """Build PE risk assessment flowables."""
        elements: list = []

        risk_level = pe_risk.get("risk_level", "N/A")
        color_map = {"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"}
        risk_color = color_map.get(risk_level, "#888888")

        elements.append(Paragraph("Permanent Establishment Risk", self.styles["subheading"]))
        elements.append(
            Paragraph(
                f'<font color="{risk_color}"><b>{risk_level}</b></font>',
                self.styles["body"],
            )
        )

        summary = pe_risk.get("summary", "")
        if summary:
            elements.append(Paragraph(str(summary), self.styles["body"]))

        treaty_info = pe_risk.get("treaty_info", "")
        if treaty_info:
            elements.append(Paragraph(f"<b>Treaty:</b> {treaty_info}", self.styles["body"]))

        economic_note = pe_risk.get("economic_employer_note", "")
        if economic_note:
            elements.append(Paragraph(f"<b>Economic employer:</b> {economic_note}", self.styles["body"]))

        # PE timeline bar
        threshold_days = pe_risk.get("pe_threshold_days", 183)
        assignment_days = pe_risk.get("assignment_days", 0)
        if assignment_days > 0:
            timeline = self._build_pe_timeline_bar(assignment_days, threshold_days)
            elements.append(Spacer(1, 4))
            elements.append(timeline)
            elements.append(Spacer(1, 4))

        mitigation = pe_risk.get("mitigation_steps", [])
        if mitigation:
            elements.append(Paragraph("<b>Mitigation Steps:</b>", self.styles["body"]))
            for step in mitigation:
                elements.append(
                    Paragraph(f"&bull; {step}", self.styles["body"])
                )

        return elements

    def _build_pe_timeline_bar(self, assignment_days: int, threshold_days: int) -> Drawing:
        """Build a horizontal bar showing assignment duration vs PE threshold."""
        drawing = Drawing(400, 40)
        max_days = max(assignment_days, threshold_days) * 1.2
        bar_width = 350

        # Bar background
        from reportlab.graphics.shapes import Rect, Line

        bg_rect = Rect(25, 10, bar_width, 20, fillColor=HexColor("#eeeeee"), strokeColor=None)
        drawing.add(bg_rect)

        # Duration bar
        duration_w = min((assignment_days / max_days) * bar_width, bar_width)
        exceeds = assignment_days > threshold_days
        bar_color = HexColor("#e74c3c") if exceeds else HexColor("#2ecc71")
        dur_rect = Rect(25, 10, duration_w, 20, fillColor=bar_color, strokeColor=None)
        drawing.add(dur_rect)

        # Threshold marker
        threshold_x = 25 + min((threshold_days / max_days) * bar_width, bar_width)
        threshold_line = Line(threshold_x, 5, threshold_x, 35, strokeColor=TEXT_DARK, strokeWidth=2)
        drawing.add(threshold_line)

        # Labels
        dur_label = String(30, 16, f"{assignment_days} days", fontSize=8, fontName="Helvetica", fillColor=WHITE)
        drawing.add(dur_label)

        thr_label = String(threshold_x, 37, f"PE: {threshold_days}d", fontSize=7, fontName="Helvetica", fillColor=TEXT_DARK, textAnchor="middle")
        drawing.add(thr_label)

        return drawing

    def _build_disclaimer_page(self) -> list:
        """Build disclaimer page flowables."""
        elements: list = []

        elements.append(Paragraph("Important Disclaimers", self.styles["heading"]))
        elements.append(Spacer(1, 12))

        # Main disclaimer text
        elements.append(Paragraph(config.PDF_DISCLAIMER, self.styles["disclaimer"]))
        elements.append(Spacer(1, 12))

        # Additional bullet points
        bullets = [
            "All cost estimates are generated by AI and may not reflect actual tax obligations",
            "Tax laws change frequently; estimates are based on information available at generation time",
            "This analysis should be reviewed by qualified tax and legal professionals",
            "Exchange rates are indicative and subject to market fluctuation",
        ]
        for bullet in bullets:
            elements.append(
                Paragraph(f"&bull; {bullet}", self.styles["disclaimer"])
            )

        elements.append(Spacer(1, 24))
        elements.append(
            Paragraph(
                f"&copy; {datetime.now().year} {self.company_name}",
                self.styles["small"],
            )
        )

        return elements

    def _header_footer(self, canvas: Any, doc: Any) -> None:
        """Draw header and footer on every page."""
        canvas.saveState()
        page_width, page_height = letter

        # Header left: company name
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(TEXT_DARK)
        canvas.drawString(0.75 * inch, page_height - 0.6 * inch, self.company_name)

        # Header right: logo placeholder
        logo_x = page_width - 0.75 * inch - 0.8 * inch
        logo_y = page_height - 0.7 * inch
        canvas.setStrokeColor(HexColor("#cccccc"))
        canvas.setFillColor(LIGHT_ROW)
        canvas.rect(logo_x, logo_y, 0.8 * inch, 0.4 * inch, fill=1)
        canvas.setFillColor(HexColor("#999999"))
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(logo_x + 0.4 * inch, logo_y + 0.15 * inch, "LOGO")

        # Footer left: short disclaimer
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#888888"))
        canvas.drawString(
            0.75 * inch,
            0.4 * inch,
            "AI-generated estimate \u2013 not tax or legal advice",
        )

        # Footer right: page number
        canvas.drawRightString(
            page_width - 0.75 * inch,
            0.4 * inch,
            f"Page {doc.page}",
        )

        canvas.restoreState()
