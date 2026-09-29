document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.getElementById('dashboard-menu-toggle');
    const menuList = document.getElementById('dashboard-menu-list');
    const logoutButton = document.getElementById('logout-button');

    if (!menuToggle || !menuList || !logoutButton) {
        return;
    }

    function closeMenu() {
        menuList.hidden = true;
        menuToggle.setAttribute('aria-expanded', 'false');
    }

    function toggleMenu() {
        const shouldOpen = menuList.hidden;
        menuList.hidden = !shouldOpen;
        menuToggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    }

    function logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        localStorage.removeItem('user_email');
        window.location.href = '/';
    }

    menuToggle.addEventListener('click', (event) => {
        event.stopPropagation();
        toggleMenu();
    });

    logoutButton.addEventListener('click', logout);

    document.addEventListener('click', (event) => {
        if (menuList.hidden || event.target.closest('.dashboard-menu')) {
            return;
        }

        closeMenu();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeMenu();
        }
    });
});
