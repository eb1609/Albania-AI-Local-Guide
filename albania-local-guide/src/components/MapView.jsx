import { useEffect, useRef } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"

// Fix standard Leaflet marker icon issues in React/Webpack
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png"
import markerIcon from "leaflet/dist/images/marker-icon.png"
import markerShadow from "leaflet/dist/images/marker-shadow.png"

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

export default function MapView({ places = [] }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const layerGroupRef = useRef(null)

  // 1. Initialize map instance once
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    // Initialize map
    const map = L.map(mapRef.current).setView([41.3275, 19.8187], 8)

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map)

    // Store map instance and a layer group to manage markers
    mapInstanceRef.current = map
    layerGroupRef.current = L.layerGroup().addTo(map)

    // Clean up map instance on unmount
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // 2. Add markers & adjust view when `places` update
  useEffect(() => {
    const map = mapInstanceRef.current
    const layerGroup = layerGroupRef.current

    if (!map || !layerGroup || !places.length) return

    // Clear old markers so they don't stack indefinitely
    layerGroup.clearLayers()

    const bounds = []

    places.forEach((place) => {
      const lat = Number(place.lat)
      const lng = Number(place.lng)

      if (isNaN(lat) || isNaN(lng)) return

      bounds.push([lat, lng])

      // Add marker to layer group
      L.marker([lat, lng])
        .addTo(layerGroup)
        .bindPopup(`
          <div style="color: #000;">
            <strong>${place.name}</strong>
            ${place.address ? `<br/><small>${place.address}</small>` : ""}
          </div>
        `)
    })

    // Auto-fit bounds if multiple places, or flyTo single place
    if (bounds.length === 1) {
      map.flyTo(bounds[0], 13, { duration: 1.2 })
    } else if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [50, 50] })
    }
  }, [places])

  return <div ref={mapRef} style={{ height: "100%", width: "100%" }} />
}