import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

# Configuration de la page
st.set_page_config(page_title="POWERMUST - Simulateur de Recharge", layout="wide")

# --- CORRECTIF CSS (Responsive + Masquer le plein écran) ---
st.markdown("""
<style>
/* Force le centrage parfait du contenu des boutons */
div[data-testid="stButton"] button {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
/* Cache le bouton "Plein écran" sur les images */
button[title="View fullscreen"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# =================================================================
# --- EN-TÊTE AVEC LOGO ---
# =================================================================
try:
    st.image("logo-powermust.png", width=250)
except:
    st.info("🖼️ Ajoutez 'logo-powermust.png' dans le dossier pour afficher votre logo ici")

st.title("⚡ Simulateur de recharge - POWERMUST")

# =================================================================
# --- INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
# =================================================================
if 'limite_reseau_defaut' not in st.session_state: st.session_state.limite_reseau_defaut = 250
if 'puissance_module' not in st.session_state: st.session_state.puissance_module = 189
if 'capacite_module' not in st.session_state: st.session_state.capacite_module = 189
if 'nb_modules' not in st.session_state: st.session_state.nb_modules = 6
if 'soc_initial' not in st.session_state: st.session_state.soc_initial = 1134
if 'plages_reseau' not in st.session_state: st.session_state.plages_reseau = []
if 'sessions' not in st.session_state: st.session_state.sessions = []
if 'nom_fichier_actuel' not in st.session_state: st.session_state.nom_fichier_actuel = "simulation_powermust.json"
if 'id_fichier_charge' not in st.session_state: st.session_state.id_fichier_charge = None

# =================================================================
# --- BARRE LATÉRALE : SAUVEGARDE & PARAMÈTRES ---
# =================================================================
st.sidebar.header("💾 Sauvegarder / Charger")

# 1. CHARGER UNE SIMULATION
fichier_charge = st.sidebar.file_uploader("Ouvrir une simulation (.json)", type=["json"])

if fichier_charge is not None:
    if st.session_state.id_fichier_charge != fichier_charge.file_id:
        try:
            data = json.load(fichier_charge)
            st.session_state.limite_reseau_defaut = data.get("limite_reseau_defaut", 250)
            st.session_state.puissance_module = data.get("puissance_module", 189)
            st.session_state.capacite_module = data.get("capacite_module", 189)
            st.session_state.nb_modules = data.get("nb_modules", 6)
            st.session_state.soc_initial = data.get("soc_initial", 1134)
            st.session_state.plages_reseau = data.get("plages_reseau", [])
            st.session_state.sessions = data.get("sessions", [])
            
            st.session_state.nom_fichier_actuel = fichier_charge.name 
            st.session_state.id_fichier_charge = fichier_charge.file_id 
            st.sidebar.success(f"✅ Simulation '{fichier_charge.name}' chargée !")
            st.rerun() 
        except Exception as e:
            st.sidebar.error("Erreur lors du chargement du fichier.")
else:
    st.session_state.id_fichier_charge = None

# 2. SAUVEGARDER LA SIMULATION ACTUELLE
donnees_a_sauvegarder = {
    "limite_reseau_defaut": st.session_state.limite_reseau_defaut,
    "puissance_module": st.session_state.puissance_module,
    "capacite_module": st.session_state.capacite_module,
    "nb_modules": st.session_state.nb_modules,
    "soc_initial": st.session_state.soc_initial,
    "plages_reseau": st.session_state.plages_reseau,
    "sessions": st.session_state.sessions
}
json_string = json.dumps(donnees_a_sauvegarder, indent=4)

nom_fichier_saisi = st.sidebar.text_input("Nom de la sauvegarde", value=st.session_state.nom_fichier_actuel)
if not nom_fichier_saisi.endswith('.json'):
    nom_fichier_saisi += '.json'

st.sidebar.download_button(
    label="⬇️ Enregistrer la simulation",
    data=json_string,
    file_name=nom_fichier_saisi,
    mime="application/json",
    use_container_width=True
)

st.sidebar.markdown("---")

# =================================================================
# --- PARAMÈTRES DU SITE & BATTERIE ---
# =================================================================
st.sidebar.header("⚙️ Paramètres de la Simulation")

st.sidebar.subheader("🔌 Raccordement Réseau")
# CORRECTION : On passe la valeur existante et on la met à jour manuellement sans utiliser le paramètre "key"
limite_reseau_defaut = st.sidebar.number_input("Puissance Réseau par défaut (24h) en kW", value=st.session_state.limite_reseau_defaut, step=10)
st.session_state.limite_reseau_defaut = limite_reseau_defaut

st.sidebar.markdown("**Ajouter une plage réseau spécifique**")
col_r1, col_r2 = st.sidebar.columns(2)
with col_r1:
    debut_res = st.time_input("Début", datetime.strptime("06:00", "%H:%M"), key="deb_res")
with col_r2:
    fin_res = st.time_input("Fin", datetime.strptime("22:00", "%H:%M"), key="fin_res")
puissance_res = st.sidebar.number_input("Puissance spécifique (kW)", min_value=0, value=200, step=10, key="pwr_res")

if st.sidebar.button("➕ Ajouter cette plage"):
    st.session_state.plages_reseau.append({
        "Début": debut_res.strftime("%H:%M"),
        "Fin": fin_res.strftime("%H:%M"),
        "Puissance": puissance_res
    })
    st.rerun()

if st.session_state.plages_reseau:
    st.sidebar.markdown("**Plages spécifiques actives :**")
    for i, plage in enumerate(st.session_state.plages_reseau):
        c1, c2, c3 = st.sidebar.columns([3, 2, 1.2], vertical_alignment="center")
        c1.write(f"{plage['Début']}-{plage['Fin']}")
        c2.write(f"**{plage['Puissance']}kW**")
        if c3.button("❌", key=f"del_res_{i}", use_container_width=True):
            st.session_state.plages_reseau.pop(i)
            st.rerun()

st.sidebar.markdown("---")

st.sidebar.subheader("🔋 Configuration Station (Modules)")
# CORRECTION : Sauvegarde manuelle pour éviter l'effacement lors d'un rerun()
puissance_module = st.sidebar.number_input("Puissance d'un module (kW)", value=st.session_state.puissance_module, step=10)
st.session_state.puissance_module = puissance_module

capacite_module = st.sidebar.number_input("Capacité d'un module (kWh)", value=st.session_state.capacite_module, step=10)
st.session_state.capacite_module = capacite_module

nb_modules = st.sidebar.number_input("Nombre de modules", min_value=1, max_value=20, value=st.session_state.nb_modules, step=1)
st.session_state.nb_modules = nb_modules

puissance_totale_batterie = puissance_module * nb_modules
capacite_totale_batterie = capacite_module * nb_modules
st.sidebar.success(f"**Total Station : {puissance_totale_batterie} kW / {capacite_totale_batterie} kWh**")

# CORRECTION : Si on baisse le nombre de modules, le SOC initial en mémoire pourrait dépasser la nouvelle capacité max. On corrige ça avant l'affichage.
if st.session_state.soc_initial > capacite_totale_batterie:
    st.session_state.soc_initial = int(capacite_totale_batterie)

soc_initial = st.sidebar.number_input("SOC Initial (kWh)", min_value=0, max_value=int(capacite_totale_batterie), value=st.session_state.soc_initial, step=50)
st.session_state.soc_initial = soc_initial

# =================================================================
# --- GESTION DES SESSIONS DE RECHARGE (Camions) ---
# =================================================================
st.subheader("🚚 Ajouter une session de recharge (Camion)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    nom_camion = st.text_input("Nom du Camion", f"Camion {len(st.session_state.sessions) + 1}")
with col2:
    heure_debut = st.time_input("Heure de début", datetime.strptime("18:00", "%H:%M"))
with col3:
    heure_fin = st.time_input("Heure de fin", datetime.strptime("04:00", "%H:%M"))
with col4:
    energie_kwh = st.number_input("Énergie à recharger (kWh)", min_value=10, value=200, step=10)

if st.button("➕ Ajouter au planning camion"):
    st.session_state.sessions.append({
        "Camion": nom_camion,
        "Début": heure_debut.strftime("%H:%M"),
        "Fin": heure_fin.strftime("%H:%M"),
        "kWh requis": energie_kwh
    })
    st.rerun()

if st.session_state.sessions:
    st.write("#### Planning actuel des camions")
    
    h1, h2, h3, h4, h5 = st.columns([2, 2, 2, 2, 1])
    h1.write("**Camion**")
    h2.write("**Début**")
    h3.write("**Fin**")
    h4.write("**Énergie**")
    h5.write("**Action**")

    for i, session in enumerate(st.session_state.sessions):
        st.markdown('<hr style="margin: 0.2em 0; border: none; border-top: 1px solid rgba(128, 128, 128, 0.2);">', unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1], vertical_alignment="center")
        c1.write(session["Camion"])
        c2.write(session["Début"])
        c3.write(session["Fin"])
        c4.write(f"{session['kWh requis']} kWh")
        if c5.button("❌", key=f"del_cam_{i}", use_container_width=True):
            st.session_state.sessions.pop(i)
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Vider tout le planning des camions"):
        st.session_state.sessions = []
        st.rerun()

# =================================================================
# --- MOTEUR DE CALCUL INTÉGRAL (Pas de 5 min) ---
# =================================================================
st.write("---")
st.subheader("📊 Analyse de Puissance Cumulée")

temps = pd.date_range("00:00", "23:55", freq="5min").time
df_simulation = pd.DataFrame({"HEURE": temps})

df_simulation["GRID CAP (kW)"] = limite_reseau_defaut
for plage in st.session_state.plages_reseau:
    debut_r = datetime.strptime(plage["Début"], "%H:%M").time()
    fin_r = datetime.strptime(plage["Fin"], "%H:%M").time()
    pwr = plage["Puissance"]
    
    for i, row in df_simulation.iterrows():
        h = row["HEURE"]
        if (debut_r <= fin_r and debut_r <= h <= fin_r) or (debut_r > fin_r and (h >= debut_r or h <= fin_r)):
            df_simulation.at[i, "GRID CAP (kW)"] = pwr

for session in st.session_state.sessions:
    df_simulation[session["Camion"]] = 0.0

df_simulation["BESOIN TOTAL (kW)"] = 0.0

for session in st.session_state.sessions:
    debut_c = datetime.strptime(session["Début"], "%H:%M").time()
    fin_c = datetime.strptime(session["Fin"], "%H:%M").time()
    kwh = session["kWh requis"]
    
    t1 = pd.to_timedelta(str(debut_c))
    t2 = pd.to_timedelta(str(fin_c))
    if t2 < t1: t2 += pd.Timedelta(days=1)
    duree_heures = (t2 - t1).total_seconds() / 3600
    puissance_moyenne = kwh / duree_heures if duree_heures > 0 else 0
    
    for i, row in df_simulation.iterrows():
        h = row["HEURE"]
        if (debut_c <= fin_c and debut_c <= h <= fin_c) or (debut_c > fin_c and (h >= debut_c or h <= fin_c)):
            df_simulation.at[i, session["Camion"]] += puissance_moyenne
            df_simulation.at[i, "BESOIN TOTAL (kW)"] += puissance_moyenne

df_simulation["PUISSANCE RÉSEAU (kW)"] = 0.0
df_simulation["PUISSANCE BATTERIE NETTE (kW)"] = 0.0
df_simulation["SOC FIN HEURE (kWh)"] = 0.0
df_simulation["SPARE LIMITÉ (kW)"] = 0.0
df_simulation["DÉFICIT NON COUVERT (kW)"] = 0.0

soc_actuel = soc_initial

for i, row in df_simulation.iterrows():
    besoin = row["BESOIN TOTAL (kW)"]
    grid_cap = row["GRID CAP (kW)"]
    
    if besoin >= grid_cap:
        p_reseau = grid_cap
        p_batt_desired = besoin - grid_cap
        p_batt_limited = min(p_batt_desired, puissance_totale_batterie)
        e_batt_req = p_batt_limited / 12.0
        
        if soc_actuel >= e_batt_req:
            soc_actuel -= e_batt_req
            p_batt = p_batt_limited
        else:
            p_batt = soc_actuel * 12.0
            soc_actuel = 0.0
            
        deficit = p_batt_desired - p_batt
        spare = 0.0
    else:
        spare_kw = grid_cap - besoin
        e_space = capacite_totale_batterie - soc_actuel
        charge_power_limit = min(spare_kw, puissance_totale_batterie)
        e_charge_limit = charge_power_limit / 12.0
        e_charge_actual = min(e_charge_limit, e_space)
        soc_actuel += e_charge_actual
        
        p_batt = - (e_charge_actual * 12.0)
        p_reseau = besoin + (e_charge_actual * 12.0)
        spare = spare_kw - (e_charge_actual * 12.0)
        deficit = 0.0
        
    df_simulation.at[i, "PUISSANCE RÉSEAU (kW)"] = p_reseau
    df_simulation.at[i, "PUISSANCE BATTERIE NETTE (kW)"] = p_batt
    df_simulation.at[i, "SOC FIN HEURE (kWh)"] = soc_actuel
    df_simulation.at[i, "SPARE LIMITÉ (kW)"] = spare
    df_simulation.at[i, "DÉFICIT NON COUVERT (kW)"] = deficit

df_simulation = df_simulation.round(0)
df_simulation["HEURE_STR"] = df_simulation["HEURE"].apply(lambda x: x.strftime("%H:%M"))

# =================================================================
# --- GRAPHIQUE ---
# =================================================================
df_graph = df_simulation.copy()

fig = px.line(df_graph, x="HEURE_STR", 
              y=["BESOIN TOTAL (kW)", "GRID CAP (kW)", "PUISSANCE RÉSEAU (kW)", "PUISSANCE BATTERIE NETTE (kW)"],
              labels={"value": "Puissance (kW)", "variable": "Légende", "HEURE_STR": "Heure"},
              color_discrete_map={
                  "BESOIN TOTAL (kW)": "#1546F1",
                  "GRID CAP (kW)": "#dd0808",
                  "PUISSANCE RÉSEAU (kW)": "#06ac06",
                  "PUISSANCE BATTERIE NETTE (kW)": "#ff9436"
              })

fig.update_layout(
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    plot_bgcolor="rgba(128, 128, 128, 0.05)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=40, b=10)
)
fig.update_traces(patch={"line": {"dash": "dash", "shape": "vh"}}, selector={"name": "GRID CAP (kW)"})
fig.update_xaxes(tickangle=0, nticks=24, showgrid=True, gridcolor="rgba(128, 128, 128, 0.2)") 
fig.update_yaxes(showgrid=True, gridcolor="rgba(128, 128, 128, 0.2)")

st.plotly_chart(fig, use_container_width=True)

# =================================================================
# --- TABLEAU DE RÉSULTATS ---
# =================================================================
st.write("---")
st.subheader("📋 Tableau de données détaillé")

colonnes_tableau = ["HEURE_STR"] + [s["Camion"] for s in st.session_state.sessions] + [
    "BESOIN TOTAL (kW)", "GRID CAP (kW)", 
    "PUISSANCE RÉSEAU (kW)", "PUISSANCE BATTERIE NETTE (kW)",
    "SOC FIN HEURE (kWh)", "SPARE LIMITÉ (kW)", "DÉFICIT NON COUVERT (kW)"
]

df_tableau = df_simulation.iloc[::6, :][colonnes_tableau].copy()
df_tableau.reset_index(drop=True, inplace=True)
df_tableau.rename(columns={"HEURE_STR": "HEURE"}, inplace=True)

cols_num = df_tableau.columns.drop("HEURE")
df_tableau[cols_num] = df_tableau[cols_num].astype(int)

def appliquer_couleur_alternee(row):
    couleur = 'background-color: rgba(128, 128, 128, 0.15)' if row.name % 2 == 0 else ''
    return [couleur] * len(row)

df_style = df_tableau.style.apply(appliquer_couleur_alternee, axis=1)
st.dataframe(df_style, use_container_width=True, hide_index=True)