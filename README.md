# 🚀 GitHub QuickShot

GitHub QuickShot est un outil minimaliste conçu pour créer des issues GitHub en quelques secondes sans jamais quitter votre clavier.

## 💡 Pourquoi utiliser QuickShot ?

* **Vitesse maximale** : Ne naviguez plus dans les menus complexes de GitHub. Une seule ligne de commande suffit pour tout configurer.
* **Autocomplétion intelligente** : L'application suggère les dépôts, labels, membres et milestones réels de vos projets dès que vous tapez `#`.
* **Interface sans distraction** : Un champ de texte unique pour rester concentré sur l'essentiel : la rédaction de vos tickets.
* **Sécurité & Confidentialité** : Connexion via OAuth avec des droits restreints (`public_repo`) et révocation immédiate du token à la déconnexion.

---

## 🛠️ Installation et Lancement

### 1. Préparer l'environnement

Assurez-vous d'avoir Python installé, puis exécutez ces commandes dans votre terminal :

```bash
# Créer l'environnement virtuel
python -m venv venv

# L'activer
# Sur Windows :
.\venv\Scripts\activate
# Sur Mac/Linux :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

```

### 2. Configurer les accès

Créez un fichier .env à la racine du projet et ajoutez vos identifiants :

```md
GITHUB_CLIENT_ID=votre_id_ici
GITHUB_CLIENT_SECRET=votre_secret_ici
```

### 3. Lancer l'application

```sh
python server.py
```

L'application est maintenant accessible sur : http://localhost:8000

## 🔑 Création de l'OAuth App (GitHub)

Pour obtenir vos identifiants, vous devez enregistrer ce projet comme une application sur votre compte GitHub :

1. Allez dans vos Settings > Developer Settings > OAuth Apps.
2. Cliquez sur New OAuth App.
    * Application Name : GitHub QuickShot
    * Homepage URL : http://localhost:8000
    * Authorization callback URL : http://localhost:8000/callback

Une fois l'app créée, copiez le Client ID et générez un Client Secret pour le fichier .env.

## ⌨️ Aide-mémoire des commandes

Tapez votre commande directement dans le champ principal, les suggestions apparaîtront automatiquement :

* `#repo:nom-du-projet` : Définit le dépôt cible (obligatoire).
* `#label:bug` : Ajoute un label existant.
* `#assignee:pseudo` : Assigne l'issue à un membre du repo.

Le reste du texte : Devient automatiquement le titre de l'issue.

Raccourci : Appuyez sur Ctrl + Entrée pour publier l'issue instantanément.
