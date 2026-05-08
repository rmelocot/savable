const map = L.map('map').setView([43.6532, -79.3832], 10)

L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
        attribution: '&copy; OpenStreetMap contributors'
    }
).addTo(map)

fetch("http://127.0.0.1:5000/places")
    .then(res => res.json())
    .then(data => {

        data.forEach(place => {

            if (
                place.latitude &&
                place.longitude
            ) {

                L.marker([
                    place.latitude,
                    place.longitude
                ])
                .addTo(map)
                .bindPopup(`
                    <b>${place.name || "Unknown"}</b><br>
                    ${place.category}<br><br>

                    <a href="${place.tiktok_url}"
                       target="_blank">
                       Open TikTok
                    </a>
                `)
            }
        })
    })