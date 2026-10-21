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
        content = self._renderPdf(self._buildHtml(recommendations, details))
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

    def _buildHtml(self, recommendations: RecommendationSet, details: list[NeighborhoodDetailDTO]) -> str:
        rows = []
        for item in recommendations.getItems():
            rows.append(
                "<tr>"
                f"<td>{item.rank}</td>"
                f"<td>{html.escape(item.subzoneName)}</td>"
                f"<td>{item.totalScore:.1f}</td>"
                "</tr>"
            )
        detail_rows = []
        for detail in details:
            prices = ", ".join(
                f"{html.escape(flat)}: ${pricing.averagePrice:,.0f}"
                for flat, pricing in detail.pricing.items()
            )
            detail_rows.append(
                "<tr>"
                f"<td>{html.escape(detail.subzoneName)}</td>"
                f"<td>{prices or 'No pricing data'}</td>"
                f"<td>{detail.environment.greenCoveragePercent:.1f}%</td>"
                f"<td>{detail.commute.durationMinutes} min</td>"
                "</tr>"
            )
        warnings = recommendations.warnings + [w for detail in details for w in detail.warnings]
        warning_items = "".join(f"<li>{html.escape(w.message)}</li>" for w in warnings) or "<li>None</li>"
        return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Neighbourhood Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
h1 {{ font-size: 24px; }} h2 {{ margin-top: 24px; font-size: 18px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }}
th {{ background: #e2e8f0; }}
.small {{ color: #64748b; font-size: 12px; }}
</style></head><body>
<h1>Neighbourhood Recommendation Report</h1>
<p class="small">Profile: {html.escape(recommendations.profileId)} · Generated: {recommendations.generatedTime.isoformat()} · Snapshot: {html.escape(recommendations.dataSnapshotId)}</p>
<h2>Ranked recommendations</h2>
<table><thead><tr><th>Rank</th><th>Subzone</th><th>Score</th></tr></thead><tbody>{''.join(rows) or '<tr><td colspan="3">No recommendations</td></tr>'}</tbody></table>
<h2>Neighbourhood details</h2>
<table><thead><tr><th>Subzone</th><th>Pricing</th><th>Green coverage</th><th>Commute</th></tr></thead><tbody>{''.join(detail_rows) or '<tr><td colspan="4">No details</td></tr>'}</tbody></table>
<h2>Data warnings</h2><ul>{warning_items}</ul>
</body></html>"""

    def _renderPdf(self, document: str) -> bytes:
        """Render HTML with WeasyPrint when available, otherwise ReportLab."""
        if not self._weasyprintAvailable():
            return self._renderWithReportLab(document)
        try:
            from weasyprint import HTML  # type: ignore

            return HTML(string=document).write_pdf()
        except Exception:
            return self._renderWithReportLab(document)

    @staticmethod
    def _weasyprintAvailable() -> bool:
        """Check that the native Pango/GObject libraries needed by WeasyPrint exist."""
        try:
            import ctypes.util

            return bool(
                ctypes.util.find_library("gobject-2.0")
                or ctypes.util.find_library("libgobject-2.0-0")
            )
        except Exception:
            return False

    @staticmethod
    def _renderWithReportLab(document: str) -> bytes:
        """Dependency-light fallback used when WeasyPrint is unavailable."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, title="Neighbourhood Report")
        styles = getSampleStyleSheet()
        story = [Paragraph("Neighbourhood Recommendation Report", styles["Title"]), Spacer(1, 12)]
        text = html.unescape(document)
        # Keep the fallback simple: render the text content, not the HTML layout.
        import re

        plain = re.sub(r"<[^>]+>", "\n", text)
        for line in [line.strip() for line in plain.splitlines() if line.strip()]:
            story.append(Paragraph(html.escape(line), styles["BodyText"]))
            story.append(Spacer(1, 4))
        doc.build(story)
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
