# --- 1. Importation des modules nécessaires ---
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import os
from flask_mail import Mail, Message
from flask_babel import Babel

# Chargement des variables d'environnement du fichier .env
load_dotenv() 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ma_clé_sécrète'
babel = Babel(app)

# --- 2. Configuration de Flask-Mail ---
# Ces paramètres sont lus directement du fichier .env
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = True  # Utilisation de TLS pour la sécurité
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME') # L'adresse d'envoi

mail = Mail(app)

# --- Route de selection de langues ---
def get_locale():
    return session.get('lang', request.accept_languages.best_match(['fr', 'en']))

babel.init_app(app, locale_selector=get_locale)

@app.route('/lang/<lang>')
def set_language(lang):
    session['lang'] = lang
    return redirect(url_for('index'))


# --- 4. Route pour afficher le portfolio ---
@app.route('/')
def index():
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
        RECIPIENT_EMAIL = "alexcamelgouimanan@gmail.com" 

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