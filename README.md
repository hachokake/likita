# Likita

Likita est une application SaaS Django de gestion d'invitations d'evenements avec RSVP, QR code, scanner, notifications et API REST.

## Stack

- Django 6
- PostgreSQL
- Django REST Framework
- Celery + Redis
- Tailwind CSS
- Alpine.js
- Pillow + qrcode

## Demarrage local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements\base.txt
npm install
copy .env.example .env
python manage.py migrate
npm run build:css
python manage.py runserver
```

Dans un second terminal pour Celery:

```bash
celery -A config worker --loglevel=info
```

## Applications Django

- accounts
- events
- guests
- invitations
- rsvp
- qrcode via le package applicatif `qrmanager` avec le label Django `qrcode`
- scanner
- dashboard
- notifications
- adminpanel
- core
- api

## Fonctionnalites couvrees

- dashboard utilisateur et espace administration separes
- gestion des evenements et des invites
- liens d'invitation WhatsApp uniques
- envoi reel via WhatsApp Business Cloud API quand les variables d'environnement sont renseignees
- page publique d'invitation avec RSVP
- QR code unique par invite
- scanner avec validation en direct et fallback manuel
- notifications internes sur RSVP et scans
- API REST prete pour mobile
- import CSV / Excel avec mapping de colonnes

## WhatsApp Business

Likita sait utiliser WhatsApp Cloud API de Meta.

Variables a renseigner dans `.env`:

- `WHATSAPP_PROVIDER=whatsapp_cloud`
- `WHATSAPP_ACCESS_TOKEN=...`
- `WHATSAPP_PHONE_NUMBER_ID=...`
- `APP_BASE_URL=https://votre-domaine.com`

Sans ces variables, l'application repasse automatiquement en partage WhatsApp manuel.

## Deploiement

- Render: `render.yaml`
- Railway: compatible via `Procfile` et variables d'environnement de `.env.example`

### PythonAnywhere

1. Creez un compte sur [PythonAnywhere](https://www.pythonanywhere.com/), puis ouvrez un terminal **Bash**.
2. Clonez le depot et entrez dans le projet :

	```bash
	git clone https://github.com/VOTRE_COMPTE/likita.git
	cd likita
	```

3. Creez l'environnement virtuel et installez les dependances. Choisissez une version de Python compatible avec Django 6 (Python 3.12 ou plus recent) :

	```bash
	mkvirtualenv --python=/usr/bin/python3.12 likita-env
	pip install -r requirements/base.txt
	npm install
	npm run build:css
	```

4. Creez `.env` a partir de `.env.example`, avec les valeurs de production suivantes. Remplacez `votrecompte` par votre identifiant PythonAnywhere et utilisez une cle secrete longue et aleatoire :

	```dotenv
	DJANGO_SECRET_KEY=une-cle-secrete-longue-et-aleatoire
	DJANGO_DEBUG=False
	DJANGO_ALLOWED_HOSTS=votrecompte.pythonanywhere.com
	DJANGO_CSRF_TRUSTED_ORIGINS=https://votrecompte.pythonanywhere.com
	DJANGO_SECURE_SSL_REDIRECT=True
	APP_BASE_URL=https://votrecompte.pythonanywhere.com
	DATABASE_URL=sqlite:////home/votrecompte/likita/db.sqlite3
	```

	Pour PostgreSQL, remplacez `DATABASE_URL` par l'URL fournie par votre hebergeur. Ne versionnez jamais `.env`.

5. Executez les migrations et rassemblez les fichiers statiques :

	```bash
	python manage.py migrate
	python manage.py collectstatic --noinput
	python manage.py check --deploy
	```

6. Dans l'onglet **Web**, creez une application manuelle avec la meme version de Python. Configurez le virtualenv sur `/home/votrecompte/.virtualenvs/likita-env`, puis ouvrez le fichier WSGI fourni par PythonAnywhere et remplacez son contenu par :

	```python
	import os
	import sys

	project_home = '/home/votrecompte/likita'
	if project_home not in sys.path:
		 sys.path.insert(0, project_home)

	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

	from django.core.wsgi import get_wsgi_application
	application = get_wsgi_application()
	```

7. Dans **Static files**, ajoutez `/static/` vers `/home/votrecompte/likita/staticfiles` et `/media/` vers `/home/votrecompte/likita/media`. Cliquez **Reload**.
8. Testez l'accueil, une URL inexistante (page 404) et l'administration. En cas d'erreur, consultez les fichiers **Error log** et **Server log** dans l'onglet Web. Apres chaque mise a jour : `git pull`, `pip install -r requirements/base.txt`, `python manage.py migrate`, `python manage.py collectstatic --noinput`, puis **Reload**.

Celery et Redis ne sont pas disponibles nativement sur les comptes PythonAnywhere. Les taches asynchrones doivent etre desactivees, executees via une tache planifiee, ou deplacees vers un service worker/Redis externe avant d'activer les envois WhatsApp en production.

## Prochaines evolutions naturelles

- import CSV/Excel via service dedie
- paiement et abonnements
- envoi WhatsApp via provider officiel
- analytics avancees