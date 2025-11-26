# --- 1. Importation des modules nécessaires ---
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from dotenv import load_dotenv
import os
from flask_mail import Mail, Message
# Flask-Babel: Utilisation de gettext as _ pour la traduction dans le code Python
from flask_babel import Babel, gettext as _, get_locale 
from werkzeug.exceptions import InternalServerError 

# Chargement des variables d'environnement du fichier .env
load_dotenv() 

app = Flask(__name__)

# --- 2. Configuration de Flask-Mail & SECRET_KEY (Robustesse pour Render) ---

# R1. SECRET_KEY: Clé obligatoire pour la session Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# R2. Sécurité & Diagnostic pour SECRET_KEY
if not app.config['SECRET_KEY']:
    # Ce message est essentiel pour le diagnostic sur Render si la clé manque
    print("ERREUR CRITIQUE: SECRET_KEY est manquant. Le déploiement risque d'échouer ou la session sera non sécurisée.")
    # Clé de secours pour le développement UNIQUEMENT
    app.config['SECRET_KEY'] = 'UNE_CLE_DE_SECOURS_POUR_DEV_NE_PAS_UTILISER_EN_PROD'

# R3. MAIL_SERVER: Lecture simple
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')

# R4. MAIL_PORT: Conversion CRITIQUE EN INTEGER et vérification de la présence
mail_port_str = os.getenv('MAIL_PORT')
if mail_port_str is not None:
    try:
        app.config['MAIL_PORT'] = int(mail_port_str)
    except ValueError:
        print("ERREUR DE CONFIG: MAIL_PORT n'est pas un nombre valide. Utilisation du défaut 587.")
        app.config['MAIL_PORT'] = 587 
else:
    app.config['MAIL_PORT'] = None

# R5. MAIL_USE_TLS/SSL: Conversion des chaînes en booléens
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't') 
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't') 

# R6. Identifiants Mail
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# R7. Diagnostic de configuration Mail: Si une des clés est manquante, l'initialisation de Mail peut échouer.
if not all([app.config['MAIL_SERVER'], app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'], app.config['MAIL_PORT']]):
    print("ALERTE: Configuration Flask-Mail incomplète. L'envoi d'e-mails sera impossible.")

mail = Mail(app)
babel = Babel(app) # Initialisation de l'objet Babel

# --- 3. Route de selection de langues ---

# Fonction SANS décorateur pour le sélecteur de langue (Méthode compatible)
def get_locale_selector():
    # Récupère la langue dans la session si elle est définie, sinon utilise la langue du navigateur.
    return session.get('lang', request.accept_languages.best_match(['fr', 'en']))

# Initialisation manuelle de Babel (Résout l'AttributeError lié au décorateur)
babel.init_app(app, locale_selector=get_locale_selector)


@app.route('/lang/<lang>')
def set_language(lang):
    # Enregistre le choix de l'utilisateur dans la session
    session['lang'] = lang
    # Utiliser l'URL de la page précédente pour revenir où l'utilisateur était
    next_url = request.referrer if request.referrer else url_for('index')
    
    # 1. Créer la réponse de redirection
    resp = make_response(redirect(next_url))
    
    # 2. Ajout des en-têtes anti-cache pour forcer le navigateur à recharger la page
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    
    return resp

# --- 4. Route pour afficher le portfolio ---
@app.route('/')
def index():
    # LIGNE DE DEBUG CRUCIALE POUR DIAGNOSTIC
    # get_locale() est maintenant disponible grâce à babel.init_app
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

        # Vérification critique si RECIPIENT_EMAIL est défini
        RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL") 
        if not RECIPIENT_EMAIL:
            print("ERREUR: RECIPIENT_EMAIL n'est pas défini dans les variables d'environnement.")
            # Rediriger vers la page d'accueil après échec
            return redirect(url_for('index', _anchor='contact'))

        try:
            msg = Message(
                # Utilisation de gettext (_) pour permettre la traduction du sujet
                subject=_("Nouveau message de Portfolio par %(name)s (%(email)s)", name=data['name'], email=data['email']),
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[RECIPIENT_EMAIL],
                body=f"Nom: {data['name']}\nEmail: {data['email']}\nMessage:\n{data['message']}"
            )
            
            mail.send(msg)
            print("Email envoyé avec succès!")
            
            # Redirection vers la page d'accueil avec l'ancre #contact
            return redirect(url_for('index', _anchor='contact'))
            
        except Exception as e:
            # Cette erreur est souvent la SMTPAuthenticationError (mauvais mot de passe/clé) 
            # ou un problème de connexion dû aux variables MAIL_ manquantes sur Render.
            print(f"ERREUR D'ENVOI CRITIQUE: Vérifiez les variables MAIL_ sur Render. Détail: {e}")
            
            # Redirection même en cas d'erreur
            return redirect(url_for('index', _anchor='contact'))
        
# --- 6. Point d'entrée de l'application ---
if __name__ == '__main__':
    # Ne pas utiliser debug=True sur Render (production)
    app.run(debug=True)