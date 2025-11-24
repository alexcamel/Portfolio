document.addEventListener('DOMContentLoaded', function() {
    // 1. GESTION DU MENU MOBILE
    // Sélection des éléments DOM
    const navToggle = document.querySelector('.nav-toggle'); // Le bouton ☰
    const navInner = document.querySelector('.nav-inner');   // L'élément parent qui reçoit la classe 'open'

    if (navToggle && navInner) {
        // Écouteur pour ouvrir/fermer le menu
        navToggle.addEventListener('click', function() {
            // Bascule la classe 'open' sur l'élément 'nav-inner'
            navInner.classList.toggle('open');
            
            // Mise à jour de l'accessibilité
            let isExpanded = navInner.classList.contains('open');
            navToggle.setAttribute('aria-expanded', isExpanded);
        });

        // Fermeture automatique du menu lors du clic sur un lien d'ancrage
        const navLinks = document.querySelectorAll('.nav-links a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                // Ferme le menu en retirant la classe 'open'
                navInner.classList.remove('open');
                navToggle.setAttribute('aria-expanded', false);
            });
        });
    }
    // 2. Téléchargement du CV via internet
    const lienCV = document.getElementById('telecharger-cv');
    lienCV.addEventListener('click', (e) =>{
        if (!navigator.onLine){
            e.preventDefault();
            alert('Vous devez être connecté à internet pour télécharger mon CV.');
        }
    });
});