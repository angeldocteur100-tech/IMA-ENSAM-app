"""
Page Résultats des Stagiaires — IMA
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_all_chronometrages, get_all_users, get_all_mes, get_all_operations
from utils.helpers import format_duration, format_date, export_chrono_to_excel


def show_resultats(all_users=False, stagiaire_id=None):
    user = st.session_state["user"]
    role = user["role"]

    st.markdown("<div class='page-title'>📊 Résultats & Chronométrages</div>", unsafe_allow_html=True)

    # Récupération des données
    chronos    = get_all_chronometrages(stagiaire_id=stagiaire_id)
    mes_list   = get_all_mes()
    ops_list   = get_all_operations()
    users_list = [u for u in get_all_users() if u["role"] == "Stagiaire"]

    # ── Filtres ───────────────────────────────────────────────────────────────
    with st.expander("🔍 Filtres", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            if role in ("Administrateur", "Formateur") and all_users:
                stag_names = ["Tous"] + [f"{u['prenom']} {u['nom']}" for u in users_list]
                f_stag = st.selectbox("Stagiaire", stag_names)
            else:
                f_stag = "Tous"
        with fc2:
            mes_names = ["Toutes"] + [m["nom"] for m in mes_list]
            f_mes = st.selectbox("Mise en situation", mes_names)
        with fc3:
            op_names = ["Toutes"] + [op["nom"] for op in ops_list]
            f_op = st.selectbox("Opération", op_names)

    # Application des filtres
    filtered = chronos
    if f_stag != "Tous":
        filtered = [c for c in filtered if c["stagiaire_nom"] == f_stag]
    if f_mes != "Toutes":
        filtered = [c for c in filtered if c["mes_nom"] == f_mes]
    if f_op != "Toutes":
        filtered = [c for c in filtered if c["operation_nom"] == f_op]

    # ── Résumé ─────────────────────────────────────────────────────────────────
    if filtered:
        times = [c["temps_secondes"] for c in filtered]
        ka, kb, kc, kd = st.columns(4)
        with ka:
            st.metric("Nombre de mesures", len(filtered))
        with kb:
            st.metric("Temps moyen", format_duration(sum(times)/len(times)))
        with kc:
            st.metric("Temps min",   format_duration(min(times)))
        with kd:
            st.metric("Temps max",   format_duration(max(times)))

    # ── Tableau ────────────────────────────────────────────────────────────────
    st.markdown(f"**{len(filtered)} résultat(s)**")

    if filtered:
        import pandas as pd

        rows = []
        for c in filtered:
            rows.append({
                "ID":                c["id"],
                "Stagiaire":         c["stagiaire_nom"],
                "Département":       c.get("departement_nom","—"),
                "Mise en situation": c["mes_nom"],
                "Opération":         c["operation_nom"],
                "Date":              format_date(c["date_realisation"]),
                "Heure":             c.get("heure_realisation","—"),
                "Temps":             format_duration(c["temps_secondes"]),
                "Temps (s)":         round(c["temps_secondes"],1),
                "Saisie":            "Manuelle" if c.get("saisie_manuelle") else "Chrono",
            })

        df = pd.DataFrame(rows)

        # Pagination
        page_size = 20
        total_pages = max(1, (len(df) - 1) // page_size + 1)
        page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        start = (page_num - 1) * page_size
        st.dataframe(df.iloc[start:start+page_size], use_container_width=True, hide_index=True)

        # Export
        st.divider()
        ec1, ec2 = st.columns(2)
        with ec1:
            excel_data = export_chrono_to_excel(filtered)
            if excel_data:
                st.download_button(
                    "📥 Exporter Excel",
                    data=excel_data,
                    file_name="chronometrages_ima.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
        with ec2:
            # CSV simple
            csv = df.to_csv(index=False, sep=";", encoding="utf-8-sig")
            st.download_button(
                "📄 Exporter CSV",
                data=csv.encode("utf-8-sig"),
                file_name="chronometrages_ima.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("Aucun résultat pour les filtres sélectionnés.")
