import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchInteractions } from '../features/interactions/interactionsSlice'
import './RecentInteractions.css'

export default function RecentInteractions({ hcp }) {
  const dispatch = useDispatch()
  const { list, status } = useSelector((s) => s.interactions)

  useEffect(() => {
    dispatch(fetchInteractions(hcp.id))
  }, [dispatch, hcp.id])

  const hcpInteractions = list.filter((i) => i.hcp_id === hcp.id)

  return (
    <div className="recent-panel">
      <div className="recent-header">
        <span className="recent-label">Logged history · from the database</span>
        <button className="refresh-btn" onClick={() => dispatch(fetchInteractions(hcp.id))}>
          Refresh
        </button>
      </div>

      {status === 'loading' && hcpInteractions.length === 0 && (
        <p className="recent-empty">Loading…</p>
      )}
      {status !== 'loading' && hcpInteractions.length === 0 && (
        <p className="recent-empty">
          Nothing logged for {hcp.name} yet. Log an interaction above and it'll appear
          here immediately — and stay here even if you refresh the page.
        </p>
      )}

      <div className="recent-list">
        {hcpInteractions.map((i) => (
          <div key={i.id} className="recent-card">
            <div className="recent-card-top">
              <span className="recent-type">{i.interaction_type || 'Interaction'}</span>
              <span className={`recent-sentiment recent-sentiment--${(i.sentiment || '').toLowerCase()}`}>
                {i.sentiment}
              </span>
              <span className="recent-date">
                {i.date ? new Date(i.date).toLocaleDateString() : ''}
              </span>
            </div>
            <p className="recent-summary">{i.summary}</p>
            <div className="recent-tags">
              {(i.topics_discussed || []).map((t, idx) => (
                <span key={idx} className="recent-tag">{t}</span>
              ))}
              {i.follow_up_required && (
                <span className="recent-tag recent-tag--followup">
                  Follow-up: {i.follow_up_date ? new Date(i.follow_up_date).toLocaleDateString() : 'pending'}
                </span>
              )}
              {i.compliance_flag && (
                <span className="recent-tag recent-tag--flag">Compliance flag</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
