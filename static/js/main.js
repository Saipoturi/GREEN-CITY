/**
 * GreenCity — Main Client Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Toggle
  const mobileToggle = document.querySelector('.mobile-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      const icon = mobileToggle.querySelector('i');
      if (icon) {
        if (navLinks.classList.contains('open')) {
          icon.classList.remove('fa-bars');
          icon.classList.add('fa-xmark');
        } else {
          icon.classList.remove('fa-xmark');
          icon.classList.add('fa-bars');
        }
      }
    });
  }

  // 2. Alert Dismissal
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // Auto dismiss alerts after 6 seconds
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(alert => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 400);
    });
  }, 6000);

  // 3. File Upload Preview & Drag-and-Drop
  const dropzone = document.getElementById('photo-dropzone');
  const fileInput = document.getElementById('photo-input');
  const previewContainer = document.getElementById('upload-preview');
  const previewImg = document.getElementById('preview-image');

  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        fileInput.files = files;
        handleFilePreview(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFilePreview(e.target.files[0]);
      }
    });

    function handleFilePreview(file) {
      if (!file.type.startsWith('image/')) {
        alert('Please upload a valid image file (PNG, JPG, JPEG, WEBP, GIF).');
        fileInput.value = '';
        if (previewContainer) previewContainer.style.display = 'none';
        return;
      }

      // Check max size 16MB
      if (file.size > 16 * 1024 * 1024) {
        alert('File size exceeds 16MB limit.');
        fileInput.value = '';
        if (previewContainer) previewContainer.style.display = 'none';
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        if (previewImg && previewContainer) {
          previewImg.src = e.target.result;
          previewContainer.style.display = 'block';
        }
      };
      reader.readAsDataURL(file);
    }
  }

  // 4. Modal Interactions
  window.openReportModal = function(reportId) {
    const modal = document.getElementById('report-modal');
    if (!modal) return;

    // Fetch report details via JSON API
    fetch(`/api/reports/${reportId}`)
      .then(res => {
        if (!res.ok) throw new Error('Network error');
        return res.json();
      })
      .then(report => {
        document.getElementById('modal-title').textContent = report.title;
        document.getElementById('modal-category').textContent = report.category;
        document.getElementById('modal-address').textContent = report.address;
        document.getElementById('modal-date').textContent = new Date(report.created_at).toLocaleString();
        document.getElementById('modal-submitter').textContent = report.submitter_name;
        document.getElementById('modal-desc').textContent = report.description;
        document.getElementById('modal-admin-notes').textContent = report.admin_notes || 'Pending administrative review.';

        const statusBadge = document.getElementById('modal-status');
        statusBadge.textContent = report.status;
        statusBadge.className = `status-badge ${report.status.toLowerCase().replace(' ', '-')}`;

        const photoElem = document.getElementById('modal-photo');
        if (report.photo_url) {
          photoElem.src = report.photo_url;
          photoElem.style.display = 'block';
        } else {
          photoElem.style.display = 'none';
        }

        modal.classList.add('open');
      })
      .catch(err => {
        console.error('Error fetching report:', err);
        alert('Could not load report details.');
      });
  };

  window.closeReportModal = function() {
    const modal = document.getElementById('report-modal');
    if (modal) modal.classList.remove('open');
  };

  // Close modal when clicking backdrop or ESC
  const modal = document.getElementById('report-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeReportModal();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('open')) {
        closeReportModal();
      }
    });
  }
});
