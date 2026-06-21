"""
Page Gestion des Utilisateurs — Administrateur uniquement
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import (get_all_users, create_user, update_user, delete_user,
                      reset_password, toggle_user_status, get_all_departements)
from utils.helpers import format_datetime, get_status_label


def show_utilisateurs():
    st.markdown("<div class='page-title'>👥 Gestion des Utilisateurs</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Liste des utilisateurs", "➕ Créer un utilisateur"])

    # ── Onglet liste ──────────────────────────────────────────────────────────
    with tab1:
        users = get_all_users()
        depts = {d["id"]: d["nom"] for d in get_all_departements()}

        # Filtres
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            f_role  = st.selectbox("Filtrer par rôle", ["Tous", "Administrateur", "Formateur", "Stagiaire"])
        with fcol2:
            f_statut = st.selectbox("Filtrer par statut", ["Tous", "Actif", "Inactif"])
        with fcol3:
            f_search = st.text_input("🔍 Rechercher", placeholder="Nom, prénom ou identifiant")

        # Application des filtres
        filtered = users
        if f_role != "Tous":
            filtered = [u for u in filtered if u["role"] == f_role]
        if f_statut == "Actif":
            filtered = [u for u in filtered if u["statut"] == 1]
        elif f_statut == "Inactif":
            filtered = [u for u in filtered if u["statut"] == 0]
        if f_search:
            q = f_search.lower()
            filtered = [u for u in filtered if
                        q in u["nom"].lower() or
                        q in u["prenom"].lower() or
                        q in u["identifiant"].lower()]

        st.markdown(f"**{len(filtered)} utilisateur(s) trouvé(s)**")

        for u in filtered:
            role_badge = {
                "Administrateur": "badge-admin",
                "Formateur": "badge-formateur",
                "Stagiaire": "badge-stagiaire",
            }.get(u["role"], "")

            with st.expander(f"{'✅' if u['statut'] else '❌'}  {u['prenom']} {u['nom']}  —  {u['identifiant']}"):
                ci1, ci2 = st.columns(2)
                with ci1:
                    st.markdown(f"**ID :** {u['id']}")
                    st.markdown(f"**Rôle :** <span class='{role_badge}'>{u['role']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Département :** {u.get('departement_nom') or '—'}")
                with ci2:
                    st.markdown(f"**Statut :** {get_status_label(u['statut'])}")
                    st.markdown(f"**Créé le :** {format_datetime(u['date_creation'])}")

                # Actions
                ac1, ac2, ac3, ac4 = st.columns(4)
                with ac1:
                    if st.button("✏️ Modifier", key=f"edit_{u['id']}"):
                        st.session_state["edit_user"] = u
                with ac2:
                    new_statut = 0 if u["statut"] else 1
                    label_btn  = "🔒 Désactiver" if u["statut"] else "🔓 Activer"
                    if st.button(label_btn, key=f"toggle_{u['id']}"):
                        toggle_user_status(u["id"], new_statut)
                        st.success("Statut mis à jour.")
                        st.rerun()
                with ac3:
                    if st.button("🔑 Réinit. MDP", key=f"reset_{u['id']}"):
                        st.session_state["reset_user"] = u["id"]
                with ac4:
                    if u["identifiant"] != "admin":
                        if st.button("🗑️ Supprimer", key=f"del_{u['id']}"):
                            st.session_state["confirm_del"] = u["id"]

        # Formulaire de modification
        if "edit_user" in st.session_state:
            u = st.session_state["edit_user"]
            st.divider()
            st.markdown("#### ✏️ Modifier l'utilisateur")
            with st.form("edit_user_form"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_nom    = st.text_input("Nom",    value=u["nom"])
                    new_prenom = st.text_input("Prénom", value=u["prenom"])
                with ec2:
                    roles       = ["Administrateur", "Formateur", "Stagiaire"]
                    new_role    = st.selectbox("Rôle", roles, index=roles.index(u["role"]))
                    dept_list   = get_all_departements()
                    dept_names  = ["(aucun)"] + [d["nom"] for d in dept_list]
                    cur_dept    = u.get("departement_nom") or "(aucun)"
                    dept_idx    = dept_names.index(cur_dept) if cur_dept in dept_names else 0
                    new_dept_n  = st.selectbox("Département", dept_names, index=dept_idx)
                    new_dept_id = next((d["id"] for d in dept_list if d["nom"] == new_dept_n), None)
                    new_statut  = st.selectbox("Statut", [1, 0],
                                               format_func=lambda x: "Actif" if x else "Inactif",
                                               index=0 if u["statut"] else 1)
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.form_submit_button("💾 Enregistrer", type="primary", use_container_width=True):
                        update_user(u["id"], new_nom, new_prenom, new_role, new_dept_id, new_statut)
                        del st.session_state["edit_user"]
                        st.success("Utilisateur mis à jour.")
                        st.rerun()
                with bc2:
                    if st.form_submit_button("❌ Annuler", use_container_width=True):
                        del st.session_state["edit_user"]
                        st.rerun()

        # Réinitialisation MDP
        if "reset_user" in st.session_state:
            st.divider()
            st.markdown("#### 🔑 Réinitialiser le mot de passe")
            with st.form("reset_pwd_form"):
                new_pwd  = st.text_input("Nouveau mot de passe", type="password")
                new_pwd2 = st.text_input("Confirmer", type="password")
                rb1, rb2 = st.columns(2)
                with rb1:
                    if st.form_submit_button("✅ Confirmer", type="primary", use_container_width=True):
                        if new_pwd != new_pwd2:
                            st.error("Les mots de passe ne correspondent pas.")
                        elif len(new_pwd) < 6:
                            st.error("Le mot de passe doit contenir au moins 6 caractères.")
                        else:
                            reset_password(st.session_state["reset_user"], new_pwd)
                            del st.session_state["reset_user"]
                            st.success("Mot de passe réinitialisé.")
                            st.rerun()
                with rb2:
                    if st.form_submit_button("❌ Annuler", use_container_width=True):
                        del st.session_state["reset_user"]
                        st.rerun()

        # Confirmation suppression
        if "confirm_del" in st.session_state:
            st.divider()
            st.warning(f"⚠️ Confirmer la suppression de l'utilisateur ID {st.session_state['confirm_del']} ?")
            db1, db2 = st.columns(2)
            with db1:
                if st.button("✅ Oui, supprimer", type="primary"):
                    delete_user(st.session_state["confirm_del"])
                    del st.session_state["confirm_del"]
                    st.success("Utilisateur supprimé.")
                    st.rerun()
            with db2:
                if st.button("❌ Annuler"):
                    del st.session_state["confirm_del"]
                    st.rerun()

    # ── Onglet création ────────────────────────────────────────────────────────
    with tab2:
        st.markdown("#### ➕ Créer un nouveau compte")
        depts = get_all_departements()

        with st.form("create_user_form"):
            nc1, nc2 = st.columns(2)
            with nc1:
                c_nom      = st.text_input("Nom *")
                c_prenom   = st.text_input("Prénom *")
                c_identif  = st.text_input("Identifiant *", placeholder="login unique")
            with nc2:
                c_role     = st.selectbox("Rôle *", ["Formateur", "Stagiaire", "Administrateur"])
                dept_names = ["(aucun)"] + [d["nom"] for d in depts]
                c_dept_n   = st.selectbox("Département", dept_names)
                c_dept_id  = next((d["id"] for d in depts if d["nom"] == c_dept_n), None)
            c_pwd  = st.text_input("Mot de passe *", type="password", placeholder="Min. 6 caractères")
            c_pwd2 = st.text_input("Confirmer le mot de passe *", type="password")

            if st.form_submit_button("✅ Créer le compte", type="primary", use_container_width=True):
                if not all([c_nom, c_prenom, c_identif, c_pwd]):
                    st.error("Tous les champs obligatoires (*) doivent être remplis.")
                elif c_pwd != c_pwd2:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(c_pwd) < 6:
                    st.error("Le mot de passe doit contenir au moins 6 caractères.")
                else:
                    ok, msg = create_user(c_nom, c_prenom, c_identif, c_pwd, c_role, c_dept_id)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
