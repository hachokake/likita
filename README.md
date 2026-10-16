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
- tableau de bord par evenement avec statistiques RSVP, QR codes, entrees uniques et activite recente
- recherche et filtres des invites par evenement et reponse RSVP
- liens d'invitation WhatsApp uniques
- envoi reel via WhatsApp Business Cloud API quand les variables d'environnement sont renseignees
- page publique d'invitation avec RSVP
- QR code unique par invite
- partage du QR code d'un invité confirmé sur WhatsApp, sans message additionnel
- scanner QR par caméra compatible avec les navigateurs modernes et saisie manuelle de secours
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

`APP_BASE_URL` doit toujours être une URL HTTPS accessible publiquement. Une adresse locale telle que
`http://127.0.0.1:8000` ne peut être ouverte que depuis l'ordinateur qui exécute Django. Pour des essais locaux,
utilisez une URL de tunnel HTTPS temporaire ; pour la production, utilisez le domaine public de l'application.

## Deploiement

- Render: `render.yaml`
- Railway: compatible via `Procfile` et variables d'environnement de `.env.example`

## Prochaines evolutions naturelles

- import CSV/Excel via service dedie
- paiement et abonnements
- envoi WhatsApp via provider officiel
- analytics avancees