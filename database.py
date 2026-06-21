"""
Module de gestion de la base de données SQLite
Institut des Métiers de l'Aéronautique (IMA)
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = "ima_database.db"


def get_connection():
    """Retourne une connexion à la base de données avec support des clés étrangères."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    """Hash un mot de passe avec SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():
    """Initialise la base de données et crée toutes les tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Table des départements ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT    NOT NULL UNIQUE,
            description TEXT,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Table des utilisateurs ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nom            TEXT    NOT NULL,
            prenom         TEXT    NOT NULL,
            identifiant    TEXT    NOT NULL UNIQUE,
            mot_de_passe   TEXT    NOT NULL,
            role           TEXT    NOT NULL CHECK(role IN ('Administrateur','Formateur','Stagiaire')),
            departement_id INTEGER REFERENCES departements(id),
            statut         INTEGER NOT NULL DEFAULT 1,
            date_creation  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Table des mises en situation ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mises_en_situation (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nom            TEXT    NOT NULL,
            reference      TEXT    NOT NULL UNIQUE,
            departement_id INTEGER REFERENCES departements(id),
            description    TEXT,
            matiere        TEXT,
            observations   TEXT,
            date_creation  DATETIME DEFAULT CURRENT_TIMESTAMP,
            createur_id    INTEGER REFERENCES utilisateurs(id)
        )
    """)

    # ── Table des documents ─────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            mise_en_situation_id INTEGER NOT NULL REFERENCES mises_en_situation(id) ON DELETE CASCADE,
            type_document        TEXT    NOT NULL CHECK(type_document IN ('plan','fiche_instruction','fiche_autocontrole')),
            nom_fichier          TEXT    NOT NULL,
            chemin               TEXT    NOT NULL,
            date_upload          DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Table des opérations ────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT    NOT NULL UNIQUE,
            description TEXT,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Table de liaison mise_en_situation ↔ opérations ─────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mise_en_situation_operations (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            mise_en_situation_id INTEGER NOT NULL REFERENCES mises_en_situation(id) ON DELETE CASCADE,
            operation_id         INTEGER NOT NULL REFERENCES operations(id),
            ordre                INTEGER NOT NULL DEFAULT 1,
            UNIQUE(mise_en_situation_id, operation_id)
        )
    """)

    # ── Table des chronométrages ────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chronometrages (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            stagiaire_id         INTEGER NOT NULL REFERENCES utilisateurs(id),
            mise_en_situation_id INTEGER NOT NULL REFERENCES mises_en_situation(id),
            operation_id         INTEGER NOT NULL REFERENCES operations(id),
            temps_secondes       REAL    NOT NULL,
            date_realisation     DATE    DEFAULT (date('now')),
            heure_realisation    TIME    DEFAULT (time('now')),
            saisie_manuelle      INTEGER DEFAULT 0,
            saisi_par            INTEGER REFERENCES utilisateurs(id),
            commentaire          TEXT,
            date_enregistrement  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    _seed_initial_data(cursor, conn)
    conn.close()


def _seed_initial_data(cursor, conn):
    """Insère les données initiales si la base est vide."""

    # Départements
    departements = [
        ("Ajustage-Montage",  "Département spécialisé dans l'ajustage et montage de pièces aéronautiques"),
        ("Usinage CN",        "Département d'usinage à commande numérique"),
        ("Composite",         "Département de fabrication de pièces composites"),
        ("Chaudronnerie",     "Département de chaudronnerie et tôlerie"),
        ("Habillement",       "Département habillement et confection"),
    ]
    for nom, desc in departements:
        cursor.execute(
            "INSERT OR IGNORE INTO departements (nom, description) VALUES (?, ?)",
            (nom, desc)
        )

    # Administrateur par défaut
    cursor.execute(
        "SELECT id FROM utilisateurs WHERE identifiant = 'admin'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO utilisateurs (nom, prenom, identifiant, mot_de_passe, role, statut)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("Admin", "IMA", "admin", hash_password("admin123"), "Administrateur", 1))

    # Formateur démo
    cursor.execute(
        "SELECT id FROM utilisateurs WHERE identifiant = 'formateur1'")
    if not cursor.fetchone():
        cursor.execute("SELECT id FROM departements WHERE nom='Ajustage-Montage'")
        dept = cursor.fetchone()
        cursor.execute("""
            INSERT INTO utilisateurs (nom, prenom, identifiant, mot_de_passe, role, departement_id, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Benali", "Amine", "formateur1", hash_password("form123"), "Formateur", dept["id"] if dept else None, 1))

    # Stagiaire démo
    cursor.execute(
        "SELECT id FROM utilisateurs WHERE identifiant = 'stagiaire1'")
    if not cursor.fetchone():
        cursor.execute("SELECT id FROM departements WHERE nom='Ajustage-Montage'")
        dept = cursor.fetchone()
        cursor.execute("""
            INSERT INTO utilisateurs (nom, prenom, identifiant, mot_de_passe, role, departement_id, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Alami", "Ahmed", "stagiaire1", hash_password("stag123"), "Stagiaire", dept["id"] if dept else None, 1))

    # Opérations officielles IMA — Référentiel des opérations aéronautiques
    ops = [
        # ── Opérations principales ──────────────────────────────────────────
        ("OP001 — Débitage",
         "Découpe de la matière première aux dimensions souhaitées"),
        ("OP002 — Ajustage",
         "Ajustage et finition de la pièce : limage, ébavurage, rectification manuelle"),
        # ── OP003 Usinage — sous-opérations ────────────────────────────────
        ("OP003 — Usinage : Perçage",
         "Réalisation de trous cylindriques par perçage"),
        ("OP003 — Usinage : Alésage",
         "Usinage de précision de trous par alésage"),
        ("OP003 — Usinage : Fraisurage",
         "Usinage de surfaces planes ou de formes par fraisurage"),
        ("OP003 — Usinage : Lamage",
         "Réalisation de lamages pour logement de têtes de fixations"),
        # ── OP005 Assemblage — sous-opérations ─────────────────────────────
        ("OP005 — Assemblage : Accostage / Épinglage",
         "Mise en position et maintien des éléments avant assemblage définitif"),
        ("OP005 — Assemblage : Rivetage",
         "Assemblage permanent par rivetage"),
        # ── OP006 Contrôle ──────────────────────────────────────────────────
        ("OP006 — Auto-contrôle",
         "Vérification dimensionnelle réalisée par le stagiaire lui-même pendant la fabrication"),
        ("OP006 — Contrôle Final",
         "Contrôle dimensionnel et qualité final réalisé par le service contrôle"),
        # ── Procédés Spéciaux ───────────────────────────────────────────────
        ("PS — Peinture / Retouche",
         "Application de peinture ou retouche de surface"),
        ("PS — Calage",
         "Mise en place de cales pour ajustement de jeux fonctionnels"),
        ("PS — Alludine",
         "Traitement de surface par alludine (protection aluminium)"),
        ("PS — Métalisation",
         "Projection thermique de métal pour protection ou réparation de surface"),
        ("PS — Mastic",
         "Application de mastic d'étanchéité ou de protection"),
        ("PS — Couple de serrage",
         "Contrôle et application du couple de serrage réglementaire"),
        ("PS — Freinage",
         "Immobilisation des fixations par freinage (fil, vernis, etc.)"),
    ]
    for nom, desc in ops:
        cursor.execute(
            "INSERT OR IGNORE INTO operations (nom, description) VALUES (?, ?)",
            (nom, desc)
        )

    conn.commit()


# ── CRUD Utilisateurs ─────────────────────────────────────────────────────────

def get_all_users():
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.*, d.nom as departement_nom
        FROM utilisateurs u
        LEFT JOIN departements d ON u.departement_id = d.id
        ORDER BY u.date_creation DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT u.*, d.nom as departement_nom
        FROM utilisateurs u
        LEFT JOIN departements d ON u.departement_id = d.id
        WHERE u.id = ?
    """, (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(identifiant, password):
    conn = get_connection()
    row = conn.execute("""
        SELECT u.*, d.nom as departement_nom
        FROM utilisateurs u
        LEFT JOIN departements d ON u.departement_id = d.id
        WHERE u.identifiant = ? AND u.mot_de_passe = ? AND u.statut = 1
    """, (identifiant, hash_password(password))).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(nom, prenom, identifiant, password, role, departement_id=None):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO utilisateurs (nom, prenom, identifiant, mot_de_passe, role, departement_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nom, prenom, identifiant, hash_password(password), role, departement_id))
        conn.commit()
        return True, "Utilisateur créé avec succès."
    except sqlite3.IntegrityError:
        return False, "L'identifiant existe déjà."
    finally:
        conn.close()


def update_user(user_id, nom, prenom, role, departement_id, statut):
    conn = get_connection()
    conn.execute("""
        UPDATE utilisateurs SET nom=?, prenom=?, role=?, departement_id=?, statut=?
        WHERE id=?
    """, (nom, prenom, role, departement_id, statut, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM utilisateurs WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def reset_password(user_id, new_password):
    conn = get_connection()
    conn.execute(
        "UPDATE utilisateurs SET mot_de_passe=? WHERE id=?",
        (hash_password(new_password), user_id)
    )
    conn.commit()
    conn.close()


def toggle_user_status(user_id, statut):
    conn = get_connection()
    conn.execute("UPDATE utilisateurs SET statut=? WHERE id=?", (statut, user_id))
    conn.commit()
    conn.close()


# ── CRUD Départements ─────────────────────────────────────────────────────────

def get_all_departements():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM departements ORDER BY nom").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── CRUD Mises en situation ───────────────────────────────────────────────────

def get_all_mes():
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.*, d.nom as departement_nom,
               u.nom || ' ' || u.prenom as createur_nom
        FROM mises_en_situation m
        LEFT JOIN departements d ON m.departement_id = d.id
        LEFT JOIN utilisateurs u ON m.createur_id = u.id
        ORDER BY m.date_creation DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_mes_by_id(mes_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT m.*, d.nom as departement_nom
        FROM mises_en_situation m
        LEFT JOIN departements d ON m.departement_id = d.id
        WHERE m.id = ?
    """, (mes_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_mes(nom, reference, departement_id, description, matiere, observations, createur_id):
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO mises_en_situation
            (nom, reference, departement_id, description, matiere, observations, createur_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nom, reference, departement_id, description, matiere, observations, createur_id))
        conn.commit()
        return True, cursor.lastrowid
    except sqlite3.IntegrityError:
        return False, "La référence existe déjà."
    finally:
        conn.close()


def update_mes(mes_id, nom, reference, departement_id, description, matiere, observations):
    conn = get_connection()
    conn.execute("""
        UPDATE mises_en_situation
        SET nom=?, reference=?, departement_id=?, description=?, matiere=?, observations=?
        WHERE id=?
    """, (nom, reference, departement_id, description, matiere, observations, mes_id))
    conn.commit()
    conn.close()


def delete_mes(mes_id):
    conn = get_connection()
    conn.execute("DELETE FROM mises_en_situation WHERE id=?", (mes_id,))
    conn.commit()
    conn.close()


# ── CRUD Opérations ───────────────────────────────────────────────────────────

def get_all_operations():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM operations ORDER BY nom").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_operations_by_mes(mes_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.*, mso.ordre
        FROM operations o
        JOIN mise_en_situation_operations mso ON o.id = mso.operation_id
        WHERE mso.mise_en_situation_id = ?
        ORDER BY mso.ordre
    """, (mes_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_operation_to_mes(mes_id, operation_id, ordre):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO mise_en_situation_operations
            (mise_en_situation_id, operation_id, ordre)
            VALUES (?, ?, ?)
        """, (mes_id, operation_id, ordre))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def remove_operation_from_mes(mes_id, operation_id):
    conn = get_connection()
    conn.execute("""
        DELETE FROM mise_en_situation_operations
        WHERE mise_en_situation_id=? AND operation_id=?
    """, (mes_id, operation_id))
    conn.commit()
    conn.close()


def create_operation(nom, description):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO operations (nom, description) VALUES (?, ?)",
            (nom, description)
        )
        conn.commit()
        return True, "Opération créée."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ── Documents ─────────────────────────────────────────────────────────────────

def save_document(mes_id, type_doc, nom_fichier, chemin):
    conn = get_connection()
    conn.execute("""
        INSERT INTO documents (mise_en_situation_id, type_document, nom_fichier, chemin)
        VALUES (?, ?, ?, ?)
    """, (mes_id, type_doc, nom_fichier, chemin))
    conn.commit()
    conn.close()


def get_documents_by_mes(mes_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM documents WHERE mise_en_situation_id=?", (mes_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_document(doc_id):
    conn = get_connection()
    row = conn.execute("SELECT chemin FROM documents WHERE id=?", (doc_id,)).fetchone()
    if row and os.path.exists(row["chemin"]):
        os.remove(row["chemin"])
    conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()


# ── Chronométrages ────────────────────────────────────────────────────────────

def save_chronometrage(stagiaire_id, mes_id, operation_id, temps_secondes,
                       saisie_manuelle=False, saisi_par=None, commentaire=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO chronometrages
        (stagiaire_id, mise_en_situation_id, operation_id, temps_secondes,
         saisie_manuelle, saisi_par, commentaire)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (stagiaire_id, mes_id, operation_id, temps_secondes,
          1 if saisie_manuelle else 0, saisi_par, commentaire))
    conn.commit()
    conn.close()


def get_all_chronometrages(stagiaire_id=None, mes_id=None, operation_id=None):  # noqa
    conn = get_connection()
    query = """
        SELECT c.*,
               u.nom || ' ' || u.prenom AS stagiaire_nom,
               d.nom AS departement_nom,
               m.nom AS mes_nom,
               o.nom AS operation_nom
        FROM chronometrages c
        JOIN utilisateurs u  ON c.stagiaire_id = u.id
        LEFT JOIN departements d ON u.departement_id = d.id
        JOIN mises_en_situation m ON c.mise_en_situation_id = m.id
        JOIN operations o ON c.operation_id = o.id
        WHERE 1=1
    """
    params = []
    if stagiaire_id:
        query += " AND c.stagiaire_id = ?"
        params.append(stagiaire_id)
    if mes_id:
        query += " AND c.mise_en_situation_id = ?"
        params.append(mes_id)
    if operation_id:
        query += " AND c.operation_id = ?"
        params.append(operation_id)
    query += " ORDER BY c.date_enregistrement DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats_par_operation():
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.nom AS operation,
               AVG(c.temps_secondes) AS temps_moyen,
               MIN(c.temps_secondes) AS temps_min,
               MAX(c.temps_secondes) AS temps_max,
               COUNT(*)              AS nb_mesures
        FROM chronometrages c
        JOIN operations o ON c.operation_id = o.id
        GROUP BY o.id
        ORDER BY temps_moyen DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats_par_departement():
    conn = get_connection()
    rows = conn.execute("""
        SELECT d.nom AS departement,
               AVG(c.temps_secondes) AS temps_moyen,
               COUNT(*)              AS nb_mesures
        FROM chronometrages c
        JOIN utilisateurs u ON c.stagiaire_id = u.id
        JOIN departements d ON u.departement_id = d.id
        GROUP BY d.id
        ORDER BY temps_moyen DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats_par_mes():
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.nom AS mise_en_situation,
               AVG(c.temps_secondes) AS temps_moyen,
               COUNT(*)              AS nb_mesures
        FROM chronometrages c
        JOIN mises_en_situation m ON c.mise_en_situation_id = m.id
        GROUP BY m.id
        ORDER BY temps_moyen DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_global_kpis():
    conn = get_connection()
    nb_stagiaires  = conn.execute("SELECT COUNT(*) FROM utilisateurs WHERE role='Stagiaire' AND statut=1").fetchone()[0]
    nb_formateurs  = conn.execute("SELECT COUNT(*) FROM utilisateurs WHERE role='Formateur' AND statut=1").fetchone()[0]
    nb_mes         = conn.execute("SELECT COUNT(*) FROM mises_en_situation").fetchone()[0]
    nb_chrono      = conn.execute("SELECT COUNT(*) FROM chronometrages").fetchone()[0]
    avg_global     = conn.execute("SELECT AVG(temps_secondes) FROM chronometrages").fetchone()[0]
    conn.close()
    return {
        "nb_stagiaires": nb_stagiaires,
        "nb_formateurs": nb_formateurs,
        "nb_mes":        nb_mes,
        "nb_chrono":     nb_chrono,
        "temps_moyen":   avg_global or 0,
    }