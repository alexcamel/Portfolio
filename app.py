# --- 1. Importation des modules nécessaires ---
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from dotenv import load_dotenv
import os
from flask_babel import Babel, gettext as _, get_locale 
from werkzeug.exceptions import InternalServerError 

# Chargement des variables d'environnement du fichier .env (utile pour le développement local)
load_dotenv() 

# Initialisation de l'application
app = Flask(__name__)

# --- 2. Configuration de SECRET_KEY ---

# R1. SECRET_KEY: Clé obligatoire pour la session Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clé_de_secours_dev')

# Initialisation de l'objet Babel
babel = Babel(app)

# --- 3. Route de selection de langues et Configuration Babel ---

# Fonction SANS DECORATEUR pour Babel
def get_locale_selector():
    # Tente de lire le cookie en premier pour la fiabilité de Babel
    return request.cookies.get('lang') or session.get('lang', request.accept_languages.best_match(['fr', 'en']))

# Initialisation explicite de Babel (Corrige l'erreur 'AttributeError')
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


    RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL', 'adresse-email-par-defaut@example.com')
    
    return render_template('index.html', recipient_email=RECIPIENT_EMAIL)

# --- 5. Route de contact simplifiée (Elle ne fait plus que rediriger) ---
@app.route('/contact', methods=['POST'])
def handle_contact():
    # Redirige simplement l'utilisateur après le POST.
    print("Le formulaire a été posté sur /contact, mais l'envoi réel est géré par FormSubmit dans le HTML.")
    return redirect(url_for('index', _anchor='contact'))
    
# --- 6. Point d'entrée de l'application ---
if __name__ == '__main__':
    # Le port 8080 est la convention de Render/Gunicorn
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

