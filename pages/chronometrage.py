"""
Page Chronométrage — IMA
Correction : stockage des sélections dans session_state pour éviter les bugs de rerun
"""

import streamlit as st
import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import (get_all_mes, get_operations_by_mes, save_chronometrage,
                      get_all_users, get_all_chronometrages, get_all_departements)
from utils.helpers import format_duration


def show_chronometrage():
    user = st.session_state["user"]
    role = user["role"]

    st.markdown("<div class='page-title'>⏱️ Chronométrage des Opérations</div>",
                unsafe_allow_html=True)

    if role in ("Administrateur", "Formateur"):
        tab1, tab2 = st.tabs(["⏱️ Chronomètre", "✍️ Saisie manuelle"])
    else:
        tab1 = st.tabs(["⏱️ Chronomètre"])[0]

    # ════════════════════════════════════════════════════════
    # ONGLET CHRONOMÈTRE
    # ════════════════════════════════════════════════════════
    with tab1:

        # Init session_state chrono
        defaults = {
            "cr": False, "cs": None, "ce": 0.0,
            "csaved": False, "show_result": False,
            "saved_stag_id": None, "saved_mes_id": None, "saved_op_id": None,
            "saved_dept": None, "saved_mes_nom": None,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

        # ── ÉTAPE 1 : Sélections ──────────────────────────────────────────
        st.markdown("### 📋 Étape 1 — Sélection")

        depts    = get_all_departements()
        mes_list = get_all_mes()

        # Désactiver les sélections si chrono en cours ou enregistré
        locked = st.session_state["cr"] or st.session_state["csaved"]
        if locked:
            st.info("🔒 Sélections verrouillées pendant le chronométrage. Réinitialisez pour changer.")

        col1, col2 = st.columns(2)

        # Stagiaire
        if role in ("Administrateur", "Formateur"):
            with col1:
                stags     = [u for u in get_all_users() if u["role"] == "Stagiaire" and u["statut"] == 1]
                if not stags:
                    st.warning("Aucun stagiaire actif.")
                    return
                stag_noms = [f"{u['prenom']} {u['nom']}" for u in stags]
                sel_stag  = st.selectbox("👤 Stagiaire", stag_noms, disabled=locked)
                stag_id   = next(u["id"] for u in stags if f"{u['prenom']} {u['nom']}" == sel_stag)
        else:
            stag_id = user["id"]
            st.info(f"👤 **{user['prenom']} {user['nom']}**")

        # Département
        with (col2 if role in ("Administrateur","Formateur") else col1):
            dept_noms = [d["nom"] for d in depts]
            sel_dept  = st.selectbox("🏭 Département", dept_noms, disabled=locked)
            dept_obj  = next(d for d in depts if d["nom"] == sel_dept)

        # MES filtrées par département
        mes_dept = [m for m in mes_list if m.get("departement_id") == dept_obj["id"]]

        col3, col4 = st.columns(2)
        with col3:
            if not mes_dept:
                st.warning(f"⚠️ Aucune mise en situation dans **{sel_dept}**.")
                return
            mes_noms  = [f"{m['nom']}  —  {m['reference']}" for m in mes_dept]
            sel_mes_n = st.selectbox("📋 Mise en situation", mes_noms, disabled=locked)
            sel_mes   = next(m for m in mes_dept if f"{m['nom']}  —  {m['reference']}" == sel_mes_n)

        with col4:
            ops = get_operations_by_mes(sel_mes["id"])
            if not ops:
                st.warning("⚠️ Aucune opération associée à cette mise en situation.")
                return
            op_noms  = [f"{op['ordre']}. {op['nom']}" for op in ops]
            sel_op_n = st.selectbox("⚙️ Opération", op_noms, disabled=locked,
                                     key="selectbox_operation")
            sel_op   = next(op for op in ops if f"{op['ordre']}. {op['nom']}" == sel_op_n)

        commentaire = st.text_area("💬 Commentaire (optionnel)", height=80,
                                   disabled=locked)

        st.divider()

        # ── ÉTAPE 2 : Chronomètre ────────────────────────────────────────
        st.markdown("### ⏱️ Étape 2 — Chronomètre")

        # Calcul du temps affiché
        if st.session_state["cr"]:
            elapsed   = time.time() - st.session_state["cs"] + st.session_state["ce"]
            css_class = "chrono-display chrono-running"
        else:
            elapsed   = st.session_state["ce"]
            css_class = "chrono-display"

        h, rem = divmod(int(elapsed), 3600)
        m_val, s = divmod(rem, 60)

        _, col_c, _ = st.columns([1, 2, 1])
        with col_c:
            st.markdown(
                f"<div class='{css_class}'>{h:02d}:{m_val:02d}:{s:02d}</div>",
                unsafe_allow_html=True
            )
            st.markdown("<br/>", unsafe_allow_html=True)

            b1, b2, b3 = st.columns(3)

            with b1:
                lbl = "▶️ Démarrer" if not st.session_state["cr"] else "⏸️ Pause"
                if st.button(lbl, type="primary", use_container_width=True,
                             disabled=st.session_state["csaved"], key="btn_start"):
                    if not st.session_state["cr"]:
                        # Mémoriser les sélections au moment du démarrage
                        st.session_state["saved_stag_id"]  = stag_id
                        st.session_state["saved_mes_id"]   = sel_mes["id"]
                        st.session_state["saved_op_id"]    = sel_op["id"]
                        st.session_state["saved_dept"]     = sel_dept
                        st.session_state["saved_mes_nom"]  = sel_mes["nom"]
                        st.session_state["cr"]             = True
                        st.session_state["cs"]             = time.time()
                        st.session_state["csaved"]         = False
                        st.session_state["show_result"]    = False
                    else:
                        st.session_state["ce"] += time.time() - st.session_state["cs"]
                        st.session_state["cr"]  = False
                        st.session_state["cs"]  = None
                    st.rerun()

            with b2:
                if st.button("⏹️ Arrêter", use_container_width=True,
                             disabled=not (st.session_state["cr"] or st.session_state["ce"] > 0),
                             key="btn_stop"):
                    if st.session_state["cr"]:
                        st.session_state["ce"] += time.time() - st.session_state["cs"]
                        st.session_state["cr"]  = False
                        st.session_state["cs"]  = None
                    st.rerun()

            with b3:
                if st.button("🔄 Réinitialiser", use_container_width=True, key="btn_reset"):
                    for k, v in defaults.items():
                        st.session_state[k] = v
                    st.rerun()

        # Auto-refresh si chrono actif
        if st.session_state["cr"]:
            time.sleep(1)
            st.rerun()

        # ── ÉTAPE 3 : Enregistrement ─────────────────────────────────────
        final_time = st.session_state["ce"]

        if final_time > 0 and not st.session_state["cr"]:
            st.divider()
            st.markdown("### 💾 Étape 3 — Enregistrement")

            # Récupérer les valeurs mémorisées au démarrage
            saved_stag_id = st.session_state.get("saved_stag_id") or stag_id
            saved_mes_id  = st.session_state.get("saved_mes_id")  or sel_mes["id"]
            saved_op_id   = st.session_state.get("saved_op_id")   or sel_op["id"]

            # Afficher le récapitulatif de ce qui va être enregistré
            saved_op_nom  = next((op["nom"] for op in ops if op["id"] == saved_op_id), sel_op["nom"])
            saved_mes_nom = st.session_state.get("saved_mes_nom", sel_mes["nom"])

            _, col_save, _ = st.columns([1, 2, 1])
            with col_save:
                st.markdown(f"""
                <div style='background:#f0f4ff;border:2px solid #1E3A5F;border-radius:12px;
                            padding:1.2rem;margin-bottom:1rem;'>
                    <div style='text-align:center;font-size:2rem;font-weight:800;color:#C8A951;
                                font-family:monospace;margin-bottom:.8rem;'>
                        ⏱️ {format_duration(final_time)}
                    </div>
                    <div style='font-size:.85rem;color:#1E3A5F;'>
                        <div>📋 <strong>Mise en situation :</strong> {saved_mes_nom}</div>
                        <div>⚙️ <strong>Opération :</strong> {saved_op_nom}</div>
                        <div>🏭 <strong>Département :</strong> {st.session_state.get("saved_dept", sel_dept)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if not st.session_state["csaved"]:
                    if st.button("💾 Enregistrer ce temps", type="primary",
                                 use_container_width=True, key="btn_save"):
                        save_chronometrage(
                            stagiaire_id    = saved_stag_id,
                            mes_id          = saved_mes_id,
                            operation_id    = saved_op_id,
                            temps_secondes  = final_time,
                            saisie_manuelle = False,
                            saisi_par       = user["id"],
                            commentaire     = commentaire or None,
                        )
                        st.session_state["csaved"]      = True
                        st.session_state["show_result"] = True
                        st.rerun()
                else:
                    st.success("✅ Temps enregistré avec succès !")
                    st.info("👉 Cliquez sur **Réinitialiser** pour chronométrer une autre opération.")

        # ── ÉTAPE 4 : Tableau récapitulatif ──────────────────────────────
        if st.session_state.get("show_result") and st.session_state.get("saved_mes_id"):
            st.divider()
            st.markdown("### 📊 Étape 4 — Récapitulatif de la mise en situation")

            mes_id_recap  = st.session_state["saved_mes_id"]
            stag_id_recap = st.session_state["saved_stag_id"]
            mes_recap     = next((m for m in mes_list if m["id"] == mes_id_recap), None)
            ops_recap     = get_operations_by_mes(mes_id_recap)

            if mes_recap and ops_recap:
                st.markdown(f"""
                <div style='background:#1E3A5F;color:white;padding:1rem 1.5rem;
                            border-radius:12px;margin-bottom:1rem;'>
                    <div style='font-size:1.1rem;font-weight:700;'>📋 {mes_recap["nom"]}</div>
                    <div style='font-size:.83rem;opacity:.8;margin-top:.3rem;'>
                        Réf : {mes_recap["reference"]} &nbsp;|&nbsp;
                        Département : {mes_recap.get("departement_nom","—")} &nbsp;|&nbsp;
                        Matière : {mes_recap.get("matiere","—")}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Chronos du stagiaire pour cette MES
                chronos_stag = get_all_chronometrages(
                    stagiaire_id = stag_id_recap,
                    mes_id       = mes_id_recap,
                )
                # Indexer par operation_id → prendre le plus récent
                chrono_par_op = {}
                for c in chronos_stag:
                    oid = c["operation_id"]
                    if oid not in chrono_par_op:
                        chrono_par_op[oid] = c

                import pandas as pd
                rows = []
                for op in ops_recap:
                    c = chrono_par_op.get(op["id"])
                    if c:
                        tps_fmt = format_duration(c["temps_secondes"])
                        statut  = "✅ Réalisé"
                        date_r  = c.get("date_realisation", "—")
                    else:
                        tps_fmt = "—"
                        statut  = "⏳ Non réalisé"
                        date_r  = "—"

                    # Moyenne tous stagiaires pour cette opération
                    all_c = get_all_chronometrages(operation_id=op["id"])
                    moy   = format_duration(sum(x["temps_secondes"] for x in all_c) / len(all_c)) if all_c else "—"

                    rows.append({
                        "N°":                  op["ordre"],
                        "Opération":           op["nom"],
                        "Statut":              statut,
                        "Temps réalisé":       tps_fmt,
                        "Temps moyen groupe":  moy,
                        "Date":                date_r,
                    })

                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                # Mini résumé
                realises = sum(1 for r in rows if "✅" in r["Statut"])
                st.markdown(f"""
                <div style='display:flex;gap:1rem;margin-top:1rem;flex-wrap:wrap;'>
                    <div style='background:#d1e7dd;border-radius:10px;padding:.8rem 1.5rem;flex:1;text-align:center;'>
                        <div style='font-size:1.6rem;font-weight:800;color:#0a3622;'>{realises}/{len(ops_recap)}</div>
                        <div style='font-size:.8rem;color:#0a3622;'>Opérations réalisées</div>
                    </div>
                    <div style='background:#fff3cd;border-radius:10px;padding:.8rem 1.5rem;flex:1;text-align:center;'>
                        <div style='font-size:1.1rem;font-weight:800;color:#664d03;'>{mes_recap["reference"]}</div>
                        <div style='font-size:.8rem;color:#664d03;'>Référence pièce</div>
                    </div>
                    <div style='background:#cfe2ff;border-radius:10px;padding:.8rem 1.5rem;flex:1;text-align:center;'>
                        <div style='font-size:1.1rem;font-weight:800;color:#084298;'>{st.session_state.get("saved_dept","—")}</div>
                        <div style='font-size:.8rem;color:#084298;'>Département</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # ONGLET SAISIE MANUELLE
    # ════════════════════════════════════════════════════════
    if role in ("Administrateur", "Formateur"):
        with tab2:
            st.markdown("#### ✍️ Saisie manuelle d'un temps")
            depts    = get_all_departements()
            mes_list = get_all_mes()
            stags    = [u for u in get_all_users() if u["role"] == "Stagiaire" and u["statut"] == 1]

            with st.form("manual_form"):
                mc1, mc2 = st.columns(2)
                with mc1:
                    stag_noms_m = [f"{u['prenom']} {u['nom']}" for u in stags]
                    sel_stag_m  = st.selectbox("👤 Stagiaire *", stag_noms_m)
                    stag_id_m   = next((u["id"] for u in stags
                                        if f"{u['prenom']} {u['nom']}" == sel_stag_m), None)

                    dept_noms_m  = [d["nom"] for d in depts]
                    sel_dept_m_n = st.selectbox("🏭 Département *", dept_noms_m)
                    dept_m       = next(d for d in depts if d["nom"] == sel_dept_m_n)
                    mes_dept_m   = [m for m in mes_list
                                    if m.get("departement_id") == dept_m["id"]]

                with mc2:
                    if mes_dept_m:
                        mes_noms_m  = [f"{m['nom']} — {m['reference']}" for m in mes_dept_m]
                        sel_mes_m_n = st.selectbox("📋 Mise en situation *", mes_noms_m)
                        sel_mes_m   = next(m for m in mes_dept_m
                                           if f"{m['nom']} — {m['reference']}" == sel_mes_m_n)
                        ops_m       = get_operations_by_mes(sel_mes_m["id"])
                        op_noms_m   = [f"{op['ordre']}. {op['nom']}" for op in ops_m]
                        sel_op_m_n  = st.selectbox("⚙️ Opération *",
                                                    op_noms_m if op_noms_m else ["(aucune)"])
                        sel_op_m    = next((op for op in ops_m
                                            if f"{op['ordre']}. {op['nom']}" == sel_op_m_n), None)
                    else:
                        st.warning("Aucune mise en situation dans ce département.")
                        sel_mes_m = None; sel_op_m = None

                    st.markdown("**⏱️ Temps mesuré**")
                    t1, t2, t3 = st.columns(3)
                    with t1: mm_h = st.number_input("Heures",   0, 23, 0)
                    with t2: mm_m = st.number_input("Minutes",  0, 59, 0)
                    with t3: mm_s = st.number_input("Secondes", 0, 59, 0)

                mm_comment = st.text_area("💬 Commentaire", height=80)

                if st.form_submit_button("💾 Enregistrer", type="primary",
                                          use_container_width=True):
                    total = mm_h * 3600 + mm_m * 60 + mm_s
                    if not stag_id_m:
                        st.error("Sélectionnez un stagiaire.")
                    elif not sel_mes_m or not sel_op_m:
                        st.error("Sélectionnez une mise en situation et une opération.")
                    elif total == 0:
                        st.error("Le temps doit être supérieur à 0.")
                    else:
                        save_chronometrage(
                            stagiaire_id    = stag_id_m,
                            mes_id          = sel_mes_m["id"],
                            operation_id    = sel_op_m["id"],
                            temps_secondes  = total,
                            saisie_manuelle = True,
                            saisi_par       = user["id"],
                            commentaire     = mm_comment or None,
                        )
                        st.success(f"✅ {format_duration(total)} enregistré pour "
                                   f"**{sel_op_m['nom']}**")