
"""
Application IMA — Institut des Métiers de l'Aéronautique
Point d'entrée principal (app.py)

Lancement : streamlit run app.py
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from database import init_database, authenticate_user

# ── Configuration Streamlit ───────────────────────────────────────────────────
st.set_page_config(
    page_title="IMA — Gestion des Formations",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 1. Masquer la partie supérieure native du menu Streamlit via CSS
st.markdown(
    """
    <style>
        /* Masque la liste des pages natives générée par le dossier 'pages' */
        [data-testid="stSidebarNav"] ul {
            display: none !important;
        }
        
        /* Masque aussi la ligne de séparation si elle apparaît */
        [data-testid="stSidebarNav"] {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Les logos sur la page globale d'arrière-plan
st.markdown("""
<style>
.logo-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,2,1])

with col1:
    st.image("logo.png", width=150)

with col3:
    st.image("Ensam_logo.jpeg", width=150)

# Initialise la base au démarrage
init_database()

# ── CSS Global ────────────────────────────────────────────────────────────────
def load_css():
    st.markdown("""
    <style>
    /* ── Palette IMA ── */
    :root {
        --bleu-ima:    #1E3A5F;
        --bleu-clair:  #2E5D9A;
        --or-ima:      #C8A951;
        --gris-clair:  #F4F6F9;
        --gris-bord:   #DEE2E6;
        --texte:       #212529;
        --succes:      #198754;
        --danger:      #DC3545;
        --warning:     #FFC107;
    }

    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E3A5F 0%, #0d2440 100%) !important;
    }
    
    /* Textes de la sidebar (Sauf les boutons) */
    [data-testid="stSidebar"] .sidebar-text-white { 
        color: #ffffff !important; 
    }
    
    [data-testid="stSidebar"] hr { 
        border-color: rgba(200,169,81,.4) !important; 
    }

    /* En-têtes de section sidebar */
    .sidebar-section {
        font-size: .7rem;
        font-weight: 700;
        letter-spacing: .12em;
        text-transform: uppercase;
        color: var(--or-ima) !important;
        padding: .6rem 0 .2rem;
        opacity: .85;
    }

    /* ── STYLE FORCE POUR LES BOUTONS DE LA SIDEBAR ── */
    /* Cible le bouton de manière ultra-précise pour écraser le blanc et le texte clair */
    [data-testid="stSidebar"] div[data-testid="stBtnContainer"] button {
        background-color: #2E5D9A !important;
        border: 1px solid rgba(200,169,81,0.4) !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        margin-bottom: 2px !important;
    }

    /* Style du texte ET de l'icône à l'intérieur du bouton de la sidebar */
    [data-testid="stSidebar"] div[data-testid="stBtnContainer"] button p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    /* Effet au survol (Hover) : Le bouton devient doré, le texte devient bleu foncé */
    [data-testid="stSidebar"] div[data-testid="stBtnContainer"] button:hover {
        background-color: #C8A951 !important;
        border-color: #C8A951 !important;
    }
    [data-testid="stSidebar"] div[data-testid="stBtnContainer"] button:hover p {
        color: #1E3A5F !important;
    }

    /* Cards KPI */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 1.4rem 1.2rem;
        border-left: 4px solid var(--bleu-ima);
        box-shadow: 0 2px 12px rgba(0,0,0,.07);
        text-align: center;
        margin-bottom: .5rem;
    }
    .kpi-card .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--bleu-ima);
        line-height: 1.1;
    }
    .kpi-card .kpi-label {
        font-size: .82rem;
        color: #6c757d;
        margin-top: .3rem;
        font-weight: 500;
    }

    /* Badges rôles */
    .badge-admin    { background:#dc3545; color:#fff; padding:2px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }
    .badge-formateur{ background:#0d6efd; color:#fff; padding:2px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }
    .badge-stagiaire{ background:#198754; color:#fff; padding:2px 10px; border-radius:20px; font-size:.78rem; font-weight:600; }

    /* Titre de page */
    .page-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--bleu-ima);
        padding-bottom: .4rem;
        border-bottom: 3px solid var(--or-ima);
        margin-bottom: 1.2rem;
    }

    /* Bouton primaire (Page principale) */
    .stButton > button[kind="primary"] {
        background: var(--bleu-ima) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--bleu-clair) !important;
    }

    /* Tableaux */
    .dataframe tbody tr:hover { background-color: #e8f0fe !important; }

    /* Chrono */
    .chrono-display {
        font-size: 3.5rem;
        font-weight: 800;
        color: var(--bleu-ima);
        font-family: 'Courier New', monospace;
        text-align: center;
        background: #f0f4ff;
        border-radius: 16px;
        padding: 1.5rem;
        border: 3px solid var(--bleu-ima);
        letter-spacing: .05em;
    }
    .chrono-running {
        border-color: #198754 !important;
        color: #198754 !important;
        background: #f0fff4 !important;
        animation: pulse 1.2s infinite;
    }
    @keyframes pulse {
        0%,100% { box-shadow: 0 0 0 0 rgba(25,135,84,.4); }
        50%      { box-shadow: 0 0 0 10px rgba(25,135,84,0); }
    }

    /* Formulaires */
    .stTextInput > label, .stSelectbox > label, .stTextArea > label {
        font-weight: 600 !important;
        color: var(--texte) !important;
    }

    /* Logo zone */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 1rem 0 .8rem;
    }
    .logo-text-ima {
        font-size: 1.4rem;
        font-weight: 800;
        color: #fff;
        line-height: 1;
    }
    .logo-sub {
        font-size: .72rem;
        color: var(--or-ima);
        font-weight: 500;
    }

    /* Login page */
    .login-container {
        max-width: 420px;
        margin: 3rem auto;
        background: white;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,.12);
    }
    .login-title {
        text-align: center;
        color: var(--bleu-ima);
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: .3rem;
    }
    .login-sub {
        text-align: center;
        color: #6c757d;
        font-size: .88rem;
        margin-bottom: 1.5rem;
    }

    /* Alertes custom */
    .alert-success {
        background: #d1e7dd; border-left: 4px solid #198754;
        padding: .8rem 1rem; border-radius: 8px; color: #0a3622;
        margin: .5rem 0;
    }
    .alert-danger {
        background: #f8d7da; border-left: 4px solid #dc3545;
        padding: .8rem 1rem; border-radius: 8px; color: #58151c;
        margin: .5rem 0;
    }
    .alert-info {
        background: #cfe2ff; border-left: 4px solid #0d6efd;
        padding: .8rem 1rem; border-radius: 8px; color: #08306b;
        margin: .5rem 0;
    }

    /* Masquer le menu Streamlit par défaut */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


# ── Page de connexion ─────────────────────────────────────────────────────────
def show_login():
    load_css()
    
    # Injection du CSS pour cacher totalement la barre latérale au login
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown("""
        
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("#### Connexion")
            identifiant = st.text_input("Identifiant", placeholder="Votre identifiant")
            password    = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            submitted   = st.form_submit_button("Se connecter", use_container_width=True, type="primary")

        if submitted:
            if not identifiant or not password:
                st.error("Veuillez renseigner tous les champs.")
            else:
                user = authenticate_user(identifiant, password)
                if user:
                    st.session_state["user"] = user
                    st.session_state["page"] = "dashboard"
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect, ou compte désactivé.")

        st.markdown("""
        <div style='text-align:center;margin-top:1.5rem;font-size:.78rem;color:#adb5bd;'>
            Comptes démo : admin / admin123 · formateur1 / form123 · stagiaire1 / stag123
        </div>
        """, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
from streamlit_option_menu import option_menu

def show_sidebar():
    user = st.session_state["user"]
    role = user["role"]

    with st.sidebar:
        st.image("logo.png", use_container_width=True)

        st.markdown(f"""
        <div class="sidebar-text-white" style='padding:.5rem 0;'>
            <div style='font-size:1rem;font-weight:700;'>Bonjour {user["prenom"]} {user["nom"]}</div>
            <div style='font-size:.82rem;margin-top:.2rem;opacity:.9;'>Rôle : {role}</div>
            {'<div style="font-size:.78rem;opacity:.8;">Dépt. : ' + (user.get("departement_nom") or "—") + '</div>' if user.get("departement_nom") else ""}
        </div>
        <hr/>
        """, unsafe_allow_html=True)

        # ── Construction de la liste des pages selon le rôle ────────────────
        pages_communes = [("Tableau de bord", "dashboard", "house-door-fill")]
        pages_admin = [
            ("Utilisateurs",            "utilisateurs", "people-fill"),
            ("Tous les chronométrages", "tous_chronos", "bar-chart-line-fill"),
            ("Statistiques globales",   "stats",        "graph-up-arrow"),
            ("Mises en situation",      "mes",          "clipboard-check-fill"),
            ("Opérations",              "operations",   "gear-fill"),
        ]
        pages_formateur = [
            ("Mises en situation",   "mes",        "clipboard-check-fill"),
            ("Opérations",           "operations", "gear-fill"),
            ("Résultats stagiaires", "resultats",  "bar-chart-line-fill"),
            ("Statistiques",         "stats",      "graph-up-arrow"),
        ]
        pages_stagiaire = [
            ("Mises en situation", "mes",          "clipboard-check-fill"),
            ("Chronométrage",      "chrono",       "stopwatch-fill"),
            ("Mes résultats",      "mes_resultats","bar-chart-line-fill"),
        ]
        pages_profil = [("Mon profil", "profil", "person-circle")]

        all_pages = pages_communes.copy()
        if role == "Administrateur":
            all_pages += pages_admin
        elif role == "Formateur":
            all_pages += pages_formateur
        else:
            all_pages += pages_stagiaire
        all_pages += pages_profil

        labels = [p[0] for p in all_pages]
        keys   = [p[1] for p in all_pages]
        icons  = [p[2] for p in all_pages]

        current_key = st.session_state.get("page", "dashboard")
        current_index = keys.index(current_key) if current_key in keys else 0

        selected = option_menu(
            menu_title="NAVIGATION",
            options=labels,
            icons=icons,
            menu_icon="list",
            default_index=current_index,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": "#C8A951", "font-size": "1.1rem"},
                "nav-link": {
                    "font-size": "0.95rem",
                    "text-align": "left",
                    "margin": "2px 0",
                    "color": "#FFFFFF",
                    "background-color": "#2E5D9A",
                    "border-radius": "8px",
                    "border": "1px solid rgba(200,169,81,0.4)",
                },
                "nav-link-selected": {
                    "background-color": "#C8A951",
                    "color": "#1E3A5F",
                    "font-weight": "700",
                },
            },
        )

        # Synchroniser la sélection avec votre session_state
        new_key = keys[labels.index(selected)]
        if new_key != current_key:
            st.session_state["page"] = new_key
            st.rerun()

        st.markdown("<hr/>", unsafe_allow_html=True)
        if st.button("Déconnexion", use_container_width=True, icon=":material/logout:"):
            st.session_state.clear()
            st.rerun()


# ── Routeur principal ─────────────────────────────────────────────────────────
def route():
    load_css()
    show_sidebar()

    page = st.session_state.get("page", "dashboard")
    user = st.session_state["user"]
    role = user["role"]

    # Imports dynamiques pour garder app.py léger
    if page == "dashboard":
        from pages.dashboard import show_dashboard
        show_dashboard()

    elif page == "utilisateurs" and role == "Administrateur":
        from pages.utilisateurs import show_utilisateurs
        show_utilisateurs()

    elif page == "mes":
        from pages.mises_en_situation import show_mes
        show_mes()

    elif page == "operations":
        if role in ("Administrateur", "Formateur"):
            from pages.operations import show_operations
            show_operations()

    elif page == "chrono":
        from pages.chronometrage import show_chronometrage
        show_chronometrage()

    elif page == "resultats" and role in ("Administrateur", "Formateur"):
        from pages.resultats import show_resultats
        show_resultats()

    elif page == "tous_chronos" and role == "Administrateur":
        from pages.resultats import show_resultats
        show_resultats(all_users=True)

    elif page == "mes_resultats" and role == "Stagiaire":
        from pages.resultats import show_resultats
        show_resultats(stagiaire_id=user["id"])

    elif page == "stats":
        from pages.statistiques import show_statistiques
        show_statistiques()

    elif page == "profil":
        from pages.profil import show_profil
        show_profil()

    else:
        from pages.dashboard import show_dashboard
        show_dashboard()


# ── Point d'entrée ────────────────────────────────────────────────────────────
def main():
    if "user" not in st.session_state:
        show_login()
    else:
        route()


if __name__ == "__main__":
    main()

