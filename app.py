from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
from flask_mail import Mail, Message

# Charge les variables d'environnement du fichier .env
load_dotenv() 

app = Flask(__name__)

# --- 1. Configuration de Flask-Mail ---
# Ces paramètres sont lus directement du fichier .env
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = True  # Utilisation de TLS pour la sécurité
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME') # L'adresse d'envoi

mail = Mail(app)

# --- 2. Route pour afficher le portfolio ---
@app.route('/')
def index():
    # Affiche le fichier index.html, qui doit se trouver dans le dossier 'templates'
    return render_template('index.html')

# --- 3. Route pour recevoir les messages du formulaire ---
@app.route('/contact', methods=['POST'])
def handle_contact():
    # Vérifie que le formulaire a été soumis via POST
    if request.method == 'POST':
        # Récupération des données du formulaire (doit correspondre aux attributs 'name' dans l'HTML)
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'message': request.form.get('message')
        }

        # Définissez ici l'adresse email où vous voulez recevoir les messages
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
            # Vous pouvez ajouter un 'message flash' ici pour indiquer le succès à l'utilisateur
            return redirect(url_for('index', _anchor='contact'))
            
        except Exception as e:
            # En cas d'erreur (mauvaises infos SMTP, problème de connexion, etc.)
            print(f"Erreur lors de l'envoi de l'email: {e}")
            # Redirection même en cas d'erreur (pour ne pas casser l'interface)
            return redirect(url_for('index', _anchor='contact'))

if __name__ == '__main__':
    # Lance l'application. 'debug=True' est utile en développement.
    app.run(debug=True)