# --- 1. Importation des modules nécessaires ---
from flask import Flask, render_template, request, redirect, url_for, session, make_response, current_app
from dotenv import load_dotenv
import os
from flask_mail import Mail, Message
from flask_babel import Babel, gettext as _, get_locale 
from werkzeug.exceptions import InternalServerError 
import threading 

# Chargement des variables d'environnement du fichier .env (utile pour le développement local)
load_dotenv() 

# Initialisation de l'application
app = Flask(__name__)

# --- 2. Configuration de Flask-Mail & SECRET_KEY ---

# R1. SECRET_KEY: Clé obligatoire pour la session Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clé_de_secours_dev')

# R2. Configuration Mail (Simplifiée et consolidée)
# Récupération des variables depuis l'environnement (Render) ou le .env (Local)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')

# Assurer la lecture et la conversion correcte du port
try:
    # Tente de convertir le port en entier; utilise None si non défini
    port_value = os.environ.get('MAIL_PORT')
    app.config['MAIL_PORT'] = int(port_value) if port_value else 465
except ValueError:
    # Si défini mais non numérique
    app.config['MAIL_PORT'] = 465

# Les conversions en booléen sont basées sur la valeur de l'environnement (ex: "True" -> True)
app.config['MAIL_USE_TLS'] = False 
app.config['MAIL_USE_SSL'] = True 

app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
# Ajout de RECIPIENT_EMAIL pour le diagnostic et l'usage
app.config['RECIPIENT_EMAIL'] = os.getenv('RECIPIENT_EMAIL') 

# R3. Diagnostic de configuration Mail CRITIQUE
# Ces valeurs doivent être correctes dans les logs de déploiement Render.
print("-" * 50)
print("DIAGNOSTIC FLASK-MAIL - VALEURS ACTUELLEMENT CHARGÉES (TENTATIVE SSL/PORT 465)")
print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
print(f"MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
print(f"MAIL_USE_SSL: {app.config['MAIL_USE_SSL']}")
# On n'affiche pas les mots de passe, mais on vérifie leur présence
print(f"MAIL_USERNAME (SENDER): {app.config['MAIL_USERNAME']}")
print(f"MAIL_PASSWORD (Défini): {'OUI' if app.config['MAIL_PASSWORD'] else 'NON'}")
print(f"RECIPIENT_EMAIL: {app.config['RECIPIENT_EMAIL']}")

# Vérification pour un diagnostic plus clair
if not app.config['MAIL_SERVER'] or not app.config['MAIL_PORT'] or not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
    print("!!! ALERTE CRITIQUE !!!: Une ou plusieurs variables de configuration SMTP essentielles sont manquantes ou vides.")
    print("ACTION REQUISE: Assurez-vous que MAIL_SERVER, MAIL_PORT, MAIL_USERNAME et MAIL_PASSWORD sont définis DANS LES VARIABLES D'ENVIRONNEMENT DE RENDER.")
else:
    print("Configuration SMTP complète. Le problème est probablement lié à l'accès réseau ou à l'authentification.")

print("-" * 50)

# Initialisation de l'objet Mail
mail = Mail(app)

# Initialisation de l'objet Babel
babel = Babel(app)

# --- 2.5. Fonctions d'envoi Asynchrone (La solution au problème) ---

def send_async_email(app, msg):
    """Exécute l'envoi d'e-mail dans le contexte de l'application. 
    NÉCESSAIRE car les threads perdent le contexte applicatif."""
    with app.app_context():
        try:
            # Tente de créer le connexion et d'envoyer l'e-mail
            mail.send(msg)
            print("Email envoyé avec succès par le thread!")
        except Exception as e:
            # Log l'erreur d'envoi. Si [Errno 101] ou l'erreur d'authentification s'affiche ici,
            # cela confirme que la configuration est lue mais que la connexion échoue.
            print(f"ERREUR CRITIQUE D'ENVOI DANS LE THREAD: Détail: {e}")

def send_email_async(subject, sender, recipients, body):
    """Lance l'envoi d'e-mail dans un thread séparé."""

    # 1. Création du message
    msg = Message(subject, sender=sender, recipients=recipients, body=body)

    # 2. Récupération de l'instance de l'application courante
    app = current_app._get_current_object()
 
    # 3. Lancement de l'exécution dans un nouveau thread
    thr = threading.Thread(target=send_async_email, args=[app, msg])
    thr.start()

# --- 3. Route de selection de langues ---

def get_locale_selector():
    # Tente de lire le cookie en premier pour la fiabilité de Babel
    return request.cookies.get('lang') or session.get('lang', request.accept_languages.best_match(['fr', 'en']))
# Initialisation explicite de Babel avec la fonction de sélection de locale. 
# Ceci remplace l'utilisation du décorateur @babel.localeselector qui cause l'erreur.
babel.init_app(app, locale_selector=get_locale_selector)

@app.route('/lang/<lang>')
def set_language(lang):
    # Validation pour s'assurer que la langue est supportée
    if lang not in ['fr', 'en']:
        lang = 'fr' 
        
    session['lang'] = lang
    next_url = request.referrer if request.referrer else url_for('index')

    resp = make_response(redirect(next_url))

    # Définit le cookie 'lang' dans la réponse
    resp.set_cookie('lang', lang)
    
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'

    return resp

# --- 4. Route pour afficher le portfolio ---
@app.route('/')
def index():
    current_lang = str(get_locale())
    print(f"DEBUG LANGUE ACTIVE: {current_lang} | SESSION['lang']: {session.get('lang')} | COOKIE['lang']: {request.cookies.get('lang')}")

    return render_template('index.html')

# --- 5. Route pour recevoir les messages du formulaire ---
@app.route('/contact', methods=['POST'])
def handle_contact():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'message': request.form.get('message')
        }

    # Utilise la variable configurée
    RECIPIENT_EMAIL = app.config.get("RECIPIENT_EMAIL") 
    if not RECIPIENT_EMAIL:
        ("ERREUR: RECIPIENT_EMAIL n'est pas défini. L'envoi sera ignoré.")
        redirect(url_for('index', _anchor='contact'))

        try:
            subject=_(
            "Nouveau message de Portfolio par %(name)s (%(email)s)", 
                name=data['name'], 
                email=data['email']
            )
            sender=app.config['MAIL_DEFAULT_SENDER']
            recipients=[RECIPIENT_EMAIL]
            body=f"Nom: {data['name']}\nEmail: {data['email']}\nMessage:\n{data['message']}"

    # Appel de la fonction asynchrone par threading
            send_email_async(subject, sender, recipients, body)

    # Le thread a démarré et le serveur peut immédiatement renvoyer la réponse
            return redirect(url_for('index', _anchor='contact'))

        except Exception as e:
    # Cette erreur NE DEVRAIT PAS ARRIVER
            print(f"ERREUR AVANT LE THREAD: {e}")
            return redirect(url_for('index', _anchor='contact'))

# --- 6. Point d'entrée de l'application ---
if __name__ == '__main__':
    # Le port 8080 est la convention de Render/Gunicorn
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)