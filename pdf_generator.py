"""
PDF Generator for Legal Cases
Converts case JSON data to formatted PDF documents
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import io
from datetime import datetime


class LegalCasePDF:
    """Generate professional PDF documents from legal case JSON data."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles for legal documents."""

        # Title style
        self.styles.add(ParagraphStyle(
            name='CaseTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor='#1a1a1a',
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor='#0369a1',
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='#4a5568',
            spaceAfter=4,
            fontName='Helvetica'
        ))

        # Legal text style (justified, like court documents)
        self.styles.add(ParagraphStyle(
            name='LegalText',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14,
            fontName='Times-Roman'
        ))

    def generate_pdf(self, case_data: dict) -> io.BytesIO:
        """
        Generate a PDF from case JSON data.

        Args:
            case_data: Dictionary containing case information

        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Build the document content
        story = []

        # Header with case name
        case_name = case_data.get('name', 'Unknown Case')
        story.append(Paragraph(case_name, self.styles['CaseTitle']))
        story.append(Spacer(1, 0.2 * inch))

        # Case metadata section
        story.append(Paragraph('Case Information', self.styles['SectionHeader']))

        metadata_items = [
            ('Case ID', case_data.get('id')),
            ('Citation', self._format_citations(case_data.get('citations', []))),
            ('Decision Date', case_data.get('decision_date')),
            ('Court', case_data.get('court', {}).get('name', 'Unknown')),
            ('Jurisdiction', case_data.get('jurisdiction', {}).get('name_long', 'Unknown')),
            ('Docket Number', case_data.get('docket_number')),
        ]

        for label, value in metadata_items:
            if value:
                story.append(Paragraph(
                    f"<b>{label}:</b> {value}",
                    self.styles['Metadata']
                ))

        story.append(Spacer(1, 0.3 * inch))

        # Opinions section
        opinions = case_data.get('casebody', {}).get('opinions', [])
        if opinions:
            story.append(Paragraph('Opinions', self.styles['SectionHeader']))

            for i, opinion in enumerate(opinions):
                # Opinion metadata
                opinion_type = opinion.get('type', 'Opinion').title()
                author = opinion.get('author', 'Unknown')

                story.append(Paragraph(
                    f"<b>{opinion_type}</b> by {author}",
                    self.styles['Metadata']
                ))
                story.append(Spacer(1, 0.1 * inch))

                # Opinion text
                text = opinion.get('text', '')
                if text:
                    # Clean and format the text
                    text = self._clean_text(text)
                    story.append(Paragraph(text, self.styles['LegalText']))

                # Add space between opinions
                if i < len(opinions) - 1:
                    story.append(Spacer(1, 0.2 * inch))

        # Cited cases section
        cites_to = case_data.get('cites_to', [])
        if cites_to:
            story.append(PageBreak())
            story.append(Paragraph('Cases Cited', self.styles['SectionHeader']))

            for cite in cites_to[:20]:  # Limit to first 20 citations
                cite_text = cite.get('cite', 'Unknown')
                story.append(Paragraph(f"• {cite_text}", self.styles['Metadata']))

        # Footer with generation timestamp
        story.append(Spacer(1, 0.5 * inch))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(
            f"<i>Generated by Legal RAG System on {timestamp}</i>",
            self.styles['Metadata']
        ))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _format_citations(self, citations: list) -> str:
        """Format citations list into a readable string."""
        if not citations:
            return 'N/A'

        official = [c['cite'] for c in citations if c.get('type') == 'official']
        if official:
            return official[0]

        if citations:
            return citations[0].get('cite', 'N/A')

        return 'N/A'

    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for PDF rendering."""
        # Remove excessive whitespace
        text = ' '.join(text.split())

        # Escape special characters for reportlab
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        # Limit length to prevent massive PDFs
        max_length = 50000
        if len(text) > max_length:
            text = text[:max_length] + '...\n\n[Text truncated for brevity]'

        return text


def generate_case_pdf(case_data: dict) -> io.BytesIO:
    """
    Convenience function to generate PDF from case data.

    Args:
        case_data: Dictionary containing case information

    Returns:
        BytesIO buffer containing the PDF
    """
    generator = LegalCasePDF()
    return generator.generate_pdf(case_data)
