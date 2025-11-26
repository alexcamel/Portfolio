document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. GESTION DU MENU MOBILE ET ACCESSIBILITÉ ---
    
    const navToggle = document.querySelector('.nav-toggle'); 
    const navInner = document.querySelector('.nav-inner');   
    
    if (navToggle && navInner) {
        // Initialisation ARIA: Le menu est fermé par défaut
        navToggle.setAttribute('aria-expanded', 'false');
        // Initialisation ARIA: Associer le bouton au contenu qu'il contrôle (si vous ajoutez un id à nav-inner)
        // navToggle.setAttribute('aria-controls', 'nav-inner-content-id'); 

        navToggle.addEventListener('click', function() {
            // Bascule les classes d'état sur l'élément conteneur
            navInner.classList.toggle('open');
            
            // Mise à jour de l'accessibilité et de l'état du défilement
            const isExpanded = navInner.classList.contains('open');
            navToggle.setAttribute('aria-expanded', isExpanded.toString()); // ARIA n'accepte que 'true' ou 'false'
            document.body.classList.toggle('no-scroll', isExpanded); // Empêche le défilement en arrière-plan (doit être stylisé en CSS)
        });

        // Fermeture automatique du menu lors du clic sur un lien d'ancrage
        const navLinks = document.querySelectorAll('.nav-links a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                // S'assure que le menu est ouvert avant de tenter de le fermer
                if (navInner.classList.contains('open')) {
                    navInner.classList.remove('open');
                    navToggle.setAttribute('aria-expanded', 'false');
                    document.body.classList.remove('no-scroll');
                }
            });
        });
    }

    // --- 2. TÉLÉCHARGEMENT DU CV VIA INTERNET---
    
    const lienCV = document.getElementById('telecharger-cv');

    if (lienCV) { 
        lienCV.addEventListener('click', (e) => {
            e.preventDefault(); // Empêchement du navigateur de naviguer directement vers le PDF
            
            if (navigator.onLine) {
                const cvUrl = lienCV.href; 
                
                fetch(cvUrl)
                    .then(response => {
                        // Gestion des erreurs HTTP (404, 500, etc.)
                        if (!response.ok) {
                            throw new Error(`Erreur de réseau ou fichier introuvable. Statut: ${response.status}`);
                        }
                        return response.blob();
                    })
                    .then(blob => {
                        // Création d'un élément <a> temporaire pour forcer le téléchargement
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        
                        // Récupèration du nom de fichier à partir de l'attribut 'download' ou du chemin
                        const fileName = lienCV.getAttribute('download') || 'Alex_Camel_CV.pdf';
                        
                        a.href = url;
                        a.download = fileName; 
                        document.body.appendChild(a); 
                        a.click(); // Déclenche le téléchargement
                        document.body.removeChild(a); 
                        
                        URL.revokeObjectURL(url); // Libère la mémoire
                    })
                    .catch(error => {
                        console.error('Erreur lors du téléchargement du CV:', error);
                        alert(`Erreur: Le CV n'a pas pu être téléchargé. ${error.message}`);
                    });
            } else {
                alert("Veuillez vous connecter à internet pour télécharger mon CV.");
            }
        });
    }

    // --- 3. GESTION DE LA TRADUCTION ET DE LA CONNEXION INTERNET ---
    
    const langues = document.querySelector('.langues');

    if (langues) { 
        // Fonction utilitaire pour mettre à jour l'état de l'élément de langue
        const updateLanguageStatus = () => {
            if (navigator.onLine) {
                langues.classList.remove('disabled');
            } else {
                langues.classList.add('disabled');
            }
        };

        // Écoute des changements d'état de la connexion
        window.addEventListener('online', updateLanguageStatus);
        window.addEventListener('offline', updateLanguageStatus);

        // Initialisation de l'état au chargement de la page
        updateLanguageStatus();
    }
    
    // --- 4. GESTION DU FORMULAIRE DE CONTACT (Amélioration) ---
    
    const contactForm = document.getElementById('contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            
        });
    }
});