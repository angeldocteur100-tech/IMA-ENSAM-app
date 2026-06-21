"""
Page Profil Utilisateur — IMA
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import reset_password, get_all_chronometrages, get_user_by_id
from utils.helpers import format_datetime, format_duration


def show_profil():
    user = st.session_state["user"]
    role = user["role"]

    st.markdown("<div class='page-title'>👤 Mon Profil</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        # Avatar
        initiales = f"{user['prenom'][0]}{user['nom'][0]}".upper()
        role_color = {
            "Administrateur": "#dc3545",
            "Formateur":      "#0d6efd",
            "Stagiaire":      "#198754",
        }.get(role, "#6c757d")
        st.markdown(f"""
        <div style='text-align:center;padding:2rem 1rem;background:white;border-radius:16px;
                    box-shadow:0 2px 12px rgba(0,0,0,.08);'>
            <div style='width:90px;height:90px;border-radius:50%;background:{role_color};
                        display:flex;align-items:center;justify-content:center;
                        font-size:2.2rem;font-weight:800;color:white;margin:0 auto 1rem;'>
                {initiales}
            </div>
            <div style='font-size:1.2rem;font-weight:700;'>{user['prenom']} {user['nom']}</div>
            <div style='font-size:.85rem;color:#6c757d;margin:.3rem 0;'>{user['identifiant']}</div>
            <span style='background:{role_color};color:white;padding:3px 14px;
                         border-radius:20px;font-size:.8rem;font-weight:600;'>
                {role}
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 📋 Informations")
        info = {
            "ID":           str(user["id"]),
            "Nom":          user["nom"],
            "Prénom":       user["prenom"],
            "Identifiant":  user["identifiant"],
            "Rôle":         role,
            "Département":  user.get("departement_nom") or "—",
            "Compte créé":  format_datetime(user.get("date_creation", "")),
            "Statut":       "✅ Actif" if user.get("statut",1) else "❌ Inactif",
        }
        for k, v in info.items():
            st.markdown(f"**{k} :** {v}")

        # Stats pour stagiaire
        if role == "Stagiaire":
            st.divider()
            chronos = get_all_chronometrages(stagiaire_id=user["id"])
            if chronos:
                times = [c["temps_secondes"] for c in chronos]
                st.markdown("#### 📊 Mes statistiques")
                ms1, ms2, ms3 = st.columns(3)
                with ms1: st.metric("Mesures effectuées", len(chronos))
                with ms2: st.metric("Temps moyen",  format_duration(sum(times)/len(times)))
                with ms3: st.metric("Meilleur temps", format_duration(min(times)))

    # ── Changement de mot de passe ────────────────────────────────────────────
    st.divider()
    st.markdown("#### 🔑 Changer mon mot de passe")

    with st.form("change_pwd_form"):
        pc1, pc2 = st.columns(2)
        with pc1:
            new_pwd  = st.text_input("Nouveau mot de passe", type="password",
                                     placeholder="Min. 6 caractères")
        with pc2:
            new_pwd2 = st.text_input("Confirmer le mot de passe", type="password")

        if st.form_submit_button("🔒 Changer le mot de passe", type="primary"):
            if not new_pwd:
                st.error("Veuillez saisir un nouveau mot de passe.")
            elif len(new_pwd) < 6:
                st.error("Le mot de passe doit contenir au moins 6 caractères.")
            elif new_pwd != new_pwd2:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                reset_password(user["id"], new_pwd)
                st.success("✅ Mot de passe modifié avec succès.")
