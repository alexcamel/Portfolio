# --- 1. Importation des modules nécessaires ---
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from dotenv import load_dotenv
import os
from flask_mail import Mail, Message
from flask_babel import Babel, get_locale # Ajout de get_locale pour le diagnostic
# Chargement des variables d'environnement du fichier .env
load_dotenv() 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ma_clé_sécrète'
babel = Babel(app)

# --- 2. Configuration de Flask-Mail ---

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')

# CONVERSION : '587' (string) devient 587 (integer)
# Cette conversion est indispensable si vous utilisez MAIL_PORT=587 dans votre .env
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT')) 

# C'est correct de le laisser à True si c'est toujours le cas pour Gmail.
# Si vous voulez le lire du .env, il faudrait faire une conversion plus complexe (voir note ci-dessous).
app.config['MAIL_USE_TLS'] = True 

app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

# --- 3. Route de selection de langues ---
def get_locale():
     # Récupère la langue dans la session si elle est définie, sinon utilise la langue du navigateur.
    # Ceci est le sélecteur de langue pour Flask-Babel
    return session.get('lang', request.accept_languages.best_match(['fr', 'en']))

babel.init_app(app, locale_selector=get_locale)

@app.route('/lang/<lang>')
def set_language(lang):
    # Enregistre le choix de l'utilisateur dans la session
    session['lang'] = lang
     # 1. Créer la réponse de redirection
    resp = make_response(redirect(url_for('index')))
    
    # 2. Ajout des en-têtes anti-cache pour forcer le navigateur à recharger la page
    # et à ne pas utiliser l'ancienne version mise en cache (qui était dans l'ancienne langue)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    
    return resp

    


# --- 4. Route pour afficher le portfolio ---
@app.route('/')
def index():
    
    # LIGNE DE DEBUG CRUCIALE POUR DIAGNOSTIC
    # Permet de voir dans la console quelle est la langue active et le contenu de la session.
    current_lang = str(get_locale())
    print(f"DEBUG LANGUE ACTIVE: {current_lang} | SESSION['lang']: {session.get('lang')}")
    # Affiche le fichier index.html
    return render_template('index.html')

# --- 5. Route pour recevoir les messages du formulaire ---
@app.route('/contact', methods=['POST'])
def handle_contact():
    # Vérification de la soumission du formulaire via POST
    if request.method == 'POST':
        # Récupération des données du formulaire 
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'message': request.form.get('message')
        }

        # Adresse email de reception des messages
        RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL") 

        try:
            # Création de l'objet Message pour l'envoi
            msg = Message(
                subject=f"Nouveau message de Portfolio par {data['name']} ({data['email']})",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[RECIPIENT_EMAIL],
                body=f"Nom: {data['name']}\nEmail: {data['email']}\nMessage:\n{data['message']}"
            )
            mail.send(msg)
            print("Email envoyé avec succès!")
            
            # Redirection vers la page d'accueil avec l'ancre #contact (pour rester sur le formulaire)
            return redirect(url_for('index', _anchor='contact'))
            
        except Exception as e:
            # En cas d'erreur (mauvaises infos SMTP, problème de connexion, etc.)
            print(f"Erreur lors de l'envoi de l'email: {e}")
            # Redirection même en cas d'erreur (pour ne pas casser l'interface)
            return redirect(url_for('index', _anchor='contact'))

if __name__ == '__main__':
    # Lance l'application
    app.run(debug=True)