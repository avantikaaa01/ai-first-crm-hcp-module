import React, { useState, useRef, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { sendChatMessage, addUserMessage } from '../features/interactions/chatSlice'
import './ChatInterface.css'

const EMPTY_SESSION = { sessionId: null, messages: [], extractedFields: [], status: 'idle' }

export default function ChatInterface({ hcp }) {
  const dispatch = useDispatch()
  const session = useSelector((s) => s.chat.sessionsByHcp[hcp.id]) || EMPTY_SESSION
  const { messages, extractedFields, status, sessionId } = session
  const [input, setInput] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = (e) => {
    e.preventDefault()
    if (!input.trim()) return
    dispatch(addUserMessage({ hcpId: hcp.id, text: input }))
    dispatch(sendChatMessage({ sessionId: sessionId || crypto.randomUUID(), message: input, hcpId: hcp.id }))
    setInput('')
  }

  return (
    <div className="chat-layout">
      <div className="chat-panel">
        <div className="chat-scroll">
          {messages.length === 0 && (
            <div className="chat-hint">
              Tell the agent what happened in plain language — e.g. "Met Dr. {hcp.name.split(' ').slice(-1)[0]}
              {' '}today, went well, she wants more CardioFlex samples, follow up in 2 weeks."
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`bubble-row bubble-row--${m.role}`}>
              <div className={`bubble bubble--${m.role}`}>{m.text}</div>
            </div>
          ))}
          {status === 'loading' && (
            <div className="bubble-row bubble-row--agent">
              <div className="bubble bubble--agent bubble--typing">Thinking…</div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form className="chat-input-row" onSubmit={handleSend}>
          <input
            className="chat-input"
            placeholder="Describe your interaction…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button className="chat-send" type="submit" disabled={!input.trim() || status === 'loading'}>
            Send
          </button>
        </form>
      </div>

      <div className="extraction-panel">
        <div className="extraction-label">Agent activity</div>
        {extractedFields.length === 0 && (
          <p className="extraction-empty">
            As the agent calls tools (log_interaction, check_compliance, schedule_followup…)
            you'll see each call appear here — full transparency into what's being written
            to the CRM.
          </p>
        )}
        <div className="extraction-list">
          {extractedFields.map((tc, i) => (
            <ToolCallCard key={i} toolCall={tc} />
          ))}
        </div>
      </div>
    </div>
  )
}

function ToolCallCard({ toolCall }) {
  let parsed = {}
  try { parsed = JSON.parse(toolCall.output) } catch { /* noop */ }

  return (
    <div className="tool-card">
      <div className="tool-card-name">{toolCall.tool}</div>
      <div className="tool-card-body">
        {Object.entries(parsed).map(([k, v]) => (
          <div key={k} className="tool-card-field">
            <span>{k.replace(/_/g, ' ')}</span>
            <p>{Array.isArray(v) ? v.join(', ') || '—' : String(v)}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
