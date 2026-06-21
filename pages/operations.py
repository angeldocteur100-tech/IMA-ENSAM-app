"""
Page Gestion des Opérations — IMA
Référentiel officiel des opérations aéronautiques
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_all_operations, create_operation


# Groupes officiels IMA
GROUPES = {
    "🔩 Opérations Principales": [
        "OP001 — Débitage",
        "OP002 — Ajustage",
    ],
    "⚙️ OP003 — Usinage": [
        "OP003 — Usinage : Perçage",
        "OP003 — Usinage : Alésage",
        "OP003 — Usinage : Fraisurage",
        "OP003 — Usinage : Lamage",
    ],
    "🔧 OP005 — Assemblage": [
        "OP005 — Assemblage : Accostage / Épinglage",
        "OP005 — Assemblage : Rivetage",
    ],
    "✅ OP006 — Contrôle": [
        "OP006 — Auto-contrôle",
        "OP006 — Contrôle Final",
    ],
    "🎨 Procédés Spéciaux": [
        "PS — Peinture / Retouche",
        "PS — Calage",
        "PS — Alludine",
        "PS — Métalisation",
        "PS — Mastic",
        "PS — Couple de serrage",
        "PS — Freinage",
    ],
}

COULEURS_GROUPES = {
    "🔩 Opérations Principales":  "#1E3A5F",
    "⚙️ OP003 — Usinage":         "#2E5D9A",
    "🔧 OP005 — Assemblage":       "#C8A951",
    "✅ OP006 — Contrôle":         "#198754",
    "🎨 Procédés Spéciaux":        "#6f42c1",
}


def show_operations():
    user = st.session_state["user"]
    role = user["role"]
    can_edit = role in ("Administrateur", "Formateur")

    st.markdown("<div class='page-title'>⚙️ Référentiel des Opérations IMA</div>",
                unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#f0f4ff;border-left:4px solid #1E3A5F;padding:.8rem 1rem;
                border-radius:8px;margin-bottom:1.2rem;font-size:.88rem;color:#1E3A5F;'>
        📋 Ce référentiel contient les opérations officielles utilisées dans les ateliers de l'IMA.
        Chaque mise en situation peut utiliser une ou plusieurs de ces opérations.
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["📋 Référentiel", "➕ Ajouter une opération"] if can_edit else ["📋 Référentiel"])

    # ── Onglet Référentiel ────────────────────────────────────────────────────
    with tabs[0]:
        ops_db = get_all_operations()
        ops_dict = {op["nom"]: op for op in ops_db}

        search = st.text_input("🔍 Rechercher une opération", placeholder="Ex: Perçage, Rivetage…")

        for groupe, op_noms in GROUPES.items():
            couleur = COULEURS_GROUPES.get(groupe, "#1E3A5F")

            # Filtrer selon recherche
            if search:
                op_noms_filtres = [n for n in op_noms if search.lower() in n.lower()]
                if not op_noms_filtres:
                    continue
            else:
                op_noms_filtres = op_noms

            # En-tête du groupe
            st.markdown(f"""
            <div style='background:{couleur};color:white;padding:.6rem 1.2rem;
                        border-radius:10px 10px 0 0;margin-top:1rem;font-weight:700;font-size:.95rem;'>
                {groupe}
            </div>
            """, unsafe_allow_html=True)

            # Lignes d'opérations
            rows_html = ""
            for i, nom in enumerate(op_noms_filtres):
                op = ops_dict.get(nom)
                bg = "#ffffff" if i % 2 == 0 else "#f8f9fa"
                desc = op["description"] if op else "—"
                op_id = f"#{op['id']}" if op else "—"
                statut = "✅ En base" if op else "⚠️ Non trouvée"
                statut_color = "#198754" if op else "#dc3545"
                rows_html += f"""
                <div style='display:flex;align-items:center;padding:.55rem 1.2rem;
                            background:{bg};border-bottom:1px solid #dee2e6;gap:1rem;'>
                    <div style='width:40px;font-size:.75rem;color:#6c757d;font-weight:600;'>{op_id}</div>
                    <div style='flex:1.5;font-weight:600;color:#212529;font-size:.88rem;'>{nom}</div>
                    <div style='flex:2.5;font-size:.82rem;color:#6c757d;'>{desc}</div>
                    <div style='width:90px;font-size:.75rem;font-weight:600;color:{statut_color};text-align:right;'>{statut}</div>
                </div>"""

            st.markdown(
                f"<div style='border:1px solid #dee2e6;border-top:none;border-radius:0 0 10px 10px;margin-bottom:.3rem;'>"
                f"{rows_html}</div>",
                unsafe_allow_html=True
            )

        # Total
        st.markdown(f"""
        <div style='text-align:right;font-size:.82rem;color:#6c757d;margin-top:.5rem;'>
            Total : <strong>{len(ops_db)} opération(s)</strong> dans la base de données
        </div>
        """, unsafe_allow_html=True)

        # Opérations hors référentiel
        noms_officiels = [n for groupe in GROUPES.values() for n in groupe]
        ops_hors = [op for op in ops_db if op["nom"] not in noms_officiels]
        if ops_hors:
            st.markdown("---")
            st.markdown("#### ➕ Opérations personnalisées")
            import pandas as pd
            df = pd.DataFrame([{"ID": op["id"], "Nom": op["nom"],
                                 "Description": op.get("description") or "—"}
                                for op in ops_hors])
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Onglet Création ────────────────────────────────────────────────────────
    if can_edit and len(tabs) > 1:
        with tabs[1]:
            st.markdown("#### ➕ Ajouter une opération personnalisée")
            st.info("💡 Les opérations du référentiel officiel sont déjà présentes. Utilisez cet espace pour ajouter des opérations spécifiques à votre département.")

            with st.form("create_op_form"):
                # Groupe suggéré
                groupe_choix = st.selectbox(
                    "Groupe / Famille *",
                    list(GROUPES.keys()) + ["🆕 Nouvelle famille"]
                )

                op_nom  = st.text_input("Nom de l'opération *",
                                         placeholder="Ex: OP003 — Usinage : Tournage")
                op_desc = st.text_area("Description", height=100,
                                        placeholder="Décrivez brièvement cette opération…")

                st.caption("⚠️ Le nom doit être unique dans la base de données.")

                if st.form_submit_button("✅ Ajouter l'opération", type="primary",
                                          use_container_width=True):
                    if not op_nom:
                        st.error("Le nom est obligatoire.")
                    else:
                        ok, msg = create_operation(op_nom.strip(), op_desc)
                        if ok:
                            st.success(f"✅ Opération **{op_nom}** ajoutée avec succès.")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")