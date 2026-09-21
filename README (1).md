# ♻️ Recyclage de proximité (prototype)

Application qui met en relation les familles qui trient leur plastique et les collecteurs (barbechas) en Tunisie.

## Fonctionnalités

- Connexion avec un numéro de téléphone et choix du rôle : famille ou collecteur
- **Famille** : publier un sac (taille, contenu, adresse, photo), suivre son statut, gagner des points
- **Collecteur** : voir les sacs proches sur une carte, réserver, valider la collecte avec le code à 4 chiffres, suivre ses kilos et son revenu estimé
- Bouton de données de démonstration pour tester seul

## Mettre l'application en ligne (gratuit)

1. Crée un compte sur **github.com**
2. Clique sur **New repository**, nomme-le `recyclage-app`, laisse-le en **Public**, puis **Create repository**
3. Clique sur **uploading an existing file** et glisse les fichiers `app.py`, `requirements.txt` et `README.md`, puis **Commit changes**
4. Va sur **share.streamlit.io** et connecte-toi avec ton compte GitHub
5. Clique sur **Create app**, choisis ton dépôt `recyclage-app`, fichier principal `app.py`, puis **Deploy**

Après 2 ou 3 minutes, tu obtiens un lien que tu peux ouvrir sur ton téléphone et partager.

## Tester sur ton ordinateur (facultatif)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Limites du prototype

- Pas de vérification par SMS : le numéro sert simplement d'identifiant.
- Les données sont stockées dans un fichier SQLite. Sur Streamlit Cloud, elles sont **effacées quand l'application redémarre** (mise à jour du code, inactivité). Pour un vrai test avec des utilisateurs, il faudra une base en ligne (par exemple Supabase).
- La position des sacs est approximative (centre du quartier).
