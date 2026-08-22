from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

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
    details = f"Area: {area} sqft<br/>Floors: {floors}<br/>Tier: {tier}<br/>Grade: {grade}<br/>Total Estimated Cost: ?{estimated_cost:,.2f}"
    elements.append(Paragraph(details, normal_style))
    elements.append(Spacer(1, 24))
    
    # Quantities Table
    data = [
        ["Material/Item", "Quantity", "Unit"],
        ["Concrete Volume", f"{quantities['concrete_cum']}", "Cubic Meters"],
        ["Steel Weight", f"{quantities['steel_kg']}", "Kg"],
        ["Bricks", f"{quantities['bricks']}", "Pieces"],
        ["Dry Mortar", f"{quantities['dry_mortar_cum']}", "Cubic Meters"]
    ]
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(t)
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer
