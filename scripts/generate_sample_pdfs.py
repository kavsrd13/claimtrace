"""
Script to generate professional, publication-quality sample PDF contracts
for testing ClaimTrace with PDF parsing and extraction.
"""

from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT_DIR = Path(__file__).resolve().parent.parent / "sample_documents"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Color Palette
PRIMARY = HexColor("#0F172A")    # Deep Slate
SECONDARY = HexColor("#1E3A8A")  # Navy Blue
ACCENT = HexColor("#2563EB")     # Royal Blue
TEXT = HexColor("#1E293B")       # Dark Charcoal
MUTED = HexColor("#64748B")      # Slate Gray
BORDER = HexColor("#E2E8F0")     # Light Border
BG_LIGHT = HexColor("#F8FAFC")   # Soft Off-white


def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        alignment=1,  # Center
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "DocSubtitle",
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=MUTED,
        alignment=1,
        spaceAfter=15,
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "BodyBold",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "BulletItem",
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT,
        leftIndent=15,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=PRIMARY,
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT,
        alignment=0,
    ))
    return styles


def build_pdf_draft_a(filename: Path):
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = get_styles()
    story = []

    # Title & Metadata
    story.append(Paragraph("MASTER SERVICES AGREEMENT", styles["DocTitle"]))
    story.append(Paragraph("Version 1.0 (Draft A) &bull; Standard Commercial Terms", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=4, spaceAfter=14))

    intro_text = (
        "This Master Services Agreement (&ldquo;Agreement&rdquo;) is made and entered into as of "
        "<b>January 15, 2025</b> (&ldquo;Effective Date&rdquo;), by and between <b>CloudScale Technologies Inc.</b>, "
        "a Delaware corporation with principal offices at 500 Enterprise Way, Suite 400, San Francisco, CA 94105 "
        "(&ldquo;Provider&rdquo;), and <b>Apex Global Financial LLC</b>, a Delaware limited liability company with principal offices "
        "at 120 Wall Street, 18th Floor, New York, NY 10005 (&ldquo;Client&rdquo;)."
    )
    story.append(Paragraph(intro_text, styles["Body"]))
    story.append(Spacer(1, 8))

    # Recitals
    story.append(Paragraph("RECITALS", styles["SectionHeader"]))
    story.append(Paragraph(
        "WHEREAS, Provider provides managed cloud hosting administration, relational database optimization, and IT systems engineering; and "
        "WHEREAS, Client desires to engage Provider to oversee its mission-critical cloud environments on AWS and Microsoft Azure, "
        "and Provider agrees to render such services on the terms stated herein.",
        styles["Body"],
    ))

    # Section 1: Scope
    story.append(Paragraph("1. SCOPE OF SERVICES & TECHNICAL SUPPORT", styles["SectionHeader"]))
    story.append(Paragraph(
        "1.1 <u>Core Infrastructure Administration</u>: Provider shall furnish Tier-1 systems administration, multi-region database index maintenance, "
        "automated configuration snapshots, and resource utilization monitoring across Client&rsquo;s cloud environments.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "1.2 <u>Operational Support Windows</u>: Technical assistance is available Monday through Friday from 8:00 AM to 8:00 PM Eastern Standard Time (EST), "
        "excluding federal banking holidays. Severity 1 emergency outage response is staffed twenty-four (24) hours per day, seven (7) days per week.",
        styles["Body"],
    ))

    # Section 2: SLA & Table
    story.append(Paragraph("2. SERVICE LEVEL AGREEMENT (SLA) & UPTIME COMMITMENT", styles["SectionHeader"]))
    story.append(Paragraph(
        "2.1 <u>Monthly Availability Target</u>: Provider guarantees that covered cloud services shall maintain a Monthly Uptime Percentage of not less than <b>99.9%</b> (&ldquo;three nines&rdquo;).",
        styles["Body"],
    ))
    story.append(Paragraph(
        "2.2 <u>Scheduled Maintenance</u>: Routine maintenance shall be performed on Sundays between 01:00 AM and 05:00 AM EST. Provider must provide at least forty-eight (48) hours advance written notice.",
        styles["Body"],
    ))

    sla_data = [
        [Paragraph("<b>Monthly Uptime Band</b>", styles["TableHeader"]), Paragraph("<b>Service Credit Percentage</b>", styles["TableHeader"])],
        [Paragraph("99.00% &ndash; 99.89%", styles["TableCell"]), Paragraph("5% credit applied against following month fee", styles["TableCell"])],
        [Paragraph("Below 99.00%", styles["TableCell"]), Paragraph("15% credit applied against following month fee", styles["TableCell"])],
    ]
    t = Table(sla_data, colWidths=[2.5 * inch, 4.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Section 3: Fees
    story.append(Paragraph("3. PRICING, BILLING SCHEDULE & PAYMENT TERMS", styles["SectionHeader"]))
    story.append(Paragraph(
        "3.1 <u>Monthly Retainer</u>: Client shall pay a fixed fee of <b>$18,500.00 USD</b> per month, invoiced on the first day of each calendar month.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "3.2 <u>Settlement Term</u>: Invoices are payable <b>Net-30 days</b> from date of invoice.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "3.3 <u>Late Payments</u>: Unpaid balances accrue interest at <b>1.5% per month</b> or the statutory maximum, whichever is lower.",
        styles["Body"],
    ))

    # Section 4: Liability
    story.append(Paragraph("4. LIMITATION OF LIABILITY & INDEMNIFICATION", styles["SectionHeader"]))
    story.append(Paragraph(
        "4.1 <u>Liability Cap</u>: Total aggregate liability for either party under this Agreement is strictly capped at the <b>total fees paid by Client to Provider during the twelve (12) months preceding the incident</b>.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "4.2 <u>Consequential Damages</u>: In no event shall either party be liable for special, indirect, punitive, or consequential damages, including lost revenue or profits.",
        styles["Body"],
    ))

    # Section 5: Security & Privacy
    story.append(Paragraph("5. CONFIDENTIALITY & DATA PROTECTION", styles["SectionHeader"]))
    story.append(Paragraph(
        "5.1 <u>Confidentiality Period</u>: Confidentiality obligations survive for <b>five (5) years</b> post termination of this Agreement.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "5.2 <u>Security Standards</u>: Provider maintains annual SOC 2 Type II certification and complies with GDPR requirements.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "5.3 <u>Security Incident Notification</u>: In the event of a verified data compromise, Provider must inform Client in writing within <b>seventy-two (72) hours</b>.",
        styles["Body"],
    ))

    # Section 6: Term & Termination
    story.append(Paragraph("6. TERM, RENEWAL & CONVENIENCE TERMINATION", styles["SectionHeader"]))
    story.append(Paragraph(
        "6.1 <u>Initial Period</u>: Two (2) years from Effective Date, renewing annually unless sixty (60) days non-renewal notice is given.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "6.2 <u>Termination for Convenience</u>: Either party may terminate for convenience with <b>ninety (90) days advance notice</b>. "
        "If Client terminates early for convenience, Client must pay an early exit penalty equal to <b>twenty percent (20%)</b> of remaining contract fees.",
        styles["Body"],
    ))

    # Section 7: Governing Law
    story.append(Paragraph("7. GOVERNING LAW & JURISDICTION", styles["SectionHeader"]))
    story.append(Paragraph(
        "7.1 This Agreement is governed by the laws of the <b>State of Delaware</b>. Any dispute shall be settled by binding arbitration before the American Arbitration Association in Wilmington, Delaware.",
        styles["Body"],
    ))

    # Signatures
    story.append(Spacer(1, 15))
    sig_data = [
        [Paragraph("<b>CloudScale Technologies Inc.</b>", styles["BodyBold"]), Paragraph("<b>Apex Global Financial LLC</b>", styles["BodyBold"])],
        [Paragraph("By: <i>/s/ Marcus Vance</i>", styles["Body"]), Paragraph("By: <i>/s/ Eleanor Wright</i>", styles["Body"])],
        [Paragraph("Name: Marcus Vance", styles["Body"]), Paragraph("Name: Eleanor Wright", styles["Body"])],
        [Paragraph("Title: Chief Operating Officer", styles["Body"]), Paragraph("Title: VP of Technology Infrastructure", styles["Body"])],
        [Paragraph("Date: January 15, 2025", styles["Body"]), Paragraph("Date: January 15, 2025", styles["Body"])],
    ]
    st = Table(sig_data, colWidths=[3.25 * inch, 3.25 * inch])
    st.setStyle(TableStyle([
        ("LINEABOVE", (0, 1), (0, 1), 1, MUTED),
        ("LINEABOVE", (1, 1), (1, 1), 1, MUTED),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(st)

    doc.build(story)
    print(f"Created: {filename}")


def build_pdf_revision_b(filename: Path):
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = get_styles()
    story = []

    # Title & Metadata
    story.append(Paragraph("MASTER SERVICES AGREEMENT", styles["DocTitle"]))
    story.append(Paragraph("Version 2.0 (Revision B) &bull; Major Scope & High-Contrast Commercial Revision", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=2.0, color=HexColor("#DC2626"), spaceBefore=4, spaceAfter=14))

    intro_text = (
        "This Master Services Agreement (&ldquo;Agreement&rdquo;) is made and entered into as of "
        "<b>October 1, 2026</b> (&ldquo;Effective Date&rdquo;), by and between <b>CloudScale Technologies Inc.</b>, "
        "a California corporation with principal offices at 100 Mission Street, San Francisco, CA 94105 "
        "(&ldquo;Provider&rdquo;), and <b>Apex Global Financial LLC</b>, a Delaware limited liability company with principal offices "
        "at 120 Wall Street, 18th Floor, New York, NY 10005 (&ldquo;Client&rdquo;)."
    )
    story.append(Paragraph(intro_text, styles["Body"]))
    story.append(Spacer(1, 8))

    # Recitals
    story.append(Paragraph("RECITALS", styles["SectionHeader"]))
    story.append(Paragraph(
        "WHEREAS, Provider provides specialized AI supercomputing cluster administration, 24/7 Red-Team cyber warfare defense, "
        "and global multi-cloud orchestration across AWS, Azure, Google Cloud, and Oracle OCI; and "
        "WHEREAS, Client desires to retain Provider under an exclusive enterprise multi-year engagement with continuous operational coverage.",
        styles["Body"],
    ))

    # Section 1: Scope
    story.append(Paragraph("1. SCOPE OF SERVICES & TECHNICAL SUPPORT", styles["SectionHeader"]))
    story.append(Paragraph(
        "1.1 <u>Advanced AI & Multi-Cloud Infrastructure Scope</u>: Provider shall deliver dedicated GPU cluster management, "
        "autonomous neural network query optimization, multi-cloud redundancy across four cloud hyperscalers, and 24/7 active Managed Cyber Warfare Defense.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "1.2 <u>24/7 Real-Time Support</u>: Provider guarantees 24/7/365 live dedicated engineering support with guaranteed response times under <b>five (5) minutes</b> for all severity levels.",
        styles["Body"],
    ))

    # Section 2: SLA & Table
    story.append(Paragraph("2. SERVICE LEVEL AGREEMENT (SLA) & UPTIME COMMITMENT", styles["SectionHeader"]))
    story.append(Paragraph(
        "2.1 <u>Five Nines Availability Target</u>: Covered services shall maintain an ultra-high Monthly Uptime Percentage of not less than <b>99.999%</b> (&ldquo;five nines&rdquo;).",
        styles["Body"],
    ))
    story.append(Paragraph(
        "2.2 <u>Maintenance Windows</u>: Maintenance requires at least <b>seven (7) calendar days advance written notice</b>, permitted only on the first Sunday of each quarter.",
        styles["Body"],
    ))

    sla_data = [
        [Paragraph("<b>Monthly Uptime Band</b>", styles["TableHeader"]), Paragraph("<b>Service Credit Percentage</b>", styles["TableHeader"])],
        [Paragraph("99.990% &ndash; 99.998%", styles["TableCell"]), Paragraph("25% credit applied against subsequent invoice", styles["TableCell"])],
        [Paragraph("Below 99.990%", styles["TableCell"]), Paragraph("50% credit applied against subsequent invoice", styles["TableCell"])],
    ]
    t = Table(sla_data, colWidths=[2.5 * inch, 4.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Section 3: Fees
    story.append(Paragraph("3. PRICING, BILLING SCHEDULE & PAYMENT TERMS", styles["SectionHeader"]))
    story.append(Paragraph(
        "3.1 <u>Monthly Enterprise Retainer</u>: Client shall pay a monthly enterprise retainer of <b>$95,000.00 USD</b>, billed annually in advance.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "3.2 <u>Immediate Settlement Requirement</u>: Invoices are payable <b>Net-0 days (Due Immediately Upon Receipt)</b>.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "3.3 <u>Late Payments</u>: Unpaid balances accrue late interest at <b>5.0% per month</b>, compounding weekly.",
        styles["Body"],
    ))

    # Section 4: Liability
    story.append(Paragraph("4. LIMITATION OF LIABILITY & INDEMNIFICATION", styles["SectionHeader"]))
    story.append(Paragraph(
        "4.1 <u>Unlimited Liability</u>: <b>NO LIABILITY CAP SHALL APPLY.</b> The Parties explicitly agree that total aggregate liability "
        "arising under or related to this Agreement is <b>completely uncapped and unlimited</b> for all claims, breaches, and indemnities.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "4.2 <u>Consequential Damages</u>: Consequential, special, and exemplary damages are fully recoverable under this Agreement.",
        styles["Body"],
    ))

    # Section 5: Security & Privacy
    story.append(Paragraph("5. CONFIDENTIALITY & DATA PROTECTION", styles["SectionHeader"]))
    story.append(Paragraph(
        "5.1 <u>Perpetual Confidentiality</u>: Confidentiality obligations shall endure <b>in perpetuity</b> for all disclosures.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "5.2 <u>Compliance Standards</u>: Active certification and audits for SOC 2 Type II, ISO/IEC 27001:2022, FedRAMP High, and HIPAA Security Rule.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "5.3 <u>Emergency Breach Notification Window</u>: In the event of confirmed or suspected unauthorized data access, "
        "Provider must notify Client&rsquo;s Chief Information Security Officer (CISO) and relevant authorities within <b>two (2) hours</b>.",
        styles["Body"],
    ))

    # Section 6: Term & Termination
    story.append(Paragraph("6. TERM, RENEWAL & CONVENIENCE TERMINATION", styles["SectionHeader"]))
    story.append(Paragraph(
        "6.1 <u>Initial Period</u>: <b>Five (5) years</b> non-cancellable lock-in term from the Effective Date.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "6.2 <u>No Convenience Termination</u>: <b>Termination for convenience is strictly prohibited.</b> Any early termination by Client "
        "constitutes a material breach requiring immediate payment of <b>one hundred percent (100%) of all remaining contract fees</b> through the end of the five-year term as liquidated damages.",
        styles["Body"],
    ))

    # Section 7: Governing Law
    story.append(Paragraph("7. GOVERNING LAW & JURISDICTION", styles["SectionHeader"]))
    story.append(Paragraph(
        "7.1 This Agreement shall be governed strictly by the laws of the <b>State of California</b>. "
        "The Parties irrevocably submit to the exclusive jurisdiction of the <b>San Francisco County Superior Court</b> and explicitly waive any right to arbitration.",
        styles["Body"],
    ))

    # Signatures
    story.append(Spacer(1, 15))
    sig_data = [
        [Paragraph("<b>CloudScale Technologies Inc.</b>", styles["BodyBold"]), Paragraph("<b>Apex Global Financial LLC</b>", styles["BodyBold"])],
        [Paragraph("By: <i>/s/ Marcus Vance</i>", styles["Body"]), Paragraph("By: <i>/s/ Eleanor Wright</i>", styles["Body"])],
        [Paragraph("Name: Marcus Vance", styles["Body"]), Paragraph("Name: Eleanor Wright", styles["Body"])],
        [Paragraph("Title: Chief Operating Officer", styles["Body"]), Paragraph("Title: Chief Information Officer", styles["Body"])],
        [Paragraph("Date: March 1, 2026", styles["Body"]), Paragraph("Date: March 1, 2026", styles["Body"])],
    ]
    st = Table(sig_data, colWidths=[3.25 * inch, 3.25 * inch])
    st.setStyle(TableStyle([
        ("LINEABOVE", (0, 1), (0, 1), 1, MUTED),
        ("LINEABOVE", (1, 1), (1, 1), 1, MUTED),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(st)

    doc.build(story)
    print(f"Created: {filename}")


def build_pdf_saas_agreement(filename: Path):
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = get_styles()
    story = []

    story.append(Paragraph("ENTERPRISE SOFTWARE-AS-A-SERVICE (SaaS) SUBSCRIPTION AGREEMENT", styles["DocTitle"]))
    story.append(Paragraph("Commercial Subscription & End-User Licensing Terms", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=2.0, color=HexColor("#10B981"), spaceBefore=4, spaceAfter=14))

    intro_text = (
        "This SaaS Subscription Agreement (&ldquo;Agreement&rdquo;) is entered into as of <b>November 1, 2026</b>, "
        "by and between <b>QuantumLogic Systems Inc.</b>, a Washington corporation (&ldquo;Licensor&rdquo;), "
        "and <b>Apex Global Financial LLC</b>, a Delaware company (&ldquo;Licensee&rdquo;)."
    )
    story.append(Paragraph(intro_text, styles["Body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. SUBSCRIPTION GRANT & USER SEAT TIERS", styles["SectionHeader"]))
    story.append(Paragraph(
        "1.1 Licensor grants Licensee a worldwide, non-exclusive, non-transferable subscription license to access the QuantumLogic Cloud Analytics Platform for up to <b>500 named seats</b>.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "1.2 API Rate Limits: Standard enterprise quota allows up to <b>10,000,000 API calls per month</b> with burst rates capped at 500 requests per second.",
        styles["Body"],
    ))

    story.append(Paragraph("2. SUBSCRIPTION FEES & BILLING", styles["SectionHeader"]))
    story.append(Paragraph(
        "2.1 Annual Subscription Fee: Licensee shall pay an annual recurring platform subscription fee of <b>$320,000.00 USD</b>, billed in advance on a quarterly installment basis.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "2.2 Over-quota usage is billed in arrears at <b>$0.02 per 1,000 additional API calls</b>.",
        styles["Body"],
    ))

    story.append(Paragraph("3. INTELLECTUAL PROPERTY & DATA RIGHTS", styles["SectionHeader"]))
    story.append(Paragraph(
        "3.1 Licensor retains all title, ownership, patent rights, copyrights, and intellectual property rights in the underlying machine learning algorithms and software code.",
        styles["Body"],
    ))
    story.append(Paragraph(
        "3.2 Licensee retains absolute and exclusive ownership of all financial datasets and customer records processed through the platform.",
        styles["Body"],
    ))

    story.append(Paragraph("4. SERVICE AVAILABILITY & EXCLUSIONS", styles["SectionHeader"]))
    story.append(Paragraph(
        "4.1 Target availability is <b>99.5% uptime</b>, excluding third-party cloud outages, internet routing failures, or customer-side network disruptions.",
        styles["Body"],
    ))

    story.append(Paragraph("5. GOVERNING LAW", styles["SectionHeader"]))
    story.append(Paragraph(
        "5.1 This Agreement is governed by the laws of the <b>State of Washington</b>, with exclusive venue in the King County Superior Court in Seattle, WA.",
        styles["Body"],
    ))

    doc.build(story)
    print(f"Created: {filename}")


if __name__ == "__main__":
    build_pdf_draft_a(OUT_DIR / "Master_Services_Agreement_2025_Draft_A.pdf")
    build_pdf_revision_b(OUT_DIR / "Master_Services_Agreement_2026_Revision_B.pdf")
    build_pdf_saas_agreement(OUT_DIR / "Software_Licensing_and_SaaS_Agreement_2026.pdf")
