// ============================================
// OFF-CANVAS MENU COM HANDLE - FARMEDICARE
// Menu lateral deslizante com alça/aba lateral
// ============================================

document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.querySelector(".sidebar-overlay");
  const menuHandle = document.querySelector(".menu-handle");

  if (!sidebar || !menuHandle) {
    return;
  }

  // Função para abrir o menu
  function openMenu() {
    sidebar.classList.add("active");
    document.body.classList.add("menu-open");
    if (overlay) {
      overlay.classList.add("active");
    }
    document.body.style.overflow = "hidden";
  }

  // Função para fechar o menu
  function closeMenu() {
    sidebar.classList.remove("active");
    document.body.classList.remove("menu-open");
    if (overlay) {
      overlay.classList.remove("active");
    }
    document.body.style.overflow = "";
    closeAllSubmenus();
  }

  // Função para alternar menu (toggle)
  function toggleMenu() {
    if (sidebar.classList.contains("active")) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  // Função para toggle dos submenus
  function toggleSubmenu(submenuToggle) {
    const parent = submenuToggle.closest(".has-submenu");
    
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

  // Event listener para o handle (alça)
  menuHandle.addEventListener("click", function(e) {
    e.preventDefault();
    e.stopPropagation();
    toggleMenu();
  });

  // Event listener para o overlay (fechar ao clicar fora)
  if (overlay) {
    overlay.addEventListener("click", function() {
      closeMenu();
    });
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

  // Tecla ESC fecha o menu e submenus
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeMenu();
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
        closeMenu();
      }
    });
  });

  // Responsividade - remove classes ao redimensionar para desktop
  window.addEventListener("resize", function () {
    if (window.innerWidth > 992) {
      closeMenu();
      closeAllSubmenus();
    }
  });

  // Fecha todos os submenus inicialmente
  closeAllSubmenus();

  // Suporte a gestos de swipe (opcional - para mobile)
  let touchStartX = 0;
  let touchEndX = 0;

  document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
  }, { passive: true });

  document.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  }, { passive: true });

  function handleSwipe() {
    const swipeDistance = touchEndX - touchStartX;
    const minSwipeDistance = 50;

    // Swipe da esquerda para direita abre o menu
    if (swipeDistance > minSwipeDistance && touchStartX < 50 && !sidebar.classList.contains("active")) {
      openMenu();
    }

    // Swipe da direita para esquerda fecha o menu
    if (swipeDistance < -minSwipeDistance && sidebar.classList.contains("active")) {
      closeMenu();
    }
  }
});
