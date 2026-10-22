"""PDF report generation and shareable URLs."""

from __future__ import annotations

import base64
import html
import io
import json
import shutil
import tempfile
import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from app.container.report_store import ReportStore
from app.entity.pdf_report import PdfReport

if TYPE_CHECKING:
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.entity.preference_profile import PreferenceProfile
    from app.entity.recommendation_set import RecommendationSet
    from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO


class ReportControl:
    """Stereotype: Control. Stateless PDF report generator."""

    def __init__(
        self,
        notifier: DataAvailabilityNotifier,
        reportStore: ReportStore | None = None,
        reportDir: Path | str | None = None,
        publicBaseUrl: str = "",
    ) -> None:
        """Create the report control with a short-lived report store."""
        self.notifier = notifier
        self.reportStore = reportStore or ReportStore()
        self.reportDir = Path(reportDir) if reportDir else Path(tempfile.mkdtemp(prefix="sgpropfinder-reports-"))
        self.reportDir.mkdir(parents=True, exist_ok=True)
        self.publicBaseUrl = publicBaseUrl.rstrip("/")

    def generatePdfReport(
        self,
        recommendations: RecommendationSet,
        details: list[NeighborhoodDetailDTO],
    ) -> PdfReport:
        """Render a PDF, store it locally and return secure download metadata."""
        report_id = uuid.uuid4().hex
        generated = datetime.now(timezone.utc)
        expires = generated + timedelta(minutes=15)
        filename = f"SGPropFinder_Report_{report_id[:8]}.pdf"
        path = self.reportDir / filename
        content = self._renderReport(recommendations, details)
        path.write_bytes(content)
        self.reportStore.add(report_id, path, expires)
        return PdfReport(
            reportId=report_id,
            generatedTime=generated,
            downloadUrl=f"{self.publicBaseUrl}/api/v1/reports/download/{report_id}",
            expiresAt=expires,
            fileName=filename,
            contentType="application/pdf",
            sizeBytes=len(content),
        )

    def exportToFile(self, report: PdfReport, filePath: str) -> bool:
        """Copy a stored report to a caller-supplied path."""
        source = self.reportStore.getPath(report.reportId)
        if source is None or not source.exists():
            return False
        target = Path(filePath)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        return True

    def generateShareableUrl(
        self,
        profile: PreferenceProfile,
        subzoneCodes: list[str],
        baseUrl: str = "/",
    ) -> str:
        """Serialize profile inputs and selected subzones into a query string."""
        payload = {
            "profile": _toJsonable(profile),
            "subzones": list(subzoneCodes),
        }
        encoded = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        separator = "&" if "?" in baseUrl else "?"
        return f"{baseUrl}{separator}{urlencode({'share': encoded})}"

    def _renderReport(
        self,
        recommendations: RecommendationSet,
        details: list[NeighborhoodDetailDTO],
    ) -> bytes:
        """Render the report directly with ReportLab Platypus."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        styles = getSampleStyleSheet()
        body = styles["BodyText"]
        small = ParagraphStyle(
            "Small",
            parent=body,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#475467"),
        )
        header = ParagraphStyle(
            "TableHeader",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
        )

        story = [
            Paragraph("Neighbourhood Recommendation Report", styles["Title"]),
            Spacer(1, 6),
            Paragraph(
                "Profile: "
                f"{html.escape(recommendations.profileId)} · Generated: "
                f"{recommendations.generatedTime.isoformat()} · Snapshot: "
                f"{html.escape(recommendations.dataSnapshotId)}",
                small,
            ),
            Spacer(1, 14),
            Paragraph("Ranked recommendations", styles["Heading2"]),
        ]

        recommendation_rows: list[list[Paragraph]] = [
            [
                Paragraph("Rank", header),
                Paragraph("Subzone", header),
                Paragraph("Score", header),
            ]
        ]
        for item in recommendations.getItems():
            recommendation_rows.append(
                [
                    Paragraph(str(item.rank), body),
                    Paragraph(html.escape(item.subzoneName), body),
                    Paragraph(f"{item.totalScore:.1f}", body),
                ]
            )
        if len(recommendation_rows) == 1:
            recommendation_rows.append(
                [Paragraph("—", body), Paragraph("No recommendations", body), Paragraph("—", body)]
            )
        recommendation_table = Table(
            recommendation_rows,
            colWidths=[18 * mm, 112 * mm, 28 * mm],
            repeatRows=1,
        )
        recommendation_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.extend([recommendation_table, Spacer(1, 16), Paragraph("Neighbourhood details", styles["Heading2"])])

        detail_rows: list[list[Paragraph]] = [
            [
                Paragraph("Subzone", header),
                Paragraph("Pricing", header),
                Paragraph("Green coverage", header),
                Paragraph("Commute", header),
            ]
        ]
        for detail in details:
            prices = ", ".join(
                f"{html.escape(flat)}: ${pricing.averagePrice:,.0f}"
                for flat, pricing in detail.pricing.items()
            )
            detail_rows.append(
                [
                    Paragraph(html.escape(detail.subzoneName), body),
                    Paragraph(prices or "No pricing data", body),
                    Paragraph(f"{detail.environment.greenCoveragePercent:.1f}%", body),
                    Paragraph(f"{detail.commute.durationMinutes} min", body),
                ]
            )
        if len(detail_rows) == 1:
            detail_rows.append(
                [
                    Paragraph("—", body),
                    Paragraph("No details", body),
                    Paragraph("—", body),
                    Paragraph("—", body),
                ]
            )
        detail_table = Table(
            detail_rows,
            colWidths=[42 * mm, 76 * mm, 22 * mm, 18 * mm],
            repeatRows=1,
        )
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.extend([detail_table, Spacer(1, 16), Paragraph("Data warnings", styles["Heading2"])])

        warnings = recommendations.warnings + [
            warning for detail in details for warning in detail.warnings
        ]
        messages = list(dict.fromkeys(warning.message for warning in warnings))
        if messages:
            for message in messages:
                story.append(Paragraph(f"• {html.escape(message)}", body))
                story.append(Spacer(1, 3))
        else:
            story.append(Paragraph("None", body))

        story.extend(
            [
                Spacer(1, 18),
                Paragraph("Generated by SG Property Finder.", small),
            ]
        )

        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            title="Neighbourhood Report",
            author="SG Property Finder",
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )
        document.build(story)
        return buffer.getvalue()


def _toJsonable(value: Any) -> Any:
    """Convert dataclasses, enums, dates and nested containers to JSON values."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return {key: _toJsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _toJsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_toJsonable(item) for item in value]
    return value
