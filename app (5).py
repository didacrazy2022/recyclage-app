"""
Dabouza : prototype Streamlit.
Met en relation les familles qui trient leur plastique et les collecteurs (barbechas).
"""

import base64
import math
import random
import sqlite3
import string
from datetime import datetime

import pandas as pd
import streamlit as st

# ---------------- Identité de l'application ----------------
# Pour changer le nom, modifie seulement ces lignes.
APP_NAME = "Dabouza"
SLOGAN_AR = "ما ترميهاش... رجّعها"
SLOGAN_FR = "Ne jette plus tes bouteilles en plastique : quelqu'un près de chez toi vient les chercher."

VERT = "#1F6F50"
ORANGE = "#E07A3F"
CREME = "#F4EFE6"

LOGO_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
<circle cx="60" cy="60" r="58" fill="{CREME}"/>
<path d="M33.1 86.9 A38 38 0 1 1 86.9 86.9" fill="none" stroke="{ORANGE}" stroke-width="7" stroke-linecap="round"/>
<polygon points="81.2,92.6 93.2,90.4 83.4,80.6" fill="{ORANGE}"/>
<rect x="53" y="25" width="14" height="8" rx="2" fill="{VERT}"/>
<path d="M54 33 H66 V40 C66 44 74 46 74 54 V86 C74 90 71 93 67 93 H53 C49 93 46 90 46 86 V54 C46 46 54 44 54 40 Z" fill="{VERT}"/>
<rect x="46" y="60" width="28" height="14" fill="{CREME}"/>
<path d="M49 67 q4 -4 8 0 t8 0 t8 0" fill="none" stroke="{ORANGE}" stroke-width="2.2" stroke-linecap="round"/>
<rect x="50" y="47" width="3" height="10" rx="1.5" fill="#ffffff" opacity="0.35"/>
<rect x="50" y="78" width="3" height="9" rx="1.5" fill="#ffffff" opacity="0.35"/>
</svg>"""


def logo_html(taille):
    b64 = base64.b64encode(LOGO_SVG.encode("utf-8")).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{taille}" alt="{APP_NAME}">'


st.set_page_config(page_title=APP_NAME, page_icon="🧴", layout="centered")

st.markdown(
    f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+Bhaijaan+2:wght@500;700&family=Rubik:wght@400;500&display=swap');
.stApp, .stMarkdown, button, input, textarea {{ font-family: 'Rubik', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Baloo Bhaijaan 2', sans-serif !important; color: {VERT} !important; }}
.hero {{ text-align: center; padding: 0.5rem 0 1rem; }}
.hero .nom {{ font-family: 'Baloo Bhaijaan 2', sans-serif; font-size: 3.4rem; font-weight: 700; color: {VERT}; line-height: 1.1; margin-top: 0.3rem; }}
.hero .ar {{ font-family: 'Baloo Bhaijaan 2', sans-serif; font-size: 1.6rem; color: {ORANGE}; direction: rtl; }}
.hero .fr {{ font-size: 1.1rem; color: #555; max-width: 520px; margin: 0.3rem auto 0; }}
.bloc {{ background: {CREME}; color: #2b2b2b; border-radius: 14px; padding: 1.1rem 1.3rem; margin: 0.7rem 0; line-height: 1.6; }}
.carte {{ background: #ffffff; color: #2b2b2b; border: 1px solid #E6DED0; border-radius: 14px; padding: 1rem; min-height: 170px; }}
.carte .titre {{ font-family: 'Baloo Bhaijaan 2', sans-serif; font-size: 1.2rem; font-weight: 700; color: {VERT}; margin-bottom: 0.3rem; }}
.etape {{ display: flex; gap: 0.9rem; align-items: flex-start; margin: 0.7rem 0; }}
.etape .num {{ background: {VERT}; color: #fff; border-radius: 50%; min-width: 2.1rem; height: 2.1rem; display: flex; align-items: center; justify-content: center; font-weight: 700; }}
.pied {{ text-align: center; color: #888; font-size: 0.85rem; margin-top: 2rem; }}
</style>""",
    unsafe_allow_html=True,
)

DB_PATH = "recyclage.db"

# Coordonnées approximatives du centre de chaque quartier
QUARTIERS = {
    "Tunis Centre": (36.8008, 10.1800),
    "Lafayette": (36.8145, 10.1813),
    "Le Bardo": (36.8092, 10.1340),
    "El Menzah": (36.8400, 10.1700),
    "Ennasr": (36.8580, 10.1640),
    "Ariana": (36.8625, 10.1956),
    "Les Berges du Lac": (36.8340, 10.2330),
    "Le Kram": (36.8330, 10.3160),
    "Carthage": (36.8528, 10.3233),
    "La Marsa": (36.8782, 10.3247),
    "Ben Arous": (36.7531, 10.2189),
    "La Manouba": (36.8081, 10.0972),
}

TAILLES = {
    "Petit": {"description": "environ 15 à 20 bouteilles", "points": 5, "kg": 1.0},
    "Moyen": {"description": "un sac poubelle à moitié plein", "points": 10, "kg": 2.5},
    "Grand": {"description": "un grand sac poubelle plein", "points": 20, "kg": 5.0},
}

MATIERES = ["Bouteilles plastique (PET)", "Autres plastiques", "Canettes", "Carton"]

STATUTS = {
    "disponible": "Statut : disponible",
    "reserve": "Statut : réservé par un collecteur",
    "collecte": "Statut : récupéré",
}

MAX_RESERVATIONS = 10


# ---------------- Base de données ----------------

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_resource
def init_db():
    conn = connect()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            quartier TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS bags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            size TEXT NOT NULL,
            materials TEXT,
            quartier TEXT NOT NULL,
            address TEXT NOT NULL,
            note TEXT,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            photo BLOB,
            code TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'disponible',
            collector_id INTEGER,
            created_at TEXT NOT NULL,
            collected_at TEXT
        )"""
    )
    conn.commit()
    conn.close()
    return True


def query(sql, params=()):
    conn = connect()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Exécute une modification et renvoie le nombre de lignes touchées."""
    conn = connect()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


# ---------------- Outils ----------------

def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def normalize_phone(phone):
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("216") and len(digits) == 11:
        digits = digits[3:]
    return digits


def distance_km(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def position_quartier(quartier):
    """Position approximative dans le quartier (légèrement décalée pour ne pas superposer les points)."""
    lat, lon = QUARTIERS[quartier]
    return lat + random.uniform(-0.006, 0.006), lon + random.uniform(-0.006, 0.006)


def nouveau_code():
    return "".join(random.choices(string.digits, k=4))


def flash(message):
    st.session_state["flash"] = message


def afficher_flash():
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))


def bilan(sizes):
    return {
        "sacs": len(sizes),
        "kg": sum(TAILLES[s]["kg"] for s in sizes),
        "points": sum(TAILLES[s]["points"] for s in sizes),
    }


def stats_globales():
    sizes = [r["size"] for r in query("SELECT size FROM bags WHERE status='collecte'")]
    b = bilan(sizes)
    b["participants"] = query_one("SELECT COUNT(*) AS n FROM users")["n"]
    return b


def ajouter_donnees_demo():
    familles = [("Salma", "90000001", "La Marsa"), ("Karim", "90000002", "Ariana"), ("Amel", "90000003", "Le Bardo")]
    for name, phone, quartier in familles:
        if not query_one("SELECT id FROM users WHERE phone=?", (phone,)):
            execute(
                "INSERT INTO users (name, phone, role, quartier, created_at) VALUES (?,?,?,?,?)",
                (name, phone, "famille", quartier, now()),
            )
        family = query_one("SELECT id FROM users WHERE phone=?", (phone,))
        for _ in range(2):
            lat, lon = position_quartier(quartier)
            execute(
                """INSERT INTO bags (family_id, size, materials, quartier, address, note, lat, lon, code, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (family["id"], random.choice(list(TAILLES)), MATIERES[0], quartier,
                 "Adresse de démonstration", "Sac devant la porte", lat, lon, nouveau_code(), now()),
            )


# ---------------- Connexion ----------------

def sidebar_connexion():
    st.sidebar.markdown(f'<div style="text-align:center">{logo_html(70)}<h2 style="margin:0">{APP_NAME}</h2></div>', unsafe_allow_html=True)
    st.sidebar.subheader("Connexion")

    user = None
    if "user_id" in st.session_state:
        user = query_one("SELECT * FROM users WHERE id=?", (st.session_state.user_id,))

    if user:
        role_label = "Famille" if user["role"] == "famille" else "Collecteur"
        st.sidebar.success(f"Connecté : {user['name']} ({role_label})")
        st.sidebar.caption(f"Quartier : {user['quartier']}")
        if st.sidebar.button("Se déconnecter"):
            st.session_state.pop("user_id", None)
            st.rerun()
        return user

    st.sidebar.caption("Prototype : pas de code SMS, le numéro sert d'identifiant.")
    phone = normalize_phone(st.sidebar.text_input("Numéro de téléphone", placeholder="ex. 22123456"))

    if phone:
        if len(phone) != 8:
            st.sidebar.warning("Le numéro doit contenir 8 chiffres.")
        else:
            existing = query_one("SELECT * FROM users WHERE phone=?", (phone,))
            if existing:
                st.sidebar.info(f"Bon retour {existing['name']} !")
                if st.sidebar.button("Se connecter", type="primary"):
                    st.session_state.user_id = existing["id"]
                    st.rerun()
            else:
                st.sidebar.write("**Nouveau compte**")
                name = st.sidebar.text_input("Prénom")
                role = st.sidebar.radio(
                    "Je suis",
                    ["famille", "collecteur"],
                    format_func=lambda r: "Une famille qui donne son plastique" if r == "famille" else "Un collecteur (barbecha)",
                )
                quartier = st.sidebar.selectbox("Mon quartier", list(QUARTIERS))
                if st.sidebar.button("Créer mon compte", type="primary"):
                    if not name.strip():
                        st.sidebar.error("Indique ton prénom.")
                    else:
                        execute(
                            "INSERT INTO users (name, phone, role, quartier, created_at) VALUES (?,?,?,?,?)",
                            (name.strip(), phone, role, quartier, now()),
                        )
                        st.session_state.user_id = query_one("SELECT id FROM users WHERE phone=?", (phone,))["id"]
                        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("Ajouter des données de démonstration"):
        ajouter_donnees_demo()
        flash("Données de démonstration ajoutées : 3 familles et 6 sacs.")
        st.rerun()
    return None


# ---------------- Page d'accueil ----------------

def page_accueil():
    st.markdown(
        f"""<div class="hero">
{logo_html(130)}
<div class="nom">{APP_NAME}</div>
<div class="ar">{SLOGAN_AR}</div>
<div class="fr">{SLOGAN_FR}</div>
</div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""<div class="bloc"><b>Le constat.</b> Chaque jour, des collecteurs, les barbechas, fouillent les poubelles
pour récupérer les bouteilles en plastique et les revendre au kilo. Un travail pénible et sale, pour un plastique
abîmé et mal payé. De l'autre côté, beaucoup de familles aimeraient trier, mais ne savent pas à qui donner leurs bouteilles.</div>
<div class="bloc"><b>L'idée.</b> {APP_NAME} relie directement les deux : les familles gardent leurs bouteilles propres
dans un sac, les collecteurs viennent le récupérer devant la porte. Chacun participe librement, quand il veut.</div>""",
        unsafe_allow_html=True,
    )

    st.subheader("Ce que chacun y gagne")
    cartes = [
        ("Les familles", "Un geste simple pour moins de déchets à la maison, et des points à échanger bientôt chez les commerces du quartier."),
        ("Les collecteurs", "Du plastique propre, trouvé sans fouiller les poubelles, et des tournées mieux organisées pour gagner plus."),
        ("Le quartier", "Des poubelles moins pleines, moins de plastique dans la nature et plus de matière pour le recyclage."),
    ]
    for col, (titre, texte) in zip(st.columns(3), cartes):
        col.markdown(f'<div class="carte"><div class="titre">{titre}</div>{texte}</div>', unsafe_allow_html=True)

    st.subheader("Comment ça marche ?")
    etapes = [
        ("La famille publie son sac", "Taille du sac, adresse, et une photo si elle veut."),
        ("Le collecteur réserve", "Il voit les sacs proches de lui et réserve ceux qu'il va récupérer."),
        ("La récupération", "La famille donne un code à 4 chiffres au collecteur, qui valide la collecte."),
        ("Chacun y gagne", "La famille reçoit des points, le collecteur revend un plastique propre."),
    ]
    st.markdown(
        "".join(
            f'<div class="etape"><div class="num">{i}</div><div><b>{t}</b><br>{d}</div></div>'
            for i, (t, d) in enumerate(etapes, 1)
        ),
        unsafe_allow_html=True,
    )

    st.subheader("En chiffres")
    s = stats_globales()
    c1, c2, c3 = st.columns(3)
    c1.metric("Sacs récupérés", s["sacs"])
    c2.metric("Plastique recyclé", f"{s['kg']:.0f} kg")
    c3.metric("Participants", s["participants"])

    dispo = query("SELECT lat, lon FROM bags WHERE status='disponible'")
    if dispo:
        st.subheader(f"{len(dispo)} sacs attendent un collecteur")
        st.map(pd.DataFrame([dict(r) for r in dispo]), color=ORANGE)

    st.markdown(
        """<div class="bloc"><b>Envie de participer ?</b> Ouvre le menu Connexion (la flèche en haut à gauche
sur téléphone) et entre ton numéro. C'est gratuit, et tu peux arrêter quand tu veux.</div>""",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="pied">{APP_NAME} · projet citoyen en test à Tunis · version prototype</div>', unsafe_allow_html=True)


# ---------------- Espace famille ----------------

def page_famille(user):
    st.title(f"Bonjour {user['name']}")
    t1, t2, t3 = st.tabs(["Publier un sac", "Mes sacs", "Mes points"])
    with t1:
        publier_sac(user)
    with t2:
        mes_sacs(user)
    with t3:
        mes_points(user)


def publier_sac(user):
    with st.form("form_sac", clear_on_submit=True):
        taille = st.radio(
            "Taille du sac",
            list(TAILLES),
            format_func=lambda t: f"{t} ({TAILLES[t]['description']})",
        )
        matieres = st.multiselect("Contenu", MATIERES, default=[MATIERES[0]])
        quartier = st.selectbox("Quartier", list(QUARTIERS), index=list(QUARTIERS).index(user["quartier"]))
        adresse = st.text_input("Adresse ou point de repère", placeholder="ex. Rue Ibn Khaldoun, à côté de la pharmacie")
        note = st.text_area("Précisions pour le collecteur (facultatif)", placeholder="ex. sac devant la porte le matin, 2e étage")
        photo = st.file_uploader("Photo du sac (facultatif)", type=["jpg", "jpeg", "png"])
        envoye = st.form_submit_button("Publier mon sac", type="primary")

    if envoye:
        if not adresse.strip():
            st.error("Indique une adresse ou un point de repère.")
            return
        if photo and photo.size > 5 * 1024 * 1024:
            st.error("La photo est trop lourde (5 Mo maximum).")
            return
        lat, lon = position_quartier(quartier)
        code = nouveau_code()
        execute(
            """INSERT INTO bags (family_id, size, materials, quartier, address, note, lat, lon, photo, code, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (user["id"], taille, ", ".join(matieres), quartier, adresse.strip(), note.strip(),
             lat, lon, photo.getvalue() if photo else None, code, now()),
        )
        st.success(f"Ton sac est publié ! Code de récupération : **{code}**. Donne ce code au collecteur quand il passe.")


def mes_sacs(user):
    sacs = query(
        """SELECT b.*, u.name AS collector_name, u.phone AS collector_phone
           FROM bags b LEFT JOIN users u ON u.id = b.collector_id
           WHERE b.family_id=? ORDER BY b.id DESC""",
        (user["id"],),
    )
    if not sacs:
        st.info("Tu n'as pas encore publié de sac.")
        return

    for b in sacs:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**Sac {b['size'].lower()}** · {b['quartier']}")
                st.caption(f"Publié le {b['created_at']} · {b['materials']}")
                st.write(STATUTS[b["status"]])
                if b["status"] == "reserve":
                    st.write(f"Collecteur : **{b['collector_name']}** ({b['collector_phone']})")
                if b["status"] != "collecte":
                    st.info(f"Code à donner au collecteur : **{b['code']}**")
                else:
                    st.caption(f"Récupéré le {b['collected_at']} · +{TAILLES[b['size']]['points']} points")
            with c2:
                if b["photo"]:
                    st.image(b["photo"], width=110)
                if b["status"] == "disponible":
                    if st.button("Annuler", key=f"annuler_{b['id']}"):
                        execute("DELETE FROM bags WHERE id=? AND status='disponible'", (b["id"],))
                        flash("Sac retiré.")
                        st.rerun()


def mes_points(user):
    sizes = [r["size"] for r in query("SELECT size FROM bags WHERE family_id=? AND status='collecte'", (user["id"],))]
    b = bilan(sizes)
    c1, c2, c3 = st.columns(3)
    c1.metric("Points", b["points"])
    c2.metric("Sacs recyclés", b["sacs"])
    c3.metric("Plastique", f"{b['kg']:.1f} kg")

    if b["points"] < 50:
        niveau = "Débutant"
    elif b["points"] < 200:
        niveau = "Engagé"
    else:
        niveau = "Champion du recyclage"
    st.subheader(f"Ton niveau : {niveau}")
    st.caption("Bientôt : échange des points contre des réductions chez les commerces partenaires du quartier.")


# ---------------- Espace collecteur ----------------

def page_collecteur(user):
    st.title(f"Bonjour {user['name']}")
    t1, t2, t3 = st.tabs(["Sacs disponibles", "Mes réservations", "Mon bilan"])
    with t1:
        sacs_disponibles(user)
    with t2:
        mes_reservations(user)
    with t3:
        bilan_collecteur(user)


def sacs_disponibles(user):
    c1, c2 = st.columns(2)
    depart = c1.selectbox("Je suis à", list(QUARTIERS), index=list(QUARTIERS).index(user["quartier"]))
    rayon = c2.slider("Distance maximum (km)", 1, 20, 5)
    ref = QUARTIERS[depart]

    sacs = query("SELECT * FROM bags WHERE status='disponible'")
    liste = sorted(
        [(distance_km(ref, (b["lat"], b["lon"])), b) for b in sacs],
        key=lambda x: x[0],
    )
    liste = [(d, b) for d, b in liste if d <= rayon]

    if not liste:
        st.info("Aucun sac disponible dans ce rayon pour le moment.")
        return

    st.map(pd.DataFrame([{"lat": b["lat"], "lon": b["lon"]} for _, b in liste]))

    nb_res = query_one(
        "SELECT COUNT(*) AS n FROM bags WHERE collector_id=? AND status='reserve'", (user["id"],)
    )["n"]
    if nb_res >= MAX_RESERVATIONS:
        st.warning(f"Tu as déjà {MAX_RESERVATIONS} réservations en cours. Récupère-les avant d'en réserver d'autres.")

    for d, b in liste:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**Sac {b['size'].lower()}** ({TAILLES[b['size']]['description']})")
                st.caption(f"{b['quartier']} · à environ {d:.1f} km · {b['materials']}")
                st.caption("L'adresse exacte s'affiche après réservation.")
            with c2:
                if b["photo"]:
                    st.image(b["photo"], width=100)
                if st.button("Réserver", key=f"res_{b['id']}", type="primary", disabled=nb_res >= MAX_RESERVATIONS):
                    n = execute(
                        "UPDATE bags SET status='reserve', collector_id=? WHERE id=? AND status='disponible'",
                        (user["id"], b["id"]),
                    )
                    if n:
                        flash("Sac réservé ! Retrouve-le dans l'onglet « Mes réservations ».")
                    else:
                        flash("Ce sac vient d'être réservé par un autre collecteur.")
                    st.rerun()


def mes_reservations(user):
    sacs = query(
        """SELECT b.*, u.name AS family_name, u.phone AS family_phone
           FROM bags b JOIN users u ON u.id = b.family_id
           WHERE b.collector_id=? AND b.status='reserve' ORDER BY b.id""",
        (user["id"],),
    )
    if not sacs:
        st.info("Aucune réservation en cours. Va dans « Sacs disponibles » pour en réserver.")
        return

    for b in sacs:
        with st.container(border=True):
            st.markdown(f"**Sac {b['size'].lower()}** · {b['quartier']}")
            st.write(f"**Adresse :** {b['address']}")
            if b["note"]:
                st.write(f"**Précisions :** {b['note']}")
            st.write(f"**Famille :** {b['family_name']} · {b['family_phone']}")
            if b["photo"]:
                st.image(b["photo"], width=160)

            code = st.text_input("Code donné par la famille", max_chars=4, key=f"code_{b['id']}")
            c1, c2 = st.columns(2)
            if c1.button("Valider la collecte", key=f"val_{b['id']}", type="primary"):
                if code.strip() == b["code"]:
                    execute("UPDATE bags SET status='collecte', collected_at=? WHERE id=?", (now(), b["id"]))
                    flash("Collecte validée, merci !")
                    st.rerun()
                else:
                    st.error("Code incorrect. Demande-le à la famille.")
            if c2.button("Annuler la réservation", key=f"ann_{b['id']}"):
                execute(
                    "UPDATE bags SET status='disponible', collector_id=NULL WHERE id=? AND collector_id=?",
                    (b["id"], user["id"]),
                )
                flash("Réservation annulée.")
                st.rerun()


def bilan_collecteur(user):
    sizes = [r["size"] for r in query("SELECT size FROM bags WHERE collector_id=? AND status='collecte'", (user["id"],))]
    b = bilan(sizes)
    prix = st.number_input(
        "Prix de rachat du plastique (DT/kg)",
        min_value=0.0, value=0.5, step=0.05,
        help="Valeur indicative, à ajuster selon ton point de rachat.",
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Sacs récupérés", b["sacs"])
    c2.metric("Plastique", f"{b['kg']:.1f} kg")
    c3.metric("Revenu estimé", f"{b['kg'] * prix:.2f} DT")
    st.caption("Poids estimé à partir de la taille des sacs.")


# ---------------- Lancement ----------------

init_db()
utilisateur = sidebar_connexion()
afficher_flash()

if utilisateur is None:
    page_accueil()
elif utilisateur["role"] == "famille":
    page_famille(utilisateur)
else:
    page_collecteur(utilisateur)
