import React, { useState } from 'react'
import StructuredForm from './StructuredForm'
import ChatInterface from './ChatInterface'
import RecentInteractions from './RecentInteractions'
import './LogInteractionScreen.css'

export default function LogInteractionScreen({ hcp }) {
  const [mode, setMode] = useState('chat') // 'chat' | 'form'

  return (
    <div className="log-screen">
      <div className="log-screen-header">
        <div>
          <h1 className="log-title">Log Interaction</h1>
          <p className="log-subtitle">with {hcp.name} · {hcp.specialty}</p>
        </div>

        <div className="mode-toggle" role="tablist" aria-label="Log interaction mode">
          <button
            role="tab"
            aria-selected={mode === 'chat'}
            className={`mode-btn ${mode === 'chat' ? 'mode-btn--active' : ''}`}
            onClick={() => setMode('chat')}
          >
            Conversational
          </button>
          <button
            role="tab"
            aria-selected={mode === 'form'}
            className={`mode-btn ${mode === 'form' ? 'mode-btn--active' : ''}`}
            onClick={() => setMode('form')}
          >
            Structured Form
          </button>
        </div>
      </div>

      {mode === 'chat' ? <ChatInterface hcp={hcp} /> : <StructuredForm hcp={hcp} />}

      {/* Pulled straight from the database, so it survives a page refresh -
          proof the CRM record is real and persisted, not just chat state. */}
      <RecentInteractions hcp={hcp} />
    </div>
  )
}
