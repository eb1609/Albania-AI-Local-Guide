export default function PlaceChip({ name, onClick }) {
  return (
    <span
      className="place-chip"
      onClick={onClick}
      style={{
        padding: "4px 8px",
        background: "var(--parchment)",
        borderRadius: 6,
        cursor: "pointer",
        marginRight: 6
      }}
    >
      {name}
    </span>
  )
}
