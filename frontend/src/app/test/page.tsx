export default function TestPage() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Test Page</h1>
      <p>Cette page de test fonctionne !</p>
      <p>Timestamp: {new Date().toISOString()}</p>
    </div>
  )
}
