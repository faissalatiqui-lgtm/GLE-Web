import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from num2words import num2words
import qrcode
from datetime import datetime

def creer_facture_pdf(filename, produits_standards, produits_separes, total_final, remise, nom_client, cumul_mensuel, logo_path, cadeaux_texte=""):
    try:
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # En-tête / Logo (si présent)
        if logo_path and os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=4*cm, height=2*cm)
                story.append(img)
            except Exception:
                pass
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f78b4'),
            spaceAfter=10
        )
        story.append(Paragraph("<b>GLE DISTRIBUTION - FACTURE</b>", title_style))
        story.append(Spacer(1, 0.5 * cm))
        
        # Infos client et date
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_text = f"<b>Client :</b> {nom_client}<br/><b>Date :</b> {date_str}"
        story.append(Paragraph(client_text, styles['Normal']))
        story.append(Spacer(1, 0.5 * cm))
        
        # Tableau des produits
        data = [["Catégorie", "Produit", "Qté", "Prix U.", "Total"]]
        
        tous_produits = []
        if produits_standards:
            tous_produits.extend(produits_standards)
        if produits_separes:
            tous_produits.extend(produits_separes)
            
        for p in tous_produits:
            cat = str(p[0]) if len(p) > 0 else ""
            prod = str(p[1]) if len(p) > 1 else ""
            qte = str(p[2]) if len(p) > 2 else "0"
            prix = f"{float(p[3]):.2f} DH" if len(p) > 3 and isinstance(p[3], (int, float)) else "0.00 DH"
            total = f"{float(p[4]):.2f} DH" if len(p) > 4 and isinstance(p[4], (int, float)) else "0.00 DH"
            data.append([cat, prod, qte, prix, total])
            
        t = Table(data, colWidths=[3.5*cm, 5*cm, 2*cm, 3*cm, 3.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f78b4')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5 * cm))
        
        # Totaux
        remise_val = float(remise) if remise else 0.0
        total_val = float(total_final) if total_final else 0.0
        totaux_text = f"<b>Remise :</b> {remise_val:.2f} DH<br/><b>Total Net à Payer :</b> {total_val:.2f} DH"
        story.append(Paragraph(totaux_text, styles['Normal']))
        
        if cadeaux_texte:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(f"<b>Cadeaux :</b><br/>{str(cadeaux_texte).replace(chr(10), '<br/>')}", styles['Normal']))
            
        doc.build(story)
        return True
    except Exception as e:
        print(f"Erreur PDF : {e}")
        raise e