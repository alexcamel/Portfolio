 # --- 1. Importation des modules nécessaires ---
from flask import Flask, render_template, request, redirect, url_for, session, make_response, current_app
from dotenv import load_dotenv
import os
from flask_mail import Mail, Message
from flask_babel import Babel, gettext as _, get_locale 
from werkzeug.exceptions import InternalServerError 
import threading # ⭐ NOUVEL IMPORT CRITIQUE : Pour l'exécution asynchrone

# Chargement des variables d'environnement du fichier .env
load_dotenv() 

# Initialisation de l'application
app = Flask(__name__)

# --- 2. Configuration de Flask-Mail & SECRET_KEY ---

# R1. SECRET_KEY: Clé obligatoire pour la session Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clé_de_secours_dev')

# R2. Configuration Mail (Simplifiée et consolidée)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
# Assurer la lecture et la conversion correcte du port
try:
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))
except (TypeError, ValueError):
    # Si MAIL_PORT n'est pas défini ou n'est pas un nombre, on lève une alerte (pas de défaut)
    app.config['MAIL_PORT'] = None

# Les conversions en booléen sont basées sur la valeur de l'environnement (ex: "True" -> True)
# Utiliser '0' ou 'False' comme défaut pour éviter des comportements inattendus si la variable n'existe pas
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() in ('true', '1', 't') 
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't') 

app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# R3. Diagnostic de configuration Mail
if not all([app.config['MAIL_SERVER'], app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'], app.config['MAIL_PORT']]):
    print("ALERTE: Configuration Flask-Mail incomplète (Serveur, Port, Utilisateur ou Mot de passe manquant). L'envoi d'e-mails sera impossible.")

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
            # Log l'erreur d'envoi, visible dans les logs de Render
            print(f"ERREUR CRITIQUE D'ENVOI DANS LE THREAD: Vérifiez l'authentification SMTP ou le port/protocole. Détail: {e}")

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
    return session.get('lang', request.accept_languages.best_match(['fr', 'en']))

# Initialisation manuelle de Babel (Résout l'AttributeError lié au décorateur)
babel.init_app(app, locale_selector=get_locale_selector)


@app.route('/lang/<lang>')
def set_language(lang):
    session['lang'] = lang
    next_url = request.referrer if request.referrer else url_for('index')
    
    resp = make_response(redirect(next_url))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    
    return resp

# --- 4. Route pour afficher le portfolio ---
@app.route('/')
def index():
    current_lang = str(get_locale())
    print(f"DEBUG LANGUE ACTIVE: {current_lang} | SESSION['lang']: {session.get('lang')}")
    
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

        RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL") 
        if not RECIPIENT_EMAIL:
            print("ERREUR: RECIPIENT_EMAIL n'est pas défini. L'envoi sera ignoré.")
            return redirect(url_for('index', _anchor='contact'))

        try:
            subject=_(
                "Nouveau message de Portfolio par %(name)s (%(email)s)", 
                name=data['name'], 
                email=data['email']
            )
            sender=app.config['MAIL_DEFAULT_SENDER']
            recipients=[RECIPIENT_EMAIL]
            body=f"Nom: {data['name']}\nEmail: {data['email']}\nMessage:\n{data['message']}"

            # ⭐ Appel de la fonction asynchrone. La route se termine immédiatement.
            send_email_async(subject, sender, recipients, body)

            # Le thread a démarré et le serveur peut immédiatement renvoyer la réponse
            return redirect(url_for('index', _anchor='contact'))
            
        except Exception as e:
            # Cette erreur NE DEVRAIT PAS ARRIVER
            print(f"ERREUR AVANT LE THREAD: {e}")
            return redirect(url_for('index', _anchor='contact'))
        
# --- 6. Point d'entrée de l'application ---
if __name__ == '__main__':
    app.run(debug=True)