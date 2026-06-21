"""
Page Statistiques — IMA
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import (get_stats_par_operation, get_stats_par_departement,
                      get_stats_par_mes, get_all_chronometrages, get_all_users)
from utils.helpers import format_duration


def show_statistiques():
    st.markdown("<div class='page-title'>📈 Statistiques & Analyse des Performances</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📊 Par opération",
        "🏭 Par département",
        "👥 Comparaison stagiaires",
    ])

    # ── Par opération ─────────────────────────────────────────────────────────
    with tab1:
        stats = get_stats_par_operation()
        if not stats:
            st.info("Aucune donnée disponible.")
        else:
            import pandas as pd

            df = pd.DataFrame(stats)
            df["Temps moyen"] = df["temps_moyen"].apply(format_duration)
            df["Temps min"]   = df["temps_min"].apply(format_duration)
            df["Temps max"]   = df["temps_max"].apply(format_duration)
            df["Écart (s)"]   = (df["temps_max"] - df["temps_min"]).round(1)

            # Bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Temps moyen",
                x=df["operation"],
                y=(df["temps_moyen"] / 60).round(2),
                marker_color="#1E3A5F",
            ))
            fig.add_trace(go.Bar(
                name="Temps min",
                x=df["operation"],
                y=(df["temps_min"] / 60).round(2),
                marker_color="#C8A951",
            ))
            fig.add_trace(go.Bar(
                name="Temps max",
                x=df["operation"],
                y=(df["temps_max"] / 60).round(2),
                marker_color="#dc3545",
                opacity=0.6,
            ))
            fig.update_layout(
                barmode="group",
                yaxis_title="Temps (minutes)",
                height=420,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1),
                margin=dict(l=10, r=10, t=40, b=60),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tableau
            st.dataframe(
                df[["operation","Temps moyen","Temps min","Temps max","Écart (s)","nb_mesures"]].rename(columns={
                    "operation":"Opération","nb_mesures":"Nb mesures"
                }),
                use_container_width=True, hide_index=True
            )

            # Opérations les plus longues
            st.markdown("#### 🔴 Top 3 opérations les plus longues")
            top3 = df.nlargest(3, "temps_moyen")[["operation","Temps moyen","nb_mesures"]]
            for _, row in top3.iterrows():
                st.markdown(f"- **{row['operation']}** : {row['Temps moyen']}  ({row['nb_mesures']} mesures)")

    # ── Par département ───────────────────────────────────────────────────────
    with tab2:
        stats_d = get_stats_par_departement()
        stats_m = get_stats_par_mes()

        if not stats_d:
            st.info("Aucune donnée disponible.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🏭 Temps moyen par département")
                fig2 = px.bar(
                    x=[r["departement"] for r in stats_d],
                    y=[round(r["temps_moyen"]/60, 2) for r in stats_d],
                    color=[r["departement"] for r in stats_d],
                    color_discrete_sequence=["#1E3A5F","#2E5D9A","#C8A951","#198754","#6f42c1"],
                    labels={"x":"Département","y":"Temps moyen (min)"},
                )
                fig2.update_layout(
                    showlegend=False, height=350,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig2, use_container_width=True)

            with col2:
                st.markdown("#### 📋 Temps moyen par mise en situation")
                if stats_m:
                    fig3 = px.bar(
                        x=[r["mise_en_situation"][:25] for r in stats_m],
                        y=[round(r["temps_moyen"]/60, 2) for r in stats_m],
                        labels={"x":"Mise en situation","y":"Temps moyen (min)"},
                        color_discrete_sequence=["#C8A951"],
                    )
                    fig3.update_layout(
                        height=350,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig3, use_container_width=True)

    # ── Comparaison stagiaires ────────────────────────────────────────────────
    with tab3:
        st.markdown("#### 👥 Comparaison des performances par stagiaire")
        chronos = get_all_chronometrages()
        if not chronos:
            st.info("Aucune donnée disponible.")
        else:
            import pandas as pd
            df = pd.DataFrame(chronos)

            # Grouper par stagiaire
            df_stag = (df.groupby("stagiaire_nom")
                        .agg(temps_moyen=("temps_secondes","mean"),
                             nb_mesures=("temps_secondes","count"))
                        .reset_index()
                        .sort_values("temps_moyen"))

            df_stag["Temps moyen"] = df_stag["temps_moyen"].apply(format_duration)

            fig4 = go.Figure(go.Bar(
                x=df_stag["stagiaire_nom"],
                y=(df_stag["temps_moyen"] / 60).round(2),
                marker_color=["#198754" if i < len(df_stag)//2 else "#dc3545"
                              for i in range(len(df_stag))],
                text=[f"{round(v,1)} min" for v in (df_stag["temps_moyen"]/60)],
                textposition="outside",
            ))
            fig4.update_layout(
                yaxis_title="Temps moyen (min)",
                xaxis_title="Stagiaire",
                height=400,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=20, b=60),
            )
            st.plotly_chart(fig4, use_container_width=True)

            # Analyse débutants vs expérimentés
            st.markdown("#### 📊 Analyse Débutant / Expérimenté")
            st.caption("Les stagiaires avec le plus de mesures sont considérés comme expérimentés.")

            median_nb = df_stag["nb_mesures"].median()
            debutants  = df_stag[df_stag["nb_mesures"] <= median_nb]
            experim    = df_stag[df_stag["nb_mesures"] >  median_nb]

            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown("**🟡 Débutants**")
                if len(debutants) > 0:
                    avg_deb = debutants["temps_moyen"].mean()
                    st.metric("Temps moyen", format_duration(avg_deb))
                    st.metric("Nombre", len(debutants))
                else:
                    st.info("—")
            with dc2:
                st.markdown("**🟢 Expérimentés**")
                if len(experim) > 0:
                    avg_exp = experim["temps_moyen"].mean()
                    st.metric("Temps moyen", format_duration(avg_exp))
                    st.metric("Nombre", len(experim))
                else:
                    st.info("—")

            if len(debutants) > 0 and len(experim) > 0:
                gain = ((debutants["temps_moyen"].mean() - experim["temps_moyen"].mean())
                        / debutants["temps_moyen"].mean() * 100)
                st.info(f"📉 Les stagiaires expérimentés sont **{gain:.1f}%** plus rapides que les débutants.")

            # Tableau comparatif
            st.dataframe(
                df_stag[["stagiaire_nom","Temps moyen","nb_mesures"]].rename(columns={
                    "stagiaire_nom":"Stagiaire","nb_mesures":"Nb mesures"
                }),
                use_container_width=True, hide_index=True
            )
