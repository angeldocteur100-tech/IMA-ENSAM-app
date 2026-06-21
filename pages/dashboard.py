"""
Page Tableau de Bord — IMA
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_global_kpis, get_stats_par_operation, get_stats_par_departement, get_stats_par_mes, get_all_chronometrages
from utils.helpers import format_duration, format_datetime


def kpi_card(value, label, icon, color="#1E3A5F"):
    st.markdown(f"""
    <div class='kpi-card' style='border-left-color:{color};'>
        <div style='font-size:1.8rem;'>{icon}</div>
        <div class='kpi-value' style='color:{color};'>{value}</div>
        <div class='kpi-label'>{label}</div>
    </div>
    """, unsafe_allow_html=True)


def show_dashboard():
    st.markdown("<div class='page-title'>🏠 Tableau de Bord</div>", unsafe_allow_html=True)

    kpis       = get_global_kpis()
    stats_ops  = get_stats_par_operation()
    stats_dept = get_stats_par_departement()
    stats_mes  = get_stats_par_mes()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card(kpis["nb_stagiaires"], "Stagiaires actifs",    "🎓", "#1E3A5F")
    with c2: kpi_card(kpis["nb_formateurs"], "Formateurs actifs",    "👨‍🏫", "#2E5D9A")
    with c3: kpi_card(kpis["nb_mes"],        "Mises en situation",   "📋", "#C8A951")
    with c4: kpi_card(kpis["nb_chrono"],     "Chronométrages",       "⏱️", "#198754")
    with c5: kpi_card(format_duration(kpis["temps_moyen"]), "Temps moyen global", "📊", "#6f42c1")

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Graphiques ligne 1 ────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### ⏱️ Temps moyen par opération")
        if stats_ops:
            ops    = [r["operation"]   for r in stats_ops]
            moyens = [round(r["temps_moyen"] / 60, 2) for r in stats_ops]
            fig = go.Figure(go.Bar(
                x=moyens, y=ops, orientation="h",
                marker_color="#1E3A5F",
                text=[f"{m} min" for m in moyens],
                textposition="outside",
            ))
            fig.update_layout(
                xaxis_title="Temps moyen (min)",
                yaxis=dict(autorange="reversed"),
                height=350,
                margin=dict(l=10, r=30, t=20, b=30),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

    with col_b:
        st.markdown("#### 🏭 Temps moyen par département")
        if stats_dept:
            fig2 = px.pie(
                values=[r["temps_moyen"] for r in stats_dept],
                names=[r["departement"]  for r in stats_dept],
                color_discrete_sequence=["#1E3A5F", "#2E5D9A", "#C8A951", "#198754", "#6f42c1"],
                hole=0.4,
            )
            fig2.update_traces(textinfo="percent+label")
            fig2.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

    # ── Graphiques ligne 2 ────────────────────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("#### 📋 Temps moyen par mise en situation")
        if stats_mes:
            labels  = [r["mise_en_situation"][:30] for r in stats_mes]
            valeurs = [round(r["temps_moyen"] / 60, 2)  for r in stats_mes]
            fig3 = go.Figure(go.Bar(
                x=labels, y=valeurs,
                marker_color="#C8A951",
                text=[f"{v} min" for v in valeurs],
                textposition="outside",
            ))
            fig3.update_layout(
                yaxis_title="Temps moyen (min)",
                height=320,
                margin=dict(l=10, r=10, t=20, b=60),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

    with col_d:
        st.markdown("#### 📈 Historique des chronométrages (7 derniers jours)")
        chronos = get_all_chronometrages()
        if chronos:
            import pandas as pd
            df = pd.DataFrame(chronos)
            df["date_realisation"] = pd.to_datetime(df["date_realisation"])
            df_grouped = df.groupby("date_realisation").size().reset_index(name="nb")
            fig4 = go.Figure(go.Scatter(
                x=df_grouped["date_realisation"],
                y=df_grouped["nb"],
                mode="lines+markers",
                line=dict(color="#1E3A5F", width=2.5),
                marker=dict(size=7, color="#C8A951"),
                fill="tozeroy",
                fillcolor="rgba(30,58,95,0.1)",
            ))
            fig4.update_layout(
                yaxis_title="Nombre de mesures",
                height=320,
                margin=dict(l=10, r=10, t=20, b=30),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

    # ── Top opérations ────────────────────────────────────────────────────────
    if stats_ops:
        st.markdown("#### 🏆 Classement des opérations les plus longues")
        import pandas as pd
        df_ops = pd.DataFrame(stats_ops)
        df_ops["Temps moyen"]  = df_ops["temps_moyen"].apply(format_duration)
        df_ops["Temps min"]    = df_ops["temps_min"].apply(format_duration)
        df_ops["Temps max"]    = df_ops["temps_max"].apply(format_duration)
        df_ops["Nb mesures"]   = df_ops["nb_mesures"]
        df_ops = df_ops.rename(columns={"operation": "Opération"})
        st.dataframe(
            df_ops[["Opération", "Temps moyen", "Temps min", "Temps max", "Nb mesures"]],
            use_container_width=True, hide_index=True
        )
