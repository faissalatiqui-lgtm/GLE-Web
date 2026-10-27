import streamlit as st
import os
import json
from datetime import datetime

# Importation des modules existants
from produits import produits
from facture_pdf import creer_facture_pdf
from historique_web import gle_data, enregistrer_vente, stats_journalieres

# Configuration de la page
st.set_page_config(page_title="GLE Distribution - Facturation", page_icon="💧", layout="wide")

# Design CSS
st.markdown("""
    <style>
    .stButton>button {
        border-radius: 10px;
        font-weight: bold;
        color: white;
        border: 2px solid #333;
        width: 100%;
        padding: 10px;
        font-size: 14px;
    }
    div.stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #dcdcdc;
    }
    </style>
""", unsafe_allow_html=True)

# Dossiers et fichiers de configuration
prices_file = os.path.join(gle_data, "prices.json")
rules_file = os.path.join(gle_data, "gift_rules.json")
config_file = os.path.join(gle_data, "config.json")

# Gestion du mot de passe Admin
def get_password_admin():
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("admin_password", "villa2000")
        except:
            pass
    return "villa2000"

def set_password_admin(new_pass):
    cfg = {"admin_password": new_pass}
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

# Chargement des prix et métadonnées
active_produits = produits.copy()
product_meta = {}
if os.path.exists(prices_file):
    try:
        with open(prices_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        for cat, items in saved_data.items():
            if cat not in active_produits:
                active_produits[cat] = {}
            for prod, val in items.items():
                if isinstance(val, dict):
                    active_produits[cat][prod] = val.get("prix", 0)
                    product_meta[(cat, prod)] = val
                else:
                    active_produits[cat][prod] = val
                    product_meta[(cat, prod)] = {"prix": val, "separe": False}
    except:
        pass

# Chargement des règles de cadeaux
regles_cadeaux = [{"eau": 10, "boisson": 40, "global": 0, "cadeau": "1 Pack Acyl 1.5L"}]
if os.path.exists(rules_file):
    try:
        with open(rules_file, "r", encoding="utf-8") as f:
            regles_cadeaux = json.load(f)
    except:
        pass

def sauvegarder_regles(nouvelles_regles):
    global regles_cadeaux
    regles_cadeaux = nouvelles_regles
    with open(rules_file, "w", encoding="utf-8") as f:
        json.dump(regles_cadeaux, f, indent=4, ensure_ascii=False)

# --- EN-TÊTE ---
col_logo, col_titre = st.columns([1, 4])
with col_logo:
    logo_path = "logo_glc.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=220)
    else:
        st.markdown("### **GLE DISTRIBUTION**")
with col_titre:
    st.title("💧 GLE Distribution - Facturation & Admin (Mobile)")

# --- BARRE LATÉRALE : CLIENT & REMISES ---
st.sidebar.markdown("### 👤 Paramètres de Vente")
nom_client = st.sidebar.text_input("Nom du client :")

st.sidebar.markdown("### 🎁 Gestion des Remises")
mode_remise = st.sidebar.radio("Mode de Remise", ["Aucune", "5 DH / u", "Remise Totale"])
valeur_remise_perso = 0.0
if mode_remise == "Remise Totale":
    valeur_remise_perso = st.sidebar.number_input("Montant total de la remise (DH)", min_value=0.0, step=1.0)

# --- ESPACE ADMINISTRATEUR SÉCURISÉ ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔐 Espace Administrateur")
admin_expander = st.sidebar.expander("Ouvrir le Menu Admin 🔒")

admin_connecte = False
with admin_expander:
    mdp_saisi = st.text_input("Mot de passe admin", type="password", key="pwd_admin_input")
    if mdp_saisi == get_password_admin():
        admin_connecte = True
        st.success("Accès Admin Autorisé ✅")
    elif mdp_saisi:
        st.error("Mot de passe incorrect")

# --- INTERFACE PRINCIPALE (ONGLETS : Facturation / Admin & Cadeaux / Historique) ---
onglet_principal, onglet_admin_gestion, onglet_historique = st.tabs([
    "🛒 Facturation", 
    "⚙️ Gestion Admin (Prix, Séparation, Cadeaux)", 
    "📊 Historique & Factures du Jour"
])

# ================= ONGLET 1 : FACTURATION =================
with onglet_principal:
    quantites_saisies = []
    total_qte = 0
    total_brut = 0
    qte_eau = 0
    qte_boisson = 0

    categories_list = list(active_produits.keys())
    tabs_prod = st.tabs(categories_list)

    for i, cat in enumerate(categories_list):
        with tabs_prod[i]:
            items = active_produits[cat]
            cols = st.columns(3)
            idx = 0
            for prod, prix in items.items():
                meta = product_meta.get((cat, prod), {"separe": False})
                is_separe = meta.get("separe", False)
                display_name = f"💧 {prod}" if is_separe else prod
                
                with cols[idx % 3]:
                    qte = st.number_input(f"{display_name} ({prix:.2f} DH)", min_value=0, step=1, key=f"qte_{cat}_{prod}")
                    if qte > 0:
                        tot_ligne = qte * prix
                        quantites_saisies.append((cat, prod, qte, prix, tot_ligne))
                        total_qte += qte
                        total_brut += tot_ligne
                        if is_separe:
                            qte_boisson += qte
                        else:
                            qte_eau += qte
                idx += 1

    # Calcul des remises
    if mode_remise == "5 DH / u":
        current_remise = 5.0 * total_qte
    elif mode_remise == "Remise Totale":
        current_remise = valeur_remise_perso
    else:
        current_remise = 0.0

    total_final = max(total_brut - current_remise, 0)

    # Calcul automatique des cadeaux
    cadeaux_actifs_texte = ""
    resultats_cadeaux = []
    qte_globale = qte_eau + qte_boisson
    for regle in regles_cadeaux:
        req_eau = regle.get("eau", 0)
        req_boisson = regle.get("boisson", 0)
        req_global = regle.get("global", 0)
        nom_c = regle.get("cadeau", "")
        
        mults = []
        if req_eau > 0: mults.append(qte_eau // req_eau)
        if req_boisson > 0: mults.append(qte_boisson // req_boisson)
        if req_global > 0: mults.append(qte_globale // req_global)
        
        if mults:
            multiplicateur = min(mults)
            if multiplicateur > 0:
                resultats_cadeaux.append(f"{multiplicateur} x {nom_c} Gratuit !")

    if resultats_cadeaux:
        cadeaux_actifs_texte = "\n".join(resultats_cadeaux)
        st.info(f"🎁 **Cadeaux Appliqués :**\n{cadeaux_actifs_texte}")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Qté Totale", total_qte)
    c2.metric("Remise", f"{current_remise:.2f} DH")
    c3.metric("Total Net", f"{total_final:.2f} DH", delta=f"Brut : {total_brut:.2f}")

    st.markdown("---")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Initialiser", type="secondary"):
            st.rerun()

    with col_btn2:
        if st.button("🖨️ Imprimer PDF & Enregistrer", type="primary"):
            if not nom_client.strip():
                st.error("Veuillez entrer le nom du client dans la barre latérale.")
            elif not quantites_saisies:
                st.error("Veuillez sélectionner au moins un produit.")
            else:
                try:
                    produits_standards = [p for p in quantites_saisies if not product_meta.get((p[0], p[1]), {}).get("separe", False)]
                    produits_separes = [p for p in quantites_saisies if product_meta.get((p[0], p[1]), {}).get("separe", False)]
                    
                    today = datetime.now().strftime("%Y-%m-%d")
                    folder = os.path.join(gle_data, today)
                    os.makedirs(folder, exist_ok=True)
                    now_time = datetime.now().strftime("%H%M%S")
                    filename = os.path.join(folder, f"Facture_{nom_client.strip()}_{now_time}.pdf")
                    
                    creer_facture_pdf(filename, produits_standards, produits_separes, total_final, current_remise, nom_client.strip(), total_final, "logo_glc.png", cadeaux_texte=cadeaux_actifs_texte)
                    enregistrer_vente(nom_client.strip(), quantites_saisies, current_remise)
                    
                    st.success(f"✅ Facture générée et enregistrée pour **{nom_client.strip()}** !")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")

# ================= ONGLET 2 : GESTION ADMIN =================
with onglet_admin_gestion:
    st.subheader("⚙️ Paramétrage Administrateur")
    if not admin_connecte:
        st.warning("🔒 Veuillez entrer le mot de passe administrateur correct dans la barre latérale pour accéder à ces options.")
    else:
        st.success("Accès Administrateur Déverrouillé ✅")
        
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "💰 Modifier Prix", 
            "💧 Gérer Séparation", 
            "🎁 Gérer Cadeaux", 
            "🔑 Mot de Passe"
        ])
        
        with admin_tab1:
            st.markdown("### Modification des Prix")
            prod_list = [f"{c} -> {p}" for c, items in active_produits.items() for p in items.keys()]
            sel_prod = st.selectbox("Sélectionner un produit", prod_list)
            if sel_prod:
                c_sel, p_sel = sel_prod.split(" -> ")
                old_p = active_produits[c_sel][p_sel]
                new_p = st.number_input("Nouveau prix (DH)", value=float(old_p), min_value=0.0, step=0.5, key="num_prix_admin")
                if st.button("💾 Enregistrer le nouveau prix"):
                    active_produits[c_sel][p_sel] = new_p
                    saved_data = {}
                    for c_key, items_dict in active_produits.items():
                        if c_key not in saved_data: saved_data[c_key] = {}
                        for p_key, p_val in items_dict.items():
                            sep = product_meta.get((c_key, p_key), {}).get("separe", False)
                            saved_data[c_key][p_key] = {"prix": p_val, "separe": sep}
                    with open(prices_file, "w", encoding="utf-8") as f:
                        json.dump(saved_data, f, indent=4, ensure_ascii=False)
                    st.success("Prix mis à jour avec succès !")
                    st.rerun()

        with admin_tab2:
            st.markdown("### Gestion de la Séparation (Eau / Boissons Gazeuses)")
            sel_prod_sep = st.selectbox("Sélectionner un produit", prod_list, key="sel_sep_admin")
            if sel_prod_sep:
                c_s, p_s = sel_prod_sep.split(" -> ")
                current_sep = product_meta.get((c_s, p_s), {}).get("separe", False)
                new_sep = st.checkbox("Marquer comme séparé (Boisson Gazeuse 💧)", value=current_sep)
                if st.button("💾 Enregistrer la séparation"):
                    if (c_s, p_s) not in product_meta: product_meta[(c_s, p_s)] = {"prix": active_produits[c_s][p_s]}
                    product_meta[(c_s, p_s)]["separe"] = new_sep
                    
                    saved_data = {}
                    for c_key, items_dict in active_produits.items():
                        if c_key not in saved_data: saved_data[c_key] = {}
                        for p_key, p_val in items_dict.items():
                            sep = product_meta.get((c_key, p_key), {}).get("separe", False)
                            saved_data[c_key][p_key] = {"prix": p_val, "separe": sep}
                    with open(prices_file, "w", encoding="utf-8") as f:
                        json.dump(saved_data, f, indent=4, ensure_ascii=False)
                    st.success("Séparation mise à jour !")
                    st.rerun()

        with admin_tab3:
            st.markdown("### Gestion des Règles de Cadeaux")
            st.info("Configurez les seuils pour l'attribution automatique des cadeaux.")
            
            nouvelles_regles = []
            for idx_r, regle in enumerate(regles_cadeaux):
                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                with col_r1:
                    e_val = st.number_input(f"Eau (Règle {idx_r+1})", min_value=0, value=int(regle.get("eau", 0)), key=f"r_eau_{idx_r}")
                with col_r2:
                    b_val = st.number_input(f"Boisson (Règle {idx_r+1})", min_value=0, value=int(regle.get("boisson", 0)), key=f"r_bois_{idx_r}")
                with col_r3:
                    g_val = st.number_input(f"Global (Règle {idx_r+1})", min_value=0, value=int(regle.get("global", 0)), key=f"r_glob_{idx_r}")
                with col_r4:
                    c_val = st.text_input(f"Nom Cadeau {idx_r+1}", value=regle.get("cadeau", ""), key=f"r_cad_{idx_r}")
                
                if c_val.strip():
                    nouvelles_regles.append({"eau": e_val, "boisson": b_val, "global": g_val, "cadeau": c_val.strip()})
                st.markdown("---")

            if st.button("💾 Enregistrer les Règles de Cadeaux"):
                sauvegarder_regles(nouvelles_regles)
                st.success("Règles de cadeaux mises à jour avec succès !")
                st.rerun()

        with admin_tab4:
            st.markdown("### Modification du Mot de Passe Admin")
            new_m = st.text_input("Nouveau mot de passe admin", type="password", key="new_pwd_input")
            if st.button("🔑 Mettre à jour le mot de passe"):
                if new_m.strip():
                    set_password_admin(new_m.strip())
                    st.success("Mot de passe administrateur modifié avec succès !")

# ================= ONGLET 3 : HISTORIQUE & FACTURES =================
with onglet_historique:
    st.subheader("📊 Historique des Ventes du Jour")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    folder_jour = os.path.join(gle_data, today_str)
    ventes_file = os.path.join(folder_jour, "ventes.json")
    
    if not os.path.exists(ventes_file):
        st.info("Aucune vente enregistrée pour aujourd'hui.")
    else:
        try:
            with open(ventes_file, "r", encoding="utf-8") as f:
                ventes_jour = json.load(f)
            
            st.write(f"**Nombre total de factures aujourd'hui :** {len(ventes_jour)}")
            
            for i, v in enumerate(ventes_jour):
                with st.expander(f"Facture #{i+1} — Client : **{v.get('client')}** ({v.get('date')})"):
                    st.write(f"**Remise :** {v.get('remise', 0):.2f} DH")
                    st.markdown("**Produits achetés :**")
                    for p in v.get("produits", []):
                        st.text(f"- [{p.get('categorie')}] {p.get('produit')} : {p.get('qte')} x {p.get('prix')} DH = {p.get('total')} DH")
                    
                    if st.button(f"🗑️ Supprimer cette facture (#{i+1})", key=f"suppr_{i}"):
                        del ventes_jour[i]
                        with open(ventes_file, "w", encoding="utf-8") as f:
                            json.dump(ventes_jour, f, indent=4, ensure_ascii=False)
                        st.success("Facture supprimée !")
                        st.rerun()
        except Exception as e:
            st.error(f"Erreur de lecture de l'historique : {str(e)}")