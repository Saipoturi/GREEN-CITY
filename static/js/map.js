/**
 * GreenCity — Leaflet & OpenStreetMap Interactive Maps
 */

document.addEventListener('DOMContentLoaded', () => {
  // Default coordinates (Green City Central District)
  const DEFAULT_LAT = 40.7128;
  const DEFAULT_LNG = -74.0060;
  const DEFAULT_ZOOM = 13;

  // =========================================================================
  // 1. PUBLIC REPORTS MAP (View Environmental Reports Page)
  // =========================================================================
  const reportsMapEl = document.getElementById('reports-map');
  if (reportsMapEl && typeof L !== 'undefined') {
    const map = L.map('reports-map', {
      scrollWheelZoom: false
    }).setView([DEFAULT_LAT, DEFAULT_LNG], DEFAULT_ZOOM);

    // OpenStreetMap Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | GreenCity Platform'
    }).addTo(map);

    // Custom Icon Generator based on Status
    function createCustomMarker(status, category) {
      let pinClass = 'pin-pending';
      let iconClass = 'fa-triangle-exclamation';

      if (status === 'Resolved') {
        pinClass = 'pin-resolved';
        iconClass = 'fa-check';
      } else if (status === 'In Progress') {
        pinClass = 'pin-progress';
        iconClass = 'fa-wrench';
      }

      return L.divIcon({
        className: 'custom-leaflet-pin',
        html: `<div class="custom-map-pin ${pinClass}"><i class="fa-solid ${iconClass}"></i></div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });
    }

    // Fetch reports from JSON API
    fetch('/api/reports')
      .then(res => res.json())
      .then(reports => {
        const markersGroup = L.featureGroup();

        reports.forEach(report => {
          if (report.latitude && report.longitude) {
            const marker = L.marker([report.latitude, report.longitude], {
              icon: createCustomMarker(report.status, report.category)
            });

            const photoHtml = report.photo_url 
              ? `<img src="${report.photo_url}" class="map-popup-img" alt="${report.title}">`
              : `<div style="height:80px;background:#f0fdf4;display:flex;align-items:center;justify-content:center;color:#059669;font-weight:700;"><i class="fa-solid fa-seedling" style="margin-right:6px;"></i>${report.category}</div>`;

            const popupContent = `
              <div class="map-popup-card">
                ${photoHtml}
                <div class="map-popup-body">
                  <div style="margin-bottom:6px;">
                    <span class="status-badge ${report.status.toLowerCase().replace(' ', '-')}">${report.status}</span>
                  </div>
                  <h4 class="map-popup-title">${report.title}</h4>
                  <p style="font-size:0.8rem;color:#64748b;margin-bottom:8px;"><i class="fa-solid fa-location-dot" style="color:#059669;margin-right:4px;"></i>${report.address}</p>
                  <button onclick="window.openReportModal(${report.id})" class="btn btn-primary btn-sm" style="width:100%;">
                    <i class="fa-solid fa-eye"></i> View Full Details
                  </button>
                </div>
              </div>
            `;

            marker.bindPopup(popupContent, { maxWidth: 280 });
            markersGroup.addLayer(marker);
          }
        });

        markersGroup.addTo(map);

        // Adjust bounds if we have markers
        if (markersGroup.getLayers().length > 0) {
          map.fitBounds(markersGroup.getBounds(), { padding: [40, 40], maxZoom: 15 });
        }
      })
      .catch(err => {
        console.error('Failed to load reports onto map:', err);
      });
  }

  // =========================================================================
  // 2. LOCATION PICKER MAP (Report an Issue Page)
  // =========================================================================
  const pickerMapEl = document.getElementById('picker-map');
  if (pickerMapEl && typeof L !== 'undefined') {
    const latInput = document.getElementById('latitude-input');
    const lngInput = document.getElementById('longitude-input');
    const addressInput = document.getElementById('address-input');
    const locateBtn = document.getElementById('locate-me-btn');

    const initialLat = latInput && latInput.value ? parseFloat(latInput.value) : DEFAULT_LAT;
    const initialLng = lngInput && lngInput.value ? parseFloat(lngInput.value) : DEFAULT_LNG;

    const pickerMap = L.map('picker-map', {
      scrollWheelZoom: false
    }).setView([initialLat, initialLng], DEFAULT_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(pickerMap);

    const pickerIcon = L.divIcon({
      className: 'custom-leaflet-pin',
      html: `<div class="custom-map-pin pin-pending" style="background:#059669;"><i class="fa-solid fa-location-crosshairs"></i></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
    });

    let marker = L.marker([initialLat, initialLng], {
      draggable: true,
      icon: pickerIcon
    }).addTo(pickerMap);

    // Function to update inputs from coordinate values
    function updateCoordinates(lat, lng) {
      if (latInput) latInput.value = lat.toFixed(6);
      if (lngInput) lngInput.value = lng.toFixed(6);
      const coordDisplay = document.getElementById('coord-display');
      if (coordDisplay) {
        coordDisplay.textContent = `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`;
      }
    }

    // Initialize with current marker position
    updateCoordinates(initialLat, initialLng);

    // Marker drag event
    marker.on('dragend', (e) => {
      const pos = e.target.getLatLng();
      updateCoordinates(pos.lat, pos.lng);
    });

    // Map click event
    pickerMap.on('click', (e) => {
      marker.setLatLng(e.latlng);
      updateCoordinates(e.latlng.lat, e.latlng.lng);
    });

    // Browser Geolocation Support
    if (locateBtn && navigator.geolocation) {
      locateBtn.addEventListener('click', () => {
        locateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Detecting...';
        locateBtn.disabled = true;

        navigator.geolocation.getCurrentPosition(
          (position) => {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;
            pickerMap.setView([userLat, userLng], 15);
            marker.setLatLng([userLat, userLng]);
            updateCoordinates(userLat, userLng);

            locateBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Location Set!';
            setTimeout(() => {
              locateBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Current Location';
              locateBtn.disabled = false;
            }, 2500);
          },
          (error) => {
            console.warn('Geolocation failed:', error.message);
            alert('Unable to retrieve your precise location. Please click on the map or enter your address manually.');
            locateBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Current Location';
            locateBtn.disabled = false;
          },
          { enableHighAccuracy: true, timeout: 8000 }
        );
      });
    }
  }
});
