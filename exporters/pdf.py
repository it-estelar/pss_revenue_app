import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from utils import format_money

HEADER_BLUE = colors.HexColor("#062A73")
DARK_TEXT = colors.HexColor("#16324F")
LIGHT_FILL = colors.HexColor("#F4F6F8")
ALT_FILL = colors.HexColor("#EEF3F8")
TOTAL_FILL = colors.HexColor("#DCE6F8")
WHITE = colors.white
KPI_FILL = colors.HexColor("#EEF3FB")
GRID = colors.HexColor("#D6DFEA")


def _maybe_logo():
    candidates = [
        Path(__file__).resolve().parent.parent / "logo_estelar_transparent.png",
        Path(__file__).resolve().parent.parent / "logo_estelar.png",
        Path(__file__).resolve().parent / "logo_estelar_transparent.png",
        Path(__file__).resolve().parent / "logo_estelar.png",
        Path.cwd() / "logo_estelar_transparent.png",
        Path.cwd() / "logo_estelar.png",
        Path("/mnt/data/logo_estelar_transparent.png"),
        Path("/mnt/data/logo_estelar.png"),
    ]

    for logo in candidates:
        if logo.exists() and logo.is_file():
            return str(logo)

    return None


def _format_display(frame):
    display = frame.copy()

    month_names = {
        "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
    }

    for col in display.columns:
        name = str(col).upper().strip()

        if (
            "REVENUE" in name
            or "MONTO USD" in name
            or "VALOR DE LA TARIFA" in name
            or "YIELD" in name
            or "INGRESO USD" in name
            or "INGRESO" in name
            or name in month_names
            or name == "TOTAL"
        ):
            display[col] = display[col].apply(
                lambda x: "" if str(x) in {"", "nan", "None"} else format_money(x, 2)
            )
        elif "% INGRESO" in name or "% DEL TOTAL" in name:
            display[col] = display[col].apply(
                lambda v: "" if str(v) in {"", "nan", "None"} else format_money(v, 2) + "%"
            )
        elif (
            "CUPONES" in name
            or "TICKETS" in name
            or "TKTT #" in name
            or "EMDA #" in name
            or "EMDS #" in name
            or "OTROS #" in name
            or "CANTIDAD_DE_CUPONES" in name
        ):
            display[col] = display[col].apply(
                lambda v: (
                    f"{int(round(float(v))):,}".replace(",", ".")
                    if str(v) not in {"", "nan", "None"}
                    else ""
                )
            )

    return display


def _build_chart_flowable(chart_png, width_mm=240, height_mm=108):
    if not chart_png:
        return None

    if isinstance(chart_png, (bytes, bytearray)):
        buffer = io.BytesIO(chart_png)
        buffer.seek(0)
        chart = Image(buffer, width=width_mm * mm, height=height_mm * mm)
        chart.hAlign = "CENTER"
        return chart

    if hasattr(chart_png, "read"):
        try:
            chart_png.seek(0)
        except Exception:
            pass
        chart = Image(chart_png, width=width_mm * mm, height=height_mm * mm)
        chart.hAlign = "CENTER"
        return chart

    chart = Image(str(chart_png), width=width_mm * mm, height=height_mm * mm)
    chart.hAlign = "CENTER"
    return chart


def _build_kpi_table(kpi_pairs):
    if not kpi_pairs:
        return None

    row = []
    for label, value in kpi_pairs:
        cell = Paragraph(
            f"<b>{label}</b><br/>{value}",
            ParagraphStyle(
                "KPIStyle",
                fontName="Helvetica",
                fontSize=10,
                leading=13,
                textColor=DARK_TEXT,
                alignment=1,
            ),
        )
        row.append(cell)

    table = Table([row], colWidths=[66 * mm] * len(row))
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), KPI_FILL),
                ("BOX", (0, 0), (-1, -1), 1, GRID),
                ("INNERGRID", (0, 0), (-1, -1), 0.8, GRID),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _build_title_block(title, styled, styles):
    if styled:
        title_style = ParagraphStyle(
            "BigTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            alignment=1,
            textColor=WHITE,
        )
        title_table = Table([[Paragraph(title, title_style)]], colWidths=[265 * mm])
        title_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HEADER_BLUE),
                    ("BOX", (0, 0), (-1, -1), 0, HEADER_BLUE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return title_table

    return Paragraph(title, styles["Title"])


def build_single_table_pdf(
    title,
    df,
    *,
    styled=False,
    subtitle=None,
    max_rows=5000,
    chart_png=None,
    kpi_pairs=None,
    chart_first_page=False,
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    logo = _maybe_logo()
    if styled and logo:
        story.append(Image(logo, width=55 * mm, height=18 * mm))
        story.append(Spacer(1, 5))

    story.append(_build_title_block(title, styled, styles))
    story.append(Spacer(1, 6))

    if subtitle:
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9 if styled else 10,
            leading=12,
            alignment=1 if styled else 0,
            textColor=DARK_TEXT,
        )
        story.append(Paragraph(subtitle, subtitle_style))
        story.append(Spacer(1, 8))

    kpi_table = _build_kpi_table(kpi_pairs)
    if kpi_table is not None:
        story.append(kpi_table)
        story.append(Spacer(1, 8))

    chart_flowable = _build_chart_flowable(chart_png)
    if chart_flowable is not None:
        story += [chart_flowable, Spacer(1, 8)]

    effective_chart_first_page = chart_first_page or (chart_flowable is not None)

    if effective_chart_first_page:
        story.append(PageBreak())

    if chart_flowable is not None:
        detail_style = ParagraphStyle(
            "DetailHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=14,
            alignment=0,
            textColor=DARK_TEXT,
        )
        story.append(Paragraph("Detalle tabular", detail_style))
        story.append(Spacer(1, 6))

    frame = df.head(max_rows).copy()
    frame = _format_display(frame)

    data = [list(frame.columns)] + frame.astype(str).values.tolist()
    table = Table(data, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.7, GRID),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_FILL, ALT_FILL]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]

    if len(data) > 1:
        last_row_idx = len(data) - 1
        first_cell = str(data[last_row_idx][0]).upper().strip()
        if "TOTAL" in first_cell:
            style_cmds += [
                ("BACKGROUND", (0, last_row_idx), (-1, last_row_idx), TOTAL_FILL),
                ("FONTNAME", (0, last_row_idx), (-1, last_row_idx), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, last_row_idx), (-1, last_row_idx), DARK_TEXT),
            ]

    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()