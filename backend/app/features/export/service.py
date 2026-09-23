"""
Professional PDF export service.

Provides:
1. Single-analysis PDF reports.
2. Current-batch PDF reports.
3. Complete user-history PDF reports.

CSV export is intentionally not supported.
"""

import datetime as dt
import io
from collections import Counter

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import inch

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

from app.models.analysis import AnalysisResult


# =========================================================
# TEXT HELPERS
# =========================================================

def _safe_text(value) -> str:
    """
    Convert database values into safe ReportLab text.
    """
    if value is None:
        return ""

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def _percentage(value: float, total: int) -> float:
    if total <= 0:
        return 0.0

    return (value / total) * 100.0


# =========================================================
# STYLES
# =========================================================

def _styles():
    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=21,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1a237e"),
            spaceAfter=8,
        ),

        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#666666"),
            spaceAfter=14,
        ),

        "heading": ParagraphStyle(
            "ReportHeading",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#283593"),
            spaceBefore=8,
            spaceAfter=8,
        ),

        "body": ParagraphStyle(
            "ReportBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
        ),

        "small": ParagraphStyle(
            "ReportSmall",
            parent=styles["BodyText"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#555555"),
        ),

        "verdict_hate": ParagraphStyle(
            "VerdictHate",
            parent=styles["BodyText"],
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#c62828"),
            spaceAfter=6,
        ),

        "verdict_safe": ParagraphStyle(
            "VerdictSafe",
            parent=styles["BodyText"],
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#2e7d32"),
            spaceAfter=6,
        ),
    }


# =========================================================
# PAGE HEADER / FOOTER
# =========================================================

def _draw_page(canvas, doc):
    canvas.saveState()

    width, height = letter

    canvas.setStrokeColor(
        colors.HexColor("#dddddd")
    )

    canvas.line(
        0.65 * inch,
        0.48 * inch,
        width - 0.65 * inch,
        0.48 * inch,
    )

    canvas.setFont("Helvetica", 7)

    canvas.setFillColor(
        colors.HexColor("#777777")
    )

    canvas.drawString(
        0.65 * inch,
        0.3 * inch,
        "Meme Hate Speech Detection System",
    )

    canvas.drawRightString(
        width - 0.65 * inch,
        0.3 * inch,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# =========================================================
# ANALYTICS
# =========================================================

def _calculate_analytics(
    results: list[AnalysisResult],
):
    total = len(results)

    hate_count = sum(
        1
        for result in results
        if result.is_hate
    )

    safe_count = total - hate_count

    hate_scores = [
        float(result.hate_score or 0)
        for result in results
    ]

    avg_hate_score = (
        sum(hate_scores) / len(hate_scores)
        if hate_scores
        else 0.0
    )

    max_hate_score = (
        max(hate_scores)
        if hate_scores
        else 0.0
    )

    category_counter = Counter(
        (
            result.category
            or "none"
        )
        for result in results
        if result.is_hate
    )

    return {
        "total": total,
        "hate_count": hate_count,
        "safe_count": safe_count,
        "hate_percentage": _percentage(
            hate_count,
            total,
        ),
        "safe_percentage": _percentage(
            safe_count,
            total,
        ),
        "avg_hate_score": avg_hate_score,
        "max_hate_score": max_hate_score,
        "categories": category_counter,
    }


# =========================================================
# SUMMARY TABLE
# =========================================================

def _summary_table(analytics):
    data = [
        [
            "Total",
            "Hateful",
            "Safe",
            "Hate Rate",
            "Avg Hate Score",
            "Max Hate Score",
        ],
        [
            str(analytics["total"]),
            str(analytics["hate_count"]),
            str(analytics["safe_count"]),
            f'{analytics["hate_percentage"]:.1f}%',
            f'{analytics["avg_hate_score"]:.1f}%',
            f'{analytics["max_hate_score"]:.1f}%',
        ],
    ]

    table = Table(
        data,
        colWidths=[
            0.95 * inch,
            0.95 * inch,
            0.95 * inch,
            1.0 * inch,
            1.15 * inch,
            1.15 * inch,
        ],
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#283593"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold",
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#cccccc"),
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
        ])
    )

    return table


# =========================================================
# HATE VS SAFE PIE CHART
# =========================================================

def _hate_safe_chart(analytics):
    drawing = Drawing(
        330,
        220,
    )

    pie = Pie()

    pie.x = 65
    pie.y = 25
    pie.width = 150
    pie.height = 150

    pie.data = [
        analytics["hate_count"],
        analytics["safe_count"],
    ]

    pie.labels = [
        f'Hateful ({analytics["hate_count"]})',
        f'Safe ({analytics["safe_count"]})',
    ]

    pie.slices.strokeWidth = 0.5

    if analytics["total"] > 0:
        pie.slices[0].fillColor = (
            colors.HexColor("#c62828")
        )
        pie.slices[1].fillColor = (
            colors.HexColor("#2e7d32")
        )

    drawing.add(pie)

    legend = Legend()

    legend.x = 220
    legend.y = 115

    legend.colorNamePairs = [
        (
            colors.HexColor("#c62828"),
            f'Hateful: {analytics["hate_count"]}',
        ),
        (
            colors.HexColor("#2e7d32"),
            f'Safe: {analytics["safe_count"]}',
        ),
    ]

    legend.fontName = "Helvetica"
    legend.fontSize = 8

    drawing.add(legend)

    return drawing


# =========================================================
# CATEGORY BAR CHART
# =========================================================

def _category_chart(analytics):
    categories = list(
        analytics["categories"].keys()
    )

    values = [
        analytics["categories"][category]
        for category in categories
    ]

    if not categories:
        return Paragraph(
            "No hateful categories were detected.",
            _styles()["body"],
        )

    drawing = Drawing(
        460,
        250,
    )

    chart = VerticalBarChart()

    chart.x = 55
    chart.y = 45
    chart.height = 160
    chart.width = 360

    chart.data = [values]

    chart.categoryAxis.categoryNames = categories

    chart.valueAxis.valueMin = 0

    max_value = max(values)

    chart.valueAxis.valueMax = max(
        1,
        max_value + 1,
    )

    chart.valueAxis.valueStep = 1

    chart.bars[0].fillColor = (
        colors.HexColor("#5c6bc0")
    )

    chart.strokeColor = (
        colors.HexColor("#cccccc")
    )

    chart.valueAxis.labels.fontSize = 8
    chart.categoryAxis.labels.fontSize = 7

    chart.categoryAxis.labels.angle = 20

    drawing.add(chart)

    return drawing


# =========================================================
# INDIVIDUAL RESULT TABLE
# =========================================================

def _result_table(result, index):
    verdict = (
        "HATEFUL"
        if result.is_hate
        else "SAFE"
    )

    timestamp = (
        result.timestamp.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if result.timestamp
        else ""
    )

    info = [
        [
            "Analysis ID",
            str(result.id),
        ],
        [
            "Filename",
            _safe_text(result.filename),
        ],
        [
            "Date",
            timestamp,
        ],
        [
            "Result",
            verdict,
        ],
        [
            "Hate Score",
            f"{float(result.hate_score or 0):.2f}%",
        ],
        [
            "Safe Score",
            f"{float(result.safe_score or 0):.2f}%",
        ],
        [
            "Category",
            _safe_text(result.category),
        ],
        [
            "Threshold",
            f"{result.threshold_used}%",
        ],
        [
            "OCR Text",
            _safe_text(result.extracted_text),
        ],
        [
            "Caption",
            _safe_text(result.caption),
        ],
    ]

    converted = []

    for row in info:
        converted.append([
            Paragraph(
                f"<b>{row[0]}</b>",
                _styles()["small"],
            ),
            Paragraph(
                row[1],
                _styles()["small"],
            ),
        ])

    table = Table(
        converted,
        colWidths=[
            1.35 * inch,
            5.75 * inch,
        ],
    )

    verdict_color = (
        colors.HexColor("#ffebee")
        if result.is_hate
        else colors.HexColor("#e8f5e9")
    )

    table.setStyle(
        TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#cccccc"),
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#f3f3f3"),
            ),
            (
                "BACKGROUND",
                (1, 3),
                (1, 3),
                verdict_color,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ])
    )

    return KeepTogether([
        Paragraph(
            f"{index}. {_safe_text(result.filename)}",
            _styles()["heading"],
        ),
        table,
        Spacer(1, 14),
    ])


# =========================================================
# PROFESSIONAL REPORT HEADER
# =========================================================

def _report_header(
    title: str,
    subtitle: str,
):
    styles = _styles()

    return [
        Paragraph(
            title,
            styles["title"],
        ),
        Paragraph(
            subtitle,
            styles["subtitle"],
        ),
    ]


# =========================================================
# SINGLE ANALYSIS PDF
# =========================================================

def export_single_pdf(
    result: AnalysisResult,
) -> bytes:
    """
    Generate a detailed PDF report for exactly one analysis.
    """

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
    )

    styles = _styles()

    story = []

    story.extend(
        _report_header(
            "Meme Hate Speech Detection",
            "Individual Analysis Report",
        )
    )

    story.append(
        Paragraph(
            f"Generated: "
            f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["small"],
        )
    )

    story.append(Spacer(1, 12))

    verdict = (
        "HATEFUL"
        if result.is_hate
        else "SAFE"
    )

    verdict_style = (
        styles["verdict_hate"]
        if result.is_hate
        else styles["verdict_safe"]
    )

    story.append(
        Paragraph(
            f"<b>Detection Result: {verdict}</b>",
            verdict_style,
        )
    )

    analytics = _calculate_analytics(
        [result]
    )

    story.append(
        _summary_table(analytics)
    )

    story.append(Spacer(1, 14))

    story.append(
        Paragraph(
            "Analysis Details",
            styles["heading"],
        )
    )

    story.append(
        _result_table(
            result,
            1,
        )
    )

    story.append(
        Paragraph(
            "This report contains only the selected "
            "analysis record.",
            styles["small"],
        )
    )

    doc.build(
        story,
        onFirstPage=_draw_page,
        onLaterPages=_draw_page,
    )

    return buffer.getvalue()


# =========================================================
# MULTI-ANALYSIS PDF
# =========================================================

def export_pdf(
    results: list[AnalysisResult],
) -> bytes:
    """
    Generate a professional PDF containing exactly the
    records supplied to this function.

    This function is used by both:
    - Home current-batch export
    - Complete history export
    """

    if not results:
        raise ValueError(
            "Cannot generate a PDF without analysis records."
        )

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
    )

    styles = _styles()

    analytics = _calculate_analytics(
        results
    )

    story = []

    # -----------------------------------------------------
    # COVER / HEADER
    # -----------------------------------------------------

    story.extend(
        _report_header(
            "Meme Hate Speech Detection",
            "Analysis & Analytics Report",
        )
    )

    story.append(
        Paragraph(
            f"Generated: "
            f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["small"],
        )
    )

    story.append(Spacer(1, 12))

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Executive Summary",
            styles["heading"],
        )
    )

    story.append(
        _summary_table(analytics)
    )

    story.append(Spacer(1, 18))

    # -----------------------------------------------------
    # HATE VS SAFE CHART
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Hateful vs Safe Distribution",
            styles["heading"],
        )
    )

    story.append(
        _hate_safe_chart(analytics)
    )

    story.append(Spacer(1, 10))

    # -----------------------------------------------------
    # CATEGORY DISTRIBUTION
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Hate Category Distribution",
            styles["heading"],
        )
    )

    story.append(
        _category_chart(analytics)
    )

    story.append(PageBreak())

    # -----------------------------------------------------
    # INDIVIDUAL ANALYSES
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Individual Meme Analysis",
            styles["heading"],
        )
    )

    story.append(
        Paragraph(
            f"This report contains exactly "
            f"{len(results)} analysis record(s).",
            styles["body"],
        )
    )

    story.append(Spacer(1, 10))

    for index, result in enumerate(
        results,
        start=1,
    ):
        story.append(
            _result_table(
                result,
                index,
            )
        )

    # -----------------------------------------------------
    # FINAL SUMMARY
    # -----------------------------------------------------

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "Report Summary",
            styles["heading"],
        )
    )

    story.append(
        Paragraph(
            f"Total analysed: {analytics['total']}<br/>"
            f"Hateful: {analytics['hate_count']} "
            f"({analytics['hate_percentage']:.1f}%)<br/>"
            f"Safe: {analytics['safe_count']} "
            f"({analytics['safe_percentage']:.1f}%)<br/>"
            f"Average hate score: "
            f"{analytics['avg_hate_score']:.1f}%<br/>"
            f"Maximum hate score: "
            f"{analytics['max_hate_score']:.1f}%",
            styles["body"],
        )
    )

    doc.build(
        story,
        onFirstPage=_draw_page,
        onLaterPages=_draw_page,
    )

    return buffer.getvalue()