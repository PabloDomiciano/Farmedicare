document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.querySelector(".sidebar-overlay");
  const mobileBtn = document.querySelector(".mobile-menu-btn");

  if (!sidebar) {
    return;
  }

  if (!mobileBtn) {
    return;
  }

  function toggleMenu() {
    sidebar.classList.toggle("active");
    mobileBtn.classList.toggle("active"); // Adiciona/remove classe active no botão
    if (overlay) {
      overlay.classList.toggle("active");
    }
    document.body.style.overflow = sidebar.classList.contains("active")
      ? "hidden"
      : "";
  }

  // Função para toggle dos submenus
  function toggleSubmenu(submenuToggle) {
    const parent = submenuToggle.closest(".has-submenu");
    const isActive = parent.classList.contains("active");

    // Fecha todos os outros submenus
    document.querySelectorAll(".has-submenu").forEach(function (item) {
      if (item !== parent) {
        item.classList.remove("active");
      }
    });

    // Alterna o estado do submenu atual
    parent.classList.toggle("active");
  }

  // Fecha todos os submenus
  function closeAllSubmenus() {
    document.querySelectorAll(".has-submenu").forEach(function (item) {
      item.classList.remove("active");
    });
  }

  // Event listeners para menu mobile
  mobileBtn.addEventListener("click", toggleMenu);
  if (overlay) {
    overlay.addEventListener("click", toggleMenu);
  }

  // Event listeners para submenus
  document.querySelectorAll(".submenu-toggle").forEach(function (toggle) {
    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      toggleSubmenu(this);
    });
  });

  // Click fora fecha os submenus
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".has-submenu")) {
      closeAllSubmenus();
    }
  });

  // Tecla ESC fecha os submenus
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeAllSubmenus();
    }
  });

  // Fecha menu ao clicar em links (apenas mobile)
  document.querySelectorAll(".menu-item a").forEach((item) => {
    item.addEventListener("click", function (e) {
      // Se não for um toggle de submenu e for mobile
      if (
        !this.classList.contains("submenu-toggle") &&
        window.innerWidth <= 992
      ) {
        toggleMenu();
      }
    });
  });

  // Responsividade - remove classes ao redimensionar
  window.addEventListener("resize", function () {
    if (window.innerWidth > 992) {
      sidebar.classList.remove("active");
      mobileBtn.classList.remove("active");
      if (overlay) {
        overlay.classList.remove("active");
      }
      document.body.style.overflow = "";
      // Opcional: fecha submenus ao redimensionar para desktop
      closeAllSubmenus();
    }
  });

  // Fecha todos os submenus inicialmente
  closeAllSubmenus();
});
