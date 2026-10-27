import os
import json
from collections import defaultdict
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QHBoxLayout,
    QLineEdit, QComboBox, QTabWidget, QWidget, QFrame, QMessageBox,
    QAbstractItemView, QPushButton
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
gle_data = os.path.join(desktop, "GLE_Data")
os.makedirs(gle_data, exist_ok=True)

# ================= ENREGISTREMENT & GESTION DES FICHIERS =================
def enregistrer_vente(nom_client, produits_facture, remise):
    today = datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join(gle_data, today)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, "ventes.json")
    
    ventes = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                ventes = json.load(f)
        except:
            ventes = []

    prodata = []
    for item in produits_facture:
        c, p, q, pr, tot = item[0], item[1], item[2], item[3], item[4]
        prodata.append({
            "categorie": c,
            "produit": p,
            "qte": q,
            "prix": pr,
            "total": tot
        })

    nouvelle_vente = {
        "client": nom_client,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "produits": prodata,
        "remise": remise
    }

    ventes.append(nouvelle_vente)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(ventes, f, indent=4, ensure_ascii=False)
    generer_stats(today)

def supprimer_facture(date, index):
    file_path = os.path.join(gle_data, date, "ventes.json")
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if 0 <= index < len(data):
            del data[index]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            generer_stats(date)
            return True
    except:
        pass
    return False

def modifier_facture(date, index, nouvelle_facture):
    file_path = os.path.join(gle_data, date, "ventes.json")
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if 0 <= index < len(data):
            data[index] = nouvelle_facture
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            generer_stats(date)
            return True
    except:
        pass
    return False

def stats_journalieres(date):
    file_path = os.path.join(gle_data, date, "ventes.json")
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            ventes = json.load(f)
    except:
        return None

    stats = {
        "nbr_clients": len(ventes),
        "total_remise": 0,
        "total_ca": 0,
        "produits_par_categorie": defaultdict(int)
    }

    for vente in ventes:
        stats["total_remise"] += vente.get("remise", 0)
        total_vente = sum(item.get("total", item["qte"] * item["prix"]) for item in vente["produits"])
        stats["total_ca"] += max(total_vente - vente.get("remise", 0), 0)

        for item in vente["produits"]:
            key = (item["categorie"], item["produit"])
            stats["produits_par_categorie"][key] += item["qte"]

    return stats

def generer_stats(date):
    stats = stats_journalieres(date)
    if not stats:
        return
    folder = os.path.join(gle_data, date)
    os.makedirs(folder, exist_ok=True)
    txt_file = os.path.join(folder, "stats_journalieres.txt")

    total_par_categorie = defaultdict(int)
    for (cat, _), qte in stats["produits_par_categorie"].items():
        total_par_categorie[cat] += qte

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(f"Historique du {date}\n\n")
        f.write(f"Nombre de clients : {stats['nbr_clients']}\n")
        f.write(f"Total remise : {stats['total_remise']:.2f} dh\n")
        f.write(f"Total CA (après remise) : {stats['total_ca']:.2f} dh\n\n")
        f.write("Totaux par catégorie :\n")
        for cat, total_qte in total_par_categorie.items():
            f.write(f"- {cat} : {total_qte}\n")


# ================= FENÊTRE DE DÉTAIL D'UN CLIENT =================
class DetailClientDialog(QDialog):
    def __init__(self, nom_client, ventes_client, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Détails des achats : {nom_client}")
        self.resize(750, 450)
        self.setStyleSheet("""
            QDialog { background-color: #f4f6f8; }
            QLabel { color: #333333; font-family: 'Segoe UI', Arial; }
            QTableWidget { background-color: white; border: 1px solid #dcdcdc; border-radius: 6px; }
            QHeaderView::section { background-color: #1f78b4; color: white; padding: 6px; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        lbl_titre = QLabel(f"👤 Historique des transactions pour : <b>{nom_client}</b>")
        lbl_titre.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(lbl_titre)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Heure", "Catégorie", "Produit", "Qté", "Prix U.", "Total (DH)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        lignes = []
        ca_total_client = 0
        for v in ventes_client:
            heure = v.get("date", "").split(" ")[-1]
            for p in v.get("produits", []):
                cat = p.get("categorie", "")
                prod = p.get("produit", "")
                qte = p.get("qte", 0)
                prix = p.get("prix", 0)
                tot = p.get("total", qte * prix)
                ca_total_client += tot
                lignes.append((heure, cat, prod, qte, prix, tot))

        self.table.setRowCount(len(lignes))
        for i, row in enumerate(lignes):
            self.table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.table.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.table.setItem(i, 4, QTableWidgetItem(f"{row[4]:.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{row[5]:.2f}"))

        lbl_total = QLabel(f"💰 <b>Total Général des Achats :</b> {ca_total_client:.2f} DH")
        lbl_total.setFont(QFont("Segoe UI", 11))
        layout.addWidget(lbl_total)


# ================= FENÊTRE GESTION DES FACTURES =================
class GestionFacturesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Factures du Jour")
        self.resize(800, 450)
        self.setStyleSheet("""
            QDialog { background-color: #f4f6f8; }
            QTableWidget { background-color: white; border: 1px solid #dcdcdc; border-radius: 6px; }
            QHeaderView::section { background-color: #e91e63; color: white; padding: 6px; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Factures enregistrées aujourd'hui (Sélectionnez une ligne pour la supprimer) :</b>"))

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Heure", "Client", "Remise (DH)", "Articles"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_supprimer = QPushButton("Supprimer la facture sélectionnée")
        btn_supprimer.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        btn_supprimer.clicked.connect(self.supprimer_selection)
        
        btn_layout.addWidget(btn_supprimer)
        layout.addLayout(btn_layout)

        self.charger_factures()

    def charger_factures(self):
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(gle_data, today, "ventes.json")
        
        if not os.path.exists(file_path):
            self.ventes = []
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.ventes = json.load(f)
            except:
                self.ventes = []

        self.table.setRowCount(len(self.ventes))
        for i, v in enumerate(self.ventes):
            self.table.setItem(i, 0, QTableWidgetItem(v.get("date", "").split(" ")[-1]))
            self.table.setItem(i, 1, QTableWidgetItem(v.get("client", "")))
            self.table.setItem(i, 2, QTableWidgetItem(f"{v.get('remise', 0):.2f}"))
            nb_articles = sum(p.get("qte", 0) for p in v.get("produits", []))
            self.table.setItem(i, 3, QTableWidgetItem(str(nb_articles)))

    def supprimer_selection(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une facture à supprimer.")
            return
        
        reponse = QMessageBox.question(self, "Confirmation", "Voulez-vous vraiment supprimer cette facture ?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reponse == QMessageBox.StandardButton.Yes:
            today = datetime.now().strftime("%Y-%m-%d")
            if supprimer_facture(today, row):
                QMessageBox.information(self, "Succès", "Facture supprimée avec succès.")
                self.charger_factures()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer la facture.")

def gerer_factures(parent=None):
    if isinstance(parent, bool):
        parent = None
        
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(gle_data, today, "ventes.json")
    if not os.path.exists(file_path):
        QMessageBox.information(parent, "Gestion", "Aucune facture enregistrée pour aujourd'hui.")
        return
    dialog = GestionFacturesDialog(parent)
    dialog.exec()


# ================= FENÊTRE DIALOGUE PRO & ANALYTIQUE =================
class HistoriqueProDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tableau de Bord & Analyses Avancées - GLE")
        self.resize(1150, 720)
        self.setStyleSheet("""
            QDialog { background-color: #f4f6f8; }
            QLabel { color: #333333; font-family: 'Segoe UI', Arial; }
            QTableWidget { 
                background-color: white; 
                border: 1px solid #dcdcdc; 
                border-radius: 8px;
                gridline-color: #f1f3f5;
                selection-background-color: #e7f5ff;
                selection-color: #212529;
            }
            QHeaderView::section { 
                background-color: #1f78b4; 
                color: white; 
                padding: 8px; 
                border: none; 
                font-weight: bold;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                padding: 6px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            QTabWidget::pane { border: 1px solid #dcdcdc; background: white; border-radius: 8px; }
            QTabBar::tab { background: #e9ecef; padding: 10px 20px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; color: #495057; margin-right: 2px; }
            QTabBar::tab:selected { background: #1f78b4; color: white; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        titre_layout = QHBoxLayout()
        lbl_titre = QLabel("📊 Tableau de Bord & Statistiques Détaillées")
        lbl_titre.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_titre.setStyleSheet("color: #1f78b4;")
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        lbl_date = QLabel(f"📅 Date : {today_str}")
        lbl_date.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_date.setStyleSheet("color: #6c757d;")
        
        titre_layout.addWidget(lbl_titre)
        titre_layout.addStretch()
        titre_layout.addWidget(lbl_date)
        main_layout.addLayout(titre_layout)

        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        
        self.card_ca = self.creer_carte_kpi("CA Net du Jour", "0.00 DH", "#2b8a3e")
        self.card_remises = self.creer_carte_kpi("Total Remises", "0.00 DH", "#c92a2a")
        self.card_clients = self.creer_carte_kpi("Clients Actifs", "0", "#1c7ed6")
        self.card_articles = self.creer_carte_kpi("Articles Vendus", "0", "#fd7e14")
        
        kpi_layout.addWidget(self.card_ca)
        kpi_layout.addWidget(self.card_remises)
        kpi_layout.addWidget(self.card_clients)
        kpi_layout.addWidget(self.card_articles)
        main_layout.addLayout(kpi_layout)

        self.tabs = QTabWidget()
        
        self.tab_journal = QWidget()
        self.init_onglet_journal()
        self.tabs.addTab(self.tab_journal, "📋 Journal des Ventes")

        self.tab_cat = QWidget()
        self.init_onglet_categories()
        self.tabs.addTab(self.tab_cat, "📁 Totaux par Catégorie")

        self.tab_prod = QWidget()
        self.init_onglet_produits()
        self.tabs.addTab(self.tab_prod, "📦 Ventes par Produit")

        self.tab_client = QWidget()
        self.init_onglet_clients()
        self.tabs.addTab(self.tab_client, "👥 CA par Client (Double-clic pour détails)")

        self.tab_graph = QWidget()
        self.init_onglet_tendances()
        self.tabs.addTab(self.tab_graph, "📈 Résumé & Tendances")

        main_layout.addWidget(self.tabs)

        cumul_group = QGroupBox("📈 Cumuls du Mois en Cours (Selon Séparation)")
        cumul_layout = QHBoxLayout(cumul_group)
        
        self.lbl_cumul_eau = QLabel("💧 CA Mensuel (Eau) : 0.00 DH")
        self.lbl_cumul_eau.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_cumul_eau.setStyleSheet("color: #1f78b4; background: #e7f5ff; padding: 10px; border-radius: 6px;")

        self.lbl_cumul_boisson = QLabel("🥤 CA Mensuel (Boissons Gazeuses) : 0.00 DH")
        self.lbl_cumul_boisson.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_cumul_boisson.setStyleSheet("color: #d9480f; background: #fff4e6; padding: 10px; border-radius: 6px;")

        self.lbl_cumul_total = QLabel("💰 Total CA Mensuel : 0.00 DH")
        self.lbl_cumul_total.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_cumul_total.setStyleSheet("color: #2b8a3e; background: #ebfbee; padding: 10px; border-radius: 6px;")

        cumul_layout.addWidget(self.lbl_cumul_eau)
        cumul_layout.addWidget(self.lbl_cumul_boisson)
        cumul_layout.addWidget(self.lbl_cumul_total)
        
        main_layout.addWidget(cumul_group)

        self.charger_donnees()

    def creer_carte_kpi(self, titre, valeur_defaut, couleur):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: white; border-radius: 8px; border-left: 5px solid {couleur}; border: 1px solid #dcdcdc;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        
        lbl_titre = QLabel(titre.upper())
        lbl_titre.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl_titre.setStyleSheet("color: #868e96; border: none;")
        
        lbl_valeur = QLabel(valeur_defaut)
        lbl_valeur.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_valeur.setStyleSheet(f"color: {couleur}; border: none;")
        lbl_valeur.setObjectName("valeur")
        
        layout.addWidget(lbl_titre)
        layout.addWidget(lbl_valeur)
        return frame

    def mettre_a_jour_carte(self, carte, nouvelle_valeur):
        lbl = carte.findChild(QLabel, "valeur")
        if lbl:
            lbl.setText(nouvelle_valeur)

    def init_onglet_journal(self):
        layout = QVBoxLayout(self.tab_journal)
        filtre_layout = QHBoxLayout()
        self.input_recherche = QLineEdit()
        self.input_recherche.setPlaceholderText("🔍 Filtrer par client ou produit...")
        self.input_recherche.textChanged.connect(self.filtrer_journal)
        
        self.combo_cat = QComboBox()
        self.combo_cat.addItem("Toutes les catégories")
        self.combo_cat.currentIndexChanged.connect(self.filtrer_journal)

        filtre_layout.addWidget(self.input_recherche, 2)
        filtre_layout.addWidget(QLabel("Catégorie :"))
        filtre_layout.addWidget(self.combo_cat, 1)
        layout.addLayout(filtre_layout)

        self.table_journal = QTableWidget()
        self.table_journal.setColumnCount(7)
        self.table_journal.setHorizontalHeaderLabels(["Heure", "Client", "Catégorie", "Produit", "Qté", "Prix U.", "Total Ligne"])
        self.table_journal.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_journal)

    def init_onglet_categories(self):
        layout = QVBoxLayout(self.tab_cat)
        self.table_cat = QTableWidget()
        self.table_cat.setColumnCount(4)
        self.table_cat.setHorizontalHeaderLabels(["Catégorie", "Quantité Totale Vendue", "CA Brut (DH)", "Part du CA (%)"])
        self.table_cat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_cat)

    def init_onglet_produits(self):
        layout = QVBoxLayout(self.tab_prod)
        self.table_prod = QTableWidget()
        self.table_prod.setColumnCount(5)
        self.table_prod.setHorizontalHeaderLabels(["Produit", "Catégorie", "Quantité Vendue", "Prix Moyen", "CA Total (DH)"])
        self.table_prod.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_prod)

    def init_onglet_clients(self):
        layout = QVBoxLayout(self.tab_client)
        self.table_client = QTableWidget()
        self.table_client.setColumnCount(2)
        self.table_client.setHorizontalHeaderLabels(["Client", "Total Net (DH)"])
        self.table_client.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_client.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_client.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_client.doubleClicked.connect(self.ouvrir_detail_client)
        layout.addWidget(QLabel("<i>💡 Double-cliquez sur un client pour voir le détail de ses achats du jour.</i>"))
        layout.addWidget(self.table_client)

    def init_onglet_tendances(self):
        layout = QVBoxLayout(self.tab_graph)
        self.lbl_tendances = QLabel("Analyse des performances en cours...")
        self.lbl_tendances.setFont(QFont("Segoe UI", 12))
        self.lbl_tendances.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.lbl_tendances)

    def charger_donnees(self):
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(gle_data, today, "ventes.json")
        
        if not os.path.exists(file_path):
            self.ventes_du_jour = []
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.ventes_du_jour = json.load(f)
        except:
            self.ventes_du_jour = []

        self.toutes_les_lignes = []
        clients_dict = {}
        categories_dict = {}
        produits_dict = {}
        
        total_remises_jour = 0
        total_ca_brut = 0
        total_articles = 0
        categories_set = set()

        for v in self.ventes_du_jour:
            client = v.get("client", "Inconnu").strip()
            date_str = v.get("date", "")
            heure = date_str.split(" ")[-1] if " " in date_str else date_str
            remise = v.get("remise", 0)
            total_remises_jour += remise

            if client not in clients_dict:
                clients_dict[client] = 0

            ca_facture = 0
            prods = v.get("produits", [])
            for p in prods:
                cat = p.get("categorie", "Autre")
                prod = p.get("produit", "")
                qte = p.get("qte", 0)
                prix = p.get("prix", 0)
                tot_ligne = p.get("total", qte * prix)
                
                ca_facture += tot_ligne
                total_ca_brut += tot_ligne
                total_articles += qte
                categories_set.add(cat)

                self.toutes_les_lignes.append((heure, client, cat, prod, qte, prix, tot_ligne))

                if cat not in categories_dict:
                    categories_dict[cat] = {"qte": 0, "ca": 0}
                categories_dict[cat]["qte"] += qte
                categories_dict[cat]["ca"] += tot_ligne

                if prod not in produits_dict:
                    produits_dict[prod] = {"cat": cat, "qte": 0, "prix": prix, "ca": 0}
                produits_dict[prod]["qte"] += qte
                produits_dict[prod]["ca"] += tot_ligne

            clients_dict[client] += max(ca_facture - remise, 0)

        self.combo_cat.blockSignals(True)
        self.combo_cat.clear()
        self.combo_cat.addItem("Toutes les catégories")
        for c in sorted(categories_set):
            self.combo_cat.addItem(c)
        self.combo_cat.blockSignals(False)

        net_jour = max(total_ca_brut - total_remises_jour, 0)
        
        self.mettre_a_jour_carte(self.card_ca, f"{net_jour:.2f} DH")
        self.mettre_a_jour_carte(self.card_remises, f"{total_remises_jour:.2f} DH")
        self.mettre_a_jour_carte(self.card_clients, str(len(clients_dict)))
        self.mettre_a_jour_carte(self.card_articles, str(total_articles))

        self.afficher_journal(self.toutes_les_lignes)

        self.table_cat.setRowCount(len(categories_dict))
        for i, (cat, data) in enumerate(categories_dict.items()):
            part = (data["ca"] / total_ca_brut * 100) if total_ca_brut > 0 else 0
            self.table_cat.setItem(i, 0, QTableWidgetItem(cat))
            self.table_cat.setItem(i, 1, QTableWidgetItem(str(data["qte"])))
            self.table_cat.setItem(i, 2, QTableWidgetItem(f"{data['ca']:.2f}"))
            self.table_cat.setItem(i, 3, QTableWidgetItem(f"{part:.1f}%"))

        self.table_prod.setRowCount(len(produits_dict))
        for i, (prod, data) in enumerate(produits_dict.items()):
            self.table_prod.setItem(i, 0, QTableWidgetItem(prod))
            self.table_prod.setItem(i, 1, QTableWidgetItem(data["cat"]))
            self.table_prod.setItem(i, 2, QTableWidgetItem(str(data["qte"])))
            self.table_prod.setItem(i, 3, QTableWidgetItem(f"{data['prix']:.2f}"))
            self.table_prod.setItem(i, 4, QTableWidgetItem(f"{data['ca']:.2f}"))

        self.table_client.setRowCount(len(clients_dict))
        for i, (cl, total_client) in enumerate(clients_dict.items()):
            self.table_client.setItem(i, 0, QTableWidgetItem(cl))
            item_tot = QTableWidgetItem(f"{total_client:.2f}")
            item_tot.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_client.setItem(i, 1, item_tot)

        texte_tendances = "<h3>📈 Résumé & Répartition du Chiffre d'Affaires</h3><ul>"
        for cat, data in categories_dict.items():
            texte_tendances += f"<li><b>{cat}</b> : {data['qte']} articles vendus pour un CA de <b>{data['ca']:.2f} DH</b></li>"
        texte_tendances += f"</ul><br><b>Total Articles Vendus :</b> {total_articles} unités"
        self.lbl_tendances.setText(texte_tendances)

        ca_eau_mois, ca_boisson_mois = self.calculer_cumuls_mensuels_separation()
        total_mois = ca_eau_mois + ca_boisson_mois

        self.lbl_cumul_eau.setText(f"💧 CA Mensuel (Eau) : {ca_eau_mois:.2f} DH")
        self.lbl_cumul_boisson.setText(f"🥤 CA Mensuel (Boissons Gazeuses) : {ca_boisson_mois:.2f} DH")
        self.lbl_cumul_total.setText(f"💰 Total CA Mensuel : {total_mois:.2f} DH")

    def afficher_journal(self, lignes):
        self.table_journal.setRowCount(len(lignes))
        for i, row in enumerate(lignes):
            self.table_journal.setItem(i, 0, QTableWidgetItem(row[0]))
            self.table_journal.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table_journal.setItem(i, 2, QTableWidgetItem(row[2]))
            self.table_journal.setItem(i, 3, QTableWidgetItem(row[3]))
            self.table_journal.setItem(i, 4, QTableWidgetItem(str(row[4])))
            self.table_journal.setItem(i, 5, QTableWidgetItem(f"{row[5]:.2f}"))
            self.table_journal.setItem(i, 6, QTableWidgetItem(f"{row[6]:.2f}"))

    def filtrer_journal(self):
        texte = self.input_recherche.text().strip().lower()
        cat_sel = self.combo_cat.currentText()

        lignes_filtrees = []
        for r in self.toutes_les_lignes:
            heure, client, cat, prod, qte, prix, tot = r
            match_texte = (texte in client.lower()) or (texte in prod.lower())
            match_cat = (cat_sel == "Toutes les catégories") or (cat == cat_sel)
            if match_texte and match_cat:
                lignes_filtrees.append(r)

        self.afficher_journal(lignes_filtrees)

    def ouvrir_detail_client(self, index):
        row = index.row()
        nom_client = self.table_client.item(row, 0).text()
        ventes_client = [v for v in self.ventes_du_jour if v.get("client", "").strip() == nom_client]
        dialog = DetailClientDialog(nom_client, ventes_client, self)
        dialog.exec()

    def calculer_cumuls_mensuels_separation(self):
        ca_eau = 0.0
        ca_boisson = 0.0
        current_year_month = datetime.now().strftime("%Y-%m")
        
        # Charger les métadonnées de séparation configurées pour les produits
        prices_file = os.path.join(gle_data, "prices.json")
        produits_separes_set = set()
        if os.path.exists(prices_file):
            try:
                with open(prices_file, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    for cat, items in saved_data.items():
                        for prod, val in items.items():
                            if isinstance(val, dict) and val.get("separe", False):
                                produits_separes_set.add(prod.strip().lower())
            except:
                pass

        if os.path.exists(gle_data):
            for dossier_date in os.listdir(gle_data):
                if dossier_date.startswith(current_year_month):
                    ventes_file = os.path.join(gle_data, dossier_date, "ventes.json")
                    if os.path.exists(ventes_file):
                        try:
                            with open(ventes_file, "r", encoding="utf-8") as f:
                                ventes = json.load(f)
                                for v in ventes:
                                    prods = v.get('produits', [])
                                    for p in prods:
                                        prod_name = p.get('produit', '').strip().lower()
                                        tot = p.get('total', p.get('qte', 0) * p.get('prix', 0))
                                        
                                        # Si le produit fait partie de la séparation (boissons gazeuses par ex.), va dans boisson, sinon dans eau
                                        if prod_name in produits_separes_set:
                                            ca_boisson += tot
                                        else:
                                            ca_eau += tot
                        except:
                            pass
        return ca_eau, ca_boisson

def afficher_historique(parent=None):
    if isinstance(parent, bool):
        parent = None
        
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(gle_data, today, "ventes.json")
    
    if not os.path.exists(file_path):
        QMessageBox.information(parent, "Historique", "Aucune vente enregistrée pour aujourd'hui.")
        return
        
    dialog = HistoriqueProDialog(parent)
    dialog.exec()