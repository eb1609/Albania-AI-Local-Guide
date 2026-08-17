import Chat from "./components/chat"
import MapView from "./components/MapView"
import AgentBar from "./components/AgentBar"
import { useState } from "react"

export default function App() {
  const [activeAgents, setActiveAgents] = useState([])
  const [places, setPlaces] = useState([])
  const [messages, setMessages] = useState([])

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ width: "40%", borderRight: "1px solid var(--parchment)" }}>
        <AgentBar agents={activeAgents} />
        <Chat
          messages={messages}
          setMessages={setMessages}
          onAgentsUpdate={setActiveAgents}
          onPlacesUpdate={(newPlaces) =>
            setPlaces((prev) => [...prev, ...newPlaces])
          }
        />
      </div>

      <div style={{ width: "60%" }}>
        <MapView places={places} />
      </div>
    </div>
  )
}
