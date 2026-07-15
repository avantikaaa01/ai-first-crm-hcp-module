import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { createHcp } from '../features/interactions/hcpSlice'
import './AddHcpModal.css'

const TIERS = ['High Value', 'Growth', 'Maintain']

export default function AddHcpModal({ onClose }) {
  const dispatch = useDispatch()
  const { createStatus } = useSelector((s) => s.hcps)
  const [form, setForm] = useState({ name: '', specialty: '', hospital: '', tier: 'Growth' })

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const action = await dispatch(createHcp(form))
    if (createHcp.fulfilled.match(action)) {
      onClose()
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add HCP</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <label className="modal-label">Doctor's name</label>
          <input
            className="modal-input"
            placeholder="Dr. Full Name"
            value={form.name}
            onChange={update('name')}
            required
          />

          <label className="modal-label">Specialty</label>
          <input
            className="modal-input"
            placeholder="e.g. Cardiology"
            value={form.specialty}
            onChange={update('specialty')}
          />

          <label className="modal-label">Hospital / Clinic</label>
          <input
            className="modal-input"
            placeholder="e.g. Fortis Bengaluru"
            value={form.hospital}
            onChange={update('hospital')}
          />

          <label className="modal-label">Tier</label>
          <div className="modal-tier-row">
            {TIERS.map((t) => (
              <button
                type="button"
                key={t}
                className={`modal-tier-chip ${form.tier === t ? 'modal-tier-chip--active' : ''}`}
                onClick={() => setForm((f) => ({ ...f, tier: t }))}
              >
                {t}
              </button>
            ))}
          </div>

          <button className="modal-submit" type="submit" disabled={!form.name || createStatus === 'loading'}>
            {createStatus === 'loading' ? 'Adding…' : 'Add HCP'}
          </button>
        </form>
      </div>
    </div>
  )
}
