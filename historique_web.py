import os
import json
from datetime import datetime

# Dossier de données isolé
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
gle_data = os.path.join(desktop, "GLE_Data")
os.makedirs(gle_data, exist_ok=True)

def enregistrer_vente(nom_client, quantites_saisies, remise):
    today = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(gle_data, today)
    os.makedirs(folder, exist_ok=True)
    ventes_file = os.path.join(folder, "ventes.json")
    
    ventes = []
    if os.path.exists(ventes_file):
        try:
            with open(ventes_file, "r", encoding="utf-8") as f:
                ventes = json.load(f)
        except:
            pass
            
    produits_details = []
    for item in quantites_saisies:
        # item format : (cat, prod, qte, prix, total)
        produits_details.append({
            "categorie": item[0],
            "produit": item[1],
            "qte": item[2],
            "prix": item[3],
            "total": item[4]
        })
        
    vente_data = {
        "client": nom_client,
        "date": datetime.now().strftime("%H:%M:%S"),
        "remise": remise,
        "produits": produits_details
    }
    
    ventes.append(vente_data)
    with open(ventes_file, "w", encoding="utf-8") as f:
        json.dump(ventes, f, indent=4, ensure_ascii=False)

def stats_journalieres():
    today = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(gle_data, today)
    ventes_file = os.path.join(folder, "ventes.json")
    if os.path.exists(ventes_file):
        try:
            with open(ventes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []