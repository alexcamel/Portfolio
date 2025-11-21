// Small interactive behaviors: mobile menu + simple contact demo
document.addEventListener('DOMContentLoaded', function(){
  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  toggle && toggle.addEventListener('click', () => {
    if(navLinks.style.display === 'flex') navLinks.style.display = 'none';
    else navLinks.style.display = 'flex';
  });

  // contact form demo: don't actually send; just show a success message
  const form = document.getElementById('contact-form');
  if(form){
    form.addEventListener('submit', function(e){
      e.preventDefault();
      const btn = form.querySelector('button');
      btn.textContent = 'Envoi...';
      setTimeout(() => {
        btn.textContent = 'Envoyé ✅';
        form.reset();
        setTimeout(()=> btn.textContent = 'Envoyer', 2000);
      }, 900);
    });
  }
});
