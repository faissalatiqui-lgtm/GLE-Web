from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from datetime import datetime
from num2words import num2words
import subprocess
import os
import json
import qrcode

FACTURE_FILE = "facture_counter.json"

def get_numero_facture():
    if not os.path.exists(FACTURE_FILE):
        data = {"numero": 1}
    else:
        with open(FACTURE_FILE, "r") as f:
            data = json.load(f)
    numero = data["numero"]
    data["numero"] += 1
    with open(FACTURE_FILE, "w") as f:
        json.dump(data, f)
    return f"{numero:04d}"

def imprimer_pdf(filename):
    try:
        if not os.path.exists(filename):
            return
        sumatra = r"C:\Users\bismaili_ext\AppData\Local\SumatraPDF\SumatraPDF.exe"
        if not os.path.exists(sumatra):
            return
        subprocess.run([sumatra, "-print-to-default", "-silent", "-exit-on-print", filename])
    except Exception as e:
        print("❌ Erreur impression :", e)

def creer_facture_pdf(filename, produits_standards, produits_separes, total_final, remise, nom_client, cumul_mensuel, logo_path=None, cadeaux_texte=""):
    numero = get_numero_facture()
    c = canvas.Canvas(filename, pagesize=A5)
    width, height = A5

    margin = 25
    y = height - 30

    if logo_path and os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            c.drawImage(logo, margin, y - 35, width=70, height=30, preserveAspectRatio=True, mask='auto')
        except:
            pass

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1f78b4"))
    c.drawRightString(width - margin, y - 10, "GLE DISTRIBUTION")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawRightString(width - margin, y - 22, "Facturation & Logistique")

    y -= 45
    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.setLineWidth(1)
    c.line(margin, y, width - margin, y)

    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(margin, y, f"Client : {nom_client}")
    c.drawRightString(width - margin, y, f"Facture N° : {numero}")

    y -= 15
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#333333"))
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.drawString(margin, y, f"Date : {date_str}")
    c.drawRightString(width - margin, y, f"Cumul mois : {cumul_mensuel:.2f} DH")

    y -= 15

    def dessiner_groupe(titre_groupe, liste_prods):
        nonlocal y
        if not liste_prods:
            return 0, 0

        y -= 10
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#1f78b4"))
        c.drawString(margin, y, titre_groupe)
        y -= 14

        c.setFillColor(colors.HexColor("#f0f0f0"))
        c.rect(margin, y - 3, width - (2 * margin), 14, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin + 5, y, "Produit")
        c.drawString(margin + 175, y, "Qté")
        c.drawString(margin + 215, y, "P.U")
        c.drawRightString(width - margin - 5, y, "Total")

        y -= 14
        sous_total_montant = 0
        sous_total_qte = 0

        for cat, prod, qte, prix, tot in liste_prods:
            if y < 90:
                c.showPage()
                y = height - 40

            c.setFont("Helvetica", 9)
            c.drawString(margin + 5, y, prod[:28])
            c.drawString(margin + 175, y, str(qte))
            c.drawString(margin + 215, y, f"{prix:.2f}")
            c.drawRightString(width - margin - 5, y, f"{tot:.2f}")

            sous_total_montant += tot
            sous_total_qte += qte

            y -= 4
            c.setStrokeColor(colors.HexColor("#e0e0e0"))
            c.setLineWidth(0.5)
            c.line(margin, y, width - margin, y)
            y -= 12

        y -= 2
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.HexColor("#444444"))
        c.drawString(margin + 5, y, f"Sous-total {titre_groupe} :")
        c.drawString(margin + 170, y, f"Qté: {sous_total_qte}")
        c.drawRightString(width - margin - 5, y, f"{sous_total_montant:.2f} DH")
        y -= 15
        return sous_total_montant, sous_total_qte

    montant_std, qte_std = dessiner_groupe("Eau", produits_standards)
    montant_sep, qte_sep = dessiner_groupe("Boissons Gazeuses", produits_separes)

    montant_total = montant_std + montant_sep
    total_qte_global = qte_std + qte_sep
    net = max(montant_total - remise, 0)

    # ================= BLOC CADEAUX SPÉCIAUX =================
    if cadeaux_texte.strip():
        if y < 90:
            c.showPage()
            y = height - 40
        y -= 5
        lignes_cadeaux = cadeaux_texte.split("\n")
        hauteur_bloc = len(lignes_cadeaux) * 14 + 10
        
        c.setFillColor(colors.HexColor("#fff3cd"))
        c.setStrokeColor(colors.HexColor("#ffeeba"))
        c.rect(margin, y - hauteur_bloc, width - (2 * margin), hauteur_bloc, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor("#856404"))
        c.setFont("Helvetica-Bold", 9)
        
        y_cad = y - 12
        for ligne in lignes_cadeaux:
            if ligne.strip():
                c.drawCentredString(width / 2, y_cad, f"🎁 {ligne.strip()}")
                y_cad -= 14
        y -= (hauteur_bloc + 8)

    # ================= BLOC TOTAUX GLOBAUX =================
    if y < 110:
        c.showPage()
        y = height - 40

    c.setStrokeColor(colors.HexColor("#1f78b4"))
    c.setLineWidth(1)
    c.rect(width - 185, y - 60, 160, 55, fill=0, stroke=1)

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(width - 175, y - 10, f"Qté Totale :")
    c.drawRightString(width - margin - 5, y - 10, f"{total_qte_global}")

    c.drawString(width - 175, y - 22, f"Total Brut :")
    c.drawRightString(width - margin - 5, y - 22, f"{montant_total:.2f} DH")

    if remise > 0:
        c.drawString(width - 175, y - 34, f"Remise :")
        c.drawRightString(width - margin - 5, y - 34, f"- {remise:.2f} DH")
        y_net = y - 48
    else:
        y_net = y - 36

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1f78b4"))
    c.drawString(width - 175, y_net, "NET À PAYER :")
    c.drawRightString(width - margin - 5, y_net, f"{net:.2f} DH")

    # ================= MONTANT EN LETTRES =================
    y -= 70
    try:
        lettres = num2words(net, lang="fr").capitalize() + " dirhams"
    except:
        lettres = ""

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(margin, y, f"Arrêtée la présente facture à la somme de : {lettres}")

    # ================= PIED DE PAGE & QR CODE =================
    y -= 22
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, y, f"Merci de votre confiance, {nom_client} !")

    y -= 10
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#777777"))
    c.drawCentredString(width / 2, y, "GLE DISTRIBUTION - Soutient les Lions de l'Atlas")

    qr_text = f"Facture N°{numero} | {nom_client} | Net: {net:.2f} DH | Cumul: {cumul_mensuel:.2f}"
    qr = qrcode.make(qr_text)
    qr_path = "qr_tmp.png"
    qr.save(qr_path)

    c.drawImage(ImageReader(qr_path), width - margin - 40, 5, width=40, height=40)

    if os.path.exists(qr_path):
        os.remove(qr_path)

    c.save()
    imprimer_pdf(filename)