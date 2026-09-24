import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_boq_pdf(area, floors, tier, grade, quantities, estimated_cost):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # Title
    elements.append(Paragraph("BuildMetrics AI - Bill of Quantities (BOQ)", title_style))
    elements.append(Spacer(1, 12))
    
    # Project Details
    details = f"Area: {area} sqft<br/>Floors: {floors}<br/>Tier: {tier}<br/>Grade: {grade}<br/>Estimated Duration: {quantities['estimated_days']} Days<br/>Total Estimated Cost: Rs {estimated_cost:,.2f}"
    elements.append(Paragraph(details, normal_style))
    elements.append(Spacer(1, 24))
    
    # Quantities Table
    data = [
        ["Material/Resource", "Quantity", "Unit"],
        ["Concrete Volume", f"{quantities['concrete_cum']}", "Cubic Meters"],
        ["Steel Weight", f"{quantities['steel_kg']}", "Kg"],
        ["Bricks", f"{quantities['bricks']}", "Pieces"],
        ["Dry Mortar", f"{quantities['dry_mortar_cum']}", "Cubic Meters"],
        ["Labor Required", f"{quantities['total_mandays']}", "Man-Days"]
    ]
    
    t = Table(data, colWidths=[150, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(t)
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer
