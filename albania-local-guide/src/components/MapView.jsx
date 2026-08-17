import { useEffect } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"

let map

export default function MapView({ places }) {
  useEffect(() => {
    if (!map) {
      map = L.map("map").setView([41.3275, 19.8187], 8)

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19
      }).addTo(map)
    }
  }, [])

  useEffect(() => {
    if (!places.length) return

    const last = places[places.length - 1]

    L.marker([last.lat, last.lng])
      .addTo(map)
      .bindPopup(last.name)
      .openPopup()

    map.flyTo([last.lat, last.lng], 12, { duration: 1.2 })
  }, [places])

  return <div id="map" style={{ height: "100%", width: "100%" }} />
}
