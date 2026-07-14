import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { submitInteractionForm } from '../features/interactions/interactionsSlice'
import './StructuredForm.css'

const TYPES = ['Visit', 'Call', 'Email', 'Conference']

export default function StructuredForm({ hcp }) {
  const dispatch = useDispatch()
  const { submitStatus } = useSelector((s) => s.interactions)
  const [interactionType, setInteractionType] = useState('Visit')
  const [notes, setNotes] = useState('')
  const [followUp, setFollowUp] = useState(false)
  const [followUpDate, setFollowUpDate] = useState('')
  const [lastResult, setLastResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const action = await dispatch(submitInteractionForm({
      hcp_id: hcp.id,
      interaction_type: interactionType,
      notes,
      follow_up_required: followUp,
      follow_up_date: followUp && followUpDate ? followUpDate : null,
    }))
    if (submitInteractionForm.fulfilled.match(action)) {
      setLastResult(action.payload)
      setNotes('')
    }
  }

  return (
    <div className="form-layout">
      <form className="log-form" onSubmit={handleSubmit}>
        <label className="field-label">Interaction type</label>
        <div className="type-row">
          {TYPES.map((t) => (
            <button
              type="button"
              key={t}
              className={`type-chip ${interactionType === t ? 'type-chip--active' : ''}`}
              onClick={() => setInteractionType(t)}
            >
              {t}
            </button>
          ))}
        </div>

        <label className="field-label" htmlFor="notes">Visit notes</label>
        <textarea
          id="notes"
          className="notes-input"
          rows={7}
          placeholder="e.g. Discussed CardioFlex Q3 trial results, Dr. Mehta requested 20 more samples, positive reception..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          required
        />

        <label className="checkbox-row">
          <input type="checkbox" checked={followUp} onChange={(e) => setFollowUp(e.target.checked)} />
          Follow-up required
        </label>

        {followUp && (
          <input
            type="date"
            className="date-input"
            value={followUpDate}
            onChange={(e) => setFollowUpDate(e.target.value)}
          />
        )}

        <button className="submit-btn" type="submit" disabled={submitStatus === 'loading' || !notes}>
          {submitStatus === 'loading' ? 'Logging…' : 'Log interaction'}
        </button>
      </form>

      <div className="ai-preview-panel">
        <div className="ai-preview-label">AI-extracted record</div>
        {!lastResult && (
          <p className="ai-preview-empty">
            Once you submit, the same LLM that powers the chat mode summarizes your
            notes and extracts topics, sentiment, and samples here.
          </p>
        )}
        {lastResult && (
          <div className="ai-preview-body">
            <div className="preview-row"><span>Summary</span><p>{lastResult.summary}</p></div>
            <div className="preview-row"><span>Sentiment</span><p>{lastResult.sentiment}</p></div>
            <div className="preview-row">
              <span>Topics</span>
              <p>{(lastResult.topics_discussed || []).join(', ') || '—'}</p>
            </div>
            <div className="preview-row"><span>Follow-up</span><p>{lastResult.follow_up_required ? 'Yes' : 'No'}</p></div>
          </div>
        )}
      </div>
    </div>
  )
}
