    function togglePass(inputId, icon) {
        const input = document.getElementById(inputId);
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);

        // Đổi icon
        if (type === 'text') {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        } else {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
    const currentPath = window.location.pathname;

    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        if (href === currentPath) {
            link.classList.add('active');

            if(link.classList.contains('dropdown-item')){
                link.closest('.dropdown').querySelector('.nav-link').classList.add('active');
            }
        }
    });
});