"""
Page Gestion des Mises en Situation — IMA
"""

import streamlit as st
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import (get_all_mes, get_mes_by_id, create_mes, update_mes, delete_mes,
                      get_all_departements, get_all_operations, get_operations_by_mes,
                      add_operation_to_mes, remove_operation_from_mes,
                      get_documents_by_mes, save_document, delete_document)
from utils.helpers import format_datetime, save_uploaded_file


def show_mes():
    user = st.session_state["user"]
    role = user["role"]

    st.markdown("<div class='page-title'>📋 Mises en Situation Pédagogiques</div>", unsafe_allow_html=True)

    can_edit = role in ("Administrateur", "Formateur")
    tabs = ["📋 Liste"] + (["➕ Créer"] if can_edit else [])
    tab_objects = st.tabs(tabs)

    # ── Liste des MES ─────────────────────────────────────────────────────────
    with tab_objects[0]:
        mes_list = get_all_mes()
        depts    = get_all_departements()

        fc1, fc2 = st.columns([2, 1])
        with fc1:
            search = st.text_input("🔍 Rechercher", placeholder="Nom, référence, matière…")
        with fc2:
            dept_names = ["Tous"] + [d["nom"] for d in depts]
            f_dept = st.selectbox("Département", dept_names)

        filtered = mes_list
        if search:
            q = search.lower()
            filtered = [m for m in filtered if
                        q in m["nom"].lower() or
                        q in m["reference"].lower() or
                        (m.get("matiere") and q in m["matiere"].lower())]
        if f_dept != "Tous":
            filtered = [m for m in filtered if m.get("departement_nom") == f_dept]

        st.markdown(f"**{len(filtered)} mise(s) en situation trouvée(s)**")

        for m in filtered:
            with st.expander(f"📌 {m['nom']}  |  Réf : {m['reference']}  |  {m.get('departement_nom','—')}"):
                col_info, col_docs = st.columns([2, 1])

                with col_info:
                    st.markdown(f"**Référence :** `{m['reference']}`")
                    st.markdown(f"**Département :** {m.get('departement_nom','—')}")
                    st.markdown(f"**Matière :** {m.get('matiere','—')}")
                    st.markdown(f"**Description :** {m.get('description','—')}")
                    if m.get("observations"):
                        st.markdown(f"**Observations :** {m['observations']}")
                    st.markdown(f"**Créé le :** {format_datetime(m['date_creation'])}")

                    # Opérations associées
                    ops = get_operations_by_mes(m["id"])
                    if ops:
                        st.markdown("**Opérations :**")
                        for op in ops:
                            st.markdown(f"  {op['ordre']}. {op['nom']}")
                    else:
                        st.caption("Aucune opération associée.")

                with col_docs:
                    st.markdown("**Documents associés :**")
                    docs = get_documents_by_mes(m["id"])
                    labels = {"plan": "📐 Plan", "fiche_instruction": "📄 Fiche d'instruction",
                              "fiche_autocontrole": "✅ Fiche d'autocontrôle"}
                    for doc in docs:
                        if os.path.exists(doc["chemin"]):
                            with open(doc["chemin"], "rb") as f:
                                st.download_button(
                                    label=labels.get(doc["type_document"], doc["nom_fichier"]),
                                    data=f.read(),
                                    file_name=doc["nom_fichier"],
                                    mime="application/pdf",
                                    key=f"dl_{doc['id']}",
                                    use_container_width=True,
                                )
                        else:
                            st.caption(f"⚠️ Fichier manquant : {doc['nom_fichier']}")
                    if not docs:
                        st.caption("Aucun document.")

                # Actions formateur/admin
                if can_edit:
                    st.divider()
                    act1, act2, act3 = st.columns(3)
                    with act1:
                        if st.button("✏️ Modifier", key=f"edit_mes_{m['id']}"):
                            st.session_state["edit_mes"] = m
                    with act2:
                        if st.button("🔗 Gérer opérations", key=f"ops_mes_{m['id']}"):
                            st.session_state["manage_ops_mes"] = m["id"]
                    with act3:
                        if st.button("📎 Ajouter doc.", key=f"doc_mes_{m['id']}"):
                            st.session_state["upload_doc_mes"] = m["id"]

        # ── Modifier MES ──────────────────────────────────────────────────────
        if "edit_mes" in st.session_state and can_edit:
            m = st.session_state["edit_mes"]
            st.divider()
            st.markdown("#### ✏️ Modifier la mise en situation")
            depts = get_all_departements()
            with st.form("edit_mes_form"):
                em1, em2 = st.columns(2)
                with em1:
                    new_nom  = st.text_input("Nom *",         value=m["nom"])
                    new_ref  = st.text_input("Référence *",   value=m["reference"])
                    new_mat  = st.text_input("Matière",       value=m.get("matiere",""))
                with em2:
                    dept_names = [d["nom"] for d in depts]
                    cur_dept   = m.get("departement_nom","")
                    d_idx      = dept_names.index(cur_dept) if cur_dept in dept_names else 0
                    new_dept_n = st.selectbox("Département", dept_names, index=d_idx)
                    new_dept_id= next((d["id"] for d in depts if d["nom"] == new_dept_n), None)
                new_desc = st.text_area("Description", value=m.get("description",""), height=80)
                new_obs  = st.text_area("Observations", value=m.get("observations",""), height=60)
                eb1, eb2 = st.columns(2)
                with eb1:
                    if st.form_submit_button("💾 Enregistrer", type="primary", use_container_width=True):
                        update_mes(m["id"], new_nom, new_ref, new_dept_id, new_desc, new_mat, new_obs)
                        del st.session_state["edit_mes"]
                        st.success("Mise en situation mise à jour.")
                        st.rerun()
                with eb2:
                    if st.form_submit_button("❌ Annuler", use_container_width=True):
                        del st.session_state["edit_mes"]
                        st.rerun()

        # ── Gérer opérations ──────────────────────────────────────────────────
        if "manage_ops_mes" in st.session_state and can_edit:
            mes_id = st.session_state["manage_ops_mes"]
            mes    = get_mes_by_id(mes_id)
            st.divider()
            st.markdown(f"#### 🔗 Opérations — {mes['nom']}")

            all_ops  = get_all_operations()
            curr_ops = get_operations_by_mes(mes_id)
            curr_ids = {op["id"] for op in curr_ops}

            # Ops actuelles
            if curr_ops:
                for op in curr_ops:
                    oc1, oc2 = st.columns([4, 1])
                    with oc1:
                        st.markdown(f"**{op['ordre']}.** {op['nom']} — _{op.get('description','')}_")
                    with oc2:
                        if st.button("❌", key=f"rm_op_{mes_id}_{op['id']}"):
                            remove_operation_from_mes(mes_id, op["id"])
                            st.rerun()
            else:
                st.caption("Aucune opération associée.")

            st.markdown("**Ajouter une opération :**")
            available = [op for op in all_ops if op["id"] not in curr_ids]
            if available:
                with st.form(f"add_op_form_{mes_id}"):
                    op_names = [op["nom"] for op in available]
                    sel_op   = st.selectbox("Opération", op_names)
                    ordre    = st.number_input("Ordre", min_value=1, value=len(curr_ops)+1)
                    ab1, ab2 = st.columns(2)
                    with ab1:
                        if st.form_submit_button("➕ Ajouter", type="primary", use_container_width=True):
                            op_id = next(op["id"] for op in available if op["nom"] == sel_op)
                            add_operation_to_mes(mes_id, op_id, ordre)
                            st.success("Opération ajoutée.")
                            st.rerun()
                    with ab2:
                        if st.form_submit_button("Fermer", use_container_width=True):
                            del st.session_state["manage_ops_mes"]
                            st.rerun()
            else:
                st.info("Toutes les opérations sont déjà associées.")
                if st.button("Fermer"):
                    del st.session_state["manage_ops_mes"]
                    st.rerun()

        # ── Upload document ────────────────────────────────────────────────────
        if "upload_doc_mes" in st.session_state and can_edit:
            mes_id = st.session_state["upload_doc_mes"]
            st.divider()
            st.markdown("#### 📎 Ajouter un document")
            type_map = {
                "Plan (PDF)":                ("plan",                "uploads/plans"),
                "Fiche d'instruction (PDF)": ("fiche_instruction",   "uploads/fiches_instruction"),
                "Fiche d'autocontrôle (PDF)":("fiche_autocontrole",  "uploads/fiches_autocontrole"),
            }
            sel_type  = st.selectbox("Type de document", list(type_map.keys()))
            uploaded  = st.file_uploader("Choisir un fichier PDF", type=["pdf"])
            ub1, ub2  = st.columns(2)
            with ub1:
                if st.button("📤 Téléverser", type="primary"):
                    if uploaded:
                        doc_type, folder = type_map[sel_type]
                        nom, chemin = save_uploaded_file(uploaded, folder)
                        save_document(mes_id, doc_type, nom, chemin)
                        del st.session_state["upload_doc_mes"]
                        st.success("Document ajouté avec succès.")
                        st.rerun()
                    else:
                        st.warning("Veuillez sélectionner un fichier.")
            with ub2:
                if st.button("❌ Annuler"):
                    del st.session_state["upload_doc_mes"]
                    st.rerun()

    # ── Onglet Création ───────────────────────────────────────────────────────
    if can_edit and len(tab_objects) > 1:
        with tab_objects[1]:
            st.markdown("#### ➕ Nouvelle mise en situation")
            depts = get_all_departements()
            with st.form("create_mes_form"):
                cm1, cm2 = st.columns(2)
                with cm1:
                    c_nom  = st.text_input("Nom de la pièce *")
                    c_ref  = st.text_input("Référence *", placeholder="Ex: AJU-2024-001")
                    c_mat  = st.text_input("Matière",     placeholder="Ex: Aluminium 2024")
                with cm2:
                    dept_names = [d["nom"] for d in depts]
                    c_dept_n   = st.selectbox("Département *", dept_names)
                    c_dept_id  = next((d["id"] for d in depts if d["nom"] == c_dept_n), None)
                c_desc = st.text_area("Description", height=80)
                c_obs  = st.text_area("Observations", height=68)

                if st.form_submit_button("✅ Créer la mise en situation", type="primary", use_container_width=True):
                    if not c_nom or not c_ref:
                        st.error("Le nom et la référence sont obligatoires.")
                    else:
                        ok, result = create_mes(c_nom, c_ref, c_dept_id, c_desc, c_mat, c_obs, user["id"])
                        if ok:
                            st.success(f"✅ Mise en situation créée (ID {result}).")
                        else:
                            st.error(f"❌ {result}")
