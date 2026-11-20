/**
 * College Complaint & Resolution System - Main Client-side Script
 * Vanilla JavaScript (No external libraries)
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const sidebar = document.getElementById('appSidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  if (mobileMenuBtn && sidebar && sidebarOverlay) {
    mobileMenuBtn.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      sidebarOverlay.classList.toggle('show');
    });

    sidebarOverlay.addEventListener('click', function () {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('show');
    });
  }

  // 2. Alert Dismissal
  const alertCloseButtons = document.querySelectorAll('.alert-close');
  alertCloseButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        alert.style.transition = 'all 0.2s ease';
        setTimeout(function () {
          alert.remove();
        }, 200);
      }
    });
  });

  // Auto-dismiss success flash alerts after 5 seconds
  setTimeout(function () {
    const successAlerts = document.querySelectorAll('.alert-success, .alert-info');
    successAlerts.forEach(function (alert) {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      alert.style.transition = 'all 0.3s ease';
      setTimeout(function () {
        alert.remove();
      }, 300);
    });
  }, 5000);

  // 3. Demo Account Autofill on Login Page
  const demoButtons = document.querySelectorAll('.demo-fill-btn');
  demoButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      const u = this.getAttribute('data-user');
      const p = this.getAttribute('data-pass');
      const usernameInput = document.getElementById('username');
      const passwordInput = document.getElementById('password');

      if (usernameInput && passwordInput) {
        usernameInput.value = u;
        passwordInput.value = p;
        usernameInput.focus();

        // Highlight form
        usernameInput.style.borderColor = '#2563eb';
        passwordInput.style.borderColor = '#2563eb';
        setTimeout(function () {
          usernameInput.style.borderColor = '';
          passwordInput.style.borderColor = '';
        }, 800);
      }
    });
  });

  // 4. Client-side Real-time Search & Filter for Tables
  const clientSearchInput = document.getElementById('clientTableSearch');
  const clientCategoryFilter = document.getElementById('clientCategoryFilter');
  const clientStatusFilter = document.getElementById('clientStatusFilter');
  const filterableTable = document.getElementById('filterableTable');

  function filterTable() {
    if (!filterableTable) return;

    const searchTerm = clientSearchInput ? clientSearchInput.value.toLowerCase().trim() : '';
    const selectedCategory = clientCategoryFilter ? clientCategoryFilter.value.toLowerCase().trim() : '';
    const selectedStatus = clientStatusFilter ? clientStatusFilter.value.toLowerCase().trim() : '';

    const rows = filterableTable.querySelectorAll('tbody tr.table-row-item');
    let visibleCount = 0;

    rows.forEach(function (row) {
      const text = row.textContent.toLowerCase();
      const rowCategory = (row.getAttribute('data-category') || '').toLowerCase();
      const rowStatus = (row.getAttribute('data-status') || '').toLowerCase();

      const matchesSearch = !searchTerm || text.includes(searchTerm);
      const matchesCategory = !selectedCategory || rowCategory === selectedCategory;
      const matchesStatus = !selectedStatus || rowStatus === selectedStatus;

      if (matchesSearch && matchesCategory && matchesStatus) {
        row.style.display = '';
        visibleCount++;
      } else {
        row.style.display = 'none';
      }
    });

    const emptyNotice = document.getElementById('noFilterResultsRow');
    if (emptyNotice) {
      emptyNotice.style.display = visibleCount === 0 ? '' : 'none';
    }
  }

  if (clientSearchInput) {
    clientSearchInput.addEventListener('input', filterTable);
  }
  if (clientCategoryFilter) {
    clientCategoryFilter.addEventListener('change', filterTable);
  }
  if (clientStatusFilter) {
    clientStatusFilter.addEventListener('change', filterTable);
  }

  // 5. Modal Dialog Trigger & Close Logic
  const modalTriggers = document.querySelectorAll('[data-modal-target]');
  modalTriggers.forEach(function (trigger) {
    trigger.addEventListener('click', function (e) {
      e.preventDefault();
      const targetSelector = this.getAttribute('data-modal-target');
      const targetModal = document.querySelector(targetSelector);
      if (targetModal) {
        targetModal.classList.add('show');
      }
    });
  });

  const modalCloses = document.querySelectorAll('[data-modal-close]');
  modalCloses.forEach(function (closeBtn) {
    closeBtn.addEventListener('click', function () {
      const modal = this.closest('.modal-backdrop');
      if (modal) {
        modal.classList.remove('show');
      }
    });
  });

  // Close modal when clicking on backdrop
  const modalBackdrops = document.querySelectorAll('.modal-backdrop');
  modalBackdrops.forEach(function (backdrop) {
    backdrop.addEventListener('click', function (e) {
      if (e.target === this) {
        this.classList.remove('show');
      }
    });
  });

  // Close modal on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      modalBackdrops.forEach(function (modal) {
        modal.classList.remove('show');
      });
    }
  });

  // 6. Dynamic Department -> Staff Dropdown for Admin Assignment
  const deptSelect = document.getElementById('assignDeptSelect');
  const staffSelect = document.getElementById('assignStaffSelect');

  if (deptSelect && staffSelect) {
    deptSelect.addEventListener('change', function () {
      const deptId = this.value;
      staffSelect.innerHTML = '<option value="">-- Assign to Department Pool (Unassigned Staff) --</option>';

      if (!deptId) return;

      fetch('/api/departments/' + encodeURIComponent(deptId) + '/staff')
        .then(function (res) {
          if (!res.ok) throw new Error('Network error');
          return res.json();
        })
        .then(function (staffList) {
          if (staffList.length === 0) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = 'No staff currently registered in this department';
            opt.disabled = true;
            staffSelect.appendChild(opt);
          } else {
            staffList.forEach(function (staff) {
              const opt = document.createElement('option');
              opt.value = staff.id;
              opt.textContent = staff.full_name + ' (' + staff.email + ')';
              staffSelect.appendChild(opt);
            });
          }
        })
        .catch(function (err) {
          console.error('Error fetching staff list:', err);
        });
    });
  }

  // 7. Interactive Feedback Star Rating Display
  const starInputs = document.querySelectorAll('.star-rating input[type="radio"]');
  const ratingHelpText = document.getElementById('ratingDescriptionText');
  const ratingLabels = {
    '1': '1 Star - Very Poor (Unsatisfactory resolution)',
    '2': '2 Stars - Poor (Needs improvement)',
    '3': '3 Stars - Average (Resolved satisfactorily)',
    '4': '4 Stars - Good (Quick and helpful response)',
    '5': '5 Stars - Excellent (Outstanding & prompt resolution)'
  };

  starInputs.forEach(function (radio) {
    radio.addEventListener('change', function () {
      if (ratingHelpText && ratingLabels[this.value]) {
        ratingHelpText.textContent = ratingLabels[this.value];
        ratingHelpText.style.fontWeight = '600';
        ratingHelpText.style.color = '#b45309';
      }
    });
  });
});
