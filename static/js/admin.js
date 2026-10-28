/**
 * GreenCity — Admin Dashboard & Chart.js Visualizations
 */

document.addEventListener('DOMContentLoaded', () => {
  // Ensure Chart.js is loaded
  if (typeof Chart === 'undefined') return;

  // Chart Global Defaults
  Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
  Chart.defaults.color = '#64748b';

  const categoryCanvas = document.getElementById('categoryChart');
  const statusCanvas = document.getElementById('statusChart');
  const activityCanvas = document.getElementById('activityChart');

  if (!categoryCanvas || !statusCanvas) return;

  // Fetch Admin Statistics Data from JSON Endpoint
  fetch('/api/admin/stats')
    .then(res => res.json())
    .then(stats => {
      // 1. Category Breakdown Donut Chart
      if (categoryCanvas) {
        new Chart(categoryCanvas, {
          type: 'doughnut',
          data: {
            labels: stats.categories.labels,
            datasets: [{
              data: stats.categories.data,
              backgroundColor: [
                '#f59e0b', // Garbage - Amber
                '#0ea5e9', // Water - Cyan
                '#64748b', // Air - Slate
                '#10b981', // Plastic - Emerald
                '#15803d'  // Trees - Forest Green
              ],
              borderWidth: 2,
              borderColor: '#ffffff',
              hoverOffset: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  boxWidth: 12,
                  padding: 14,
                  font: { size: 12 }
                }
              }
            },
            cutout: '68%'
          }
        });
      }

      // 2. Status Breakdown Chart
      if (statusCanvas) {
        new Chart(statusCanvas, {
          type: 'pie',
          data: {
            labels: stats.statuses.labels,
            datasets: [{
              data: stats.statuses.data,
              backgroundColor: [
                '#f59e0b', // Pending (Amber)
                '#0284c7', // In Progress (Blue)
                '#10b981'  // Resolved (Green)
              ],
              borderWidth: 2,
              borderColor: '#ffffff',
              hoverOffset: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  boxWidth: 12,
                  padding: 14,
                  font: { size: 12 }
                }
              }
            }
          }
        });
      }

      // 3. Activity Trend Bar Chart
      if (activityCanvas && stats.timeline.labels.length > 0) {
        new Chart(activityCanvas, {
          type: 'bar',
          data: {
            labels: stats.timeline.labels,
            datasets: [{
              label: 'Citizen Submissions',
              data: stats.timeline.data,
              backgroundColor: '#059669',
              borderRadius: 6,
              hoverBackgroundColor: '#047857'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                ticks: { stepSize: 1 }
              },
              x: {
                grid: { display: false }
              }
            },
            plugins: {
              legend: { display: false }
            }
          }
        });
      }
    })
    .catch(err => {
      console.error('Failed to load chart analytics:', err);
    });

  // Admin Status Update Modal logic
  window.openAdminEditModal = function(id, title, status, notes) {
    const modal = document.getElementById('admin-edit-modal');
    if (!modal) return;

    document.getElementById('edit-report-id').textContent = id;
    document.getElementById('edit-report-title').textContent = title;
    document.getElementById('edit-status-select').value = status;
    document.getElementById('edit-admin-notes').value = notes || '';

    const form = document.getElementById('admin-status-form');
    form.action = `/admin/update-status/${id}`;

    modal.classList.add('open');
  };

  window.closeAdminEditModal = function() {
    const modal = document.getElementById('admin-edit-modal');
    if (modal) modal.classList.remove('open');
  };
});
