import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchHcps, selectHcp } from './features/interactions/hcpSlice'
import LogInteractionScreen from './components/LogInteractionScreen'
import AddHcpModal from './components/AddHcpModal'
import './App.css'

export default function App() {
  const dispatch = useDispatch()
  const { list: hcps, selectedId, status } = useSelector((s) => s.hcps)
  const [showAddModal, setShowAddModal] = useState(false)

  useEffect(() => {
    dispatch(fetchHcps())
  }, [dispatch])

  const selectedHcp = hcps.find((h) => h.id === selectedId)

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">M</span>
          <span className="brand-name">MedConnect <span className="brand-sub">HCP Module</span></span>
        </div>
        <div className="header-meta">Field Rep: <strong>Avantika S.</strong></div>
      </header>

      <div className="app-body">
        <aside className="hcp-rail">
          <div className="rail-top">
            <div className="rail-label">Your HCPs</div>
            <button className="add-hcp-btn" onClick={() => setShowAddModal(true)}>+ Add HCP</button>
          </div>
          {status === 'loading' && <div className="rail-empty">Loading HCPs…</div>}
          {status === 'failed' && (
            <div className="rail-empty">
              Couldn't reach the API. Is the backend running on :8000?
            </div>
          )}
          {hcps.map((h) => (
            <button
              key={h.id}
              className={`hcp-card ${h.id === selectedId ? 'hcp-card--active' : ''}`}
              onClick={() => dispatch(selectHcp(h.id))}
            >
              <span className="hcp-avatar">{h.name.split(' ').map(n => n[0]).slice(-2).join('')}</span>
              <span className="hcp-card-info">
                <span className="hcp-card-name">{h.name}</span>
                <span className="hcp-card-sub">{h.specialty} · {h.hospital}</span>
              </span>
              {h.tier && <span className={`tier-pill tier-${h.tier.replace(/\s+/g, '-').toLowerCase()}`}>{h.tier}</span>}
            </button>
          ))}
        </aside>

        <main className="main-panel">
          {selectedHcp ? (
            <LogInteractionScreen hcp={selectedHcp} />
          ) : (
            <div className="empty-state">Select an HCP on the left to log an interaction.</div>
          )}
        </main>
      </div>

      {showAddModal && <AddHcpModal onClose={() => setShowAddModal(false)} />}
    </div>
  )
}
