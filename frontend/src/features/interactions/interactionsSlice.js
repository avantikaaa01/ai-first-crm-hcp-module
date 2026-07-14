import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const fetchInteractions = createAsyncThunk(
  'interactions/fetch',
  async (hcpId) => {
    const url = hcpId ? `${API_BASE}/api/interactions/?hcp_id=${hcpId}` : `${API_BASE}/api/interactions/`
    const res = await fetch(url)
    if (!res.ok) throw new Error('Failed to fetch interactions')
    return res.json()
  }
)

export const submitInteractionForm = createAsyncThunk(
  'interactions/submitForm',
  async (payload) => {
    const res = await fetch(`${API_BASE}/api/interactions/form`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Failed to log interaction')
    }
    return res.json()
  }
)

export const editInteraction = createAsyncThunk(
  'interactions/edit',
  async ({ id, changes }) => {
    const res = await fetch(`${API_BASE}/api/interactions/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(changes),
    })
    if (!res.ok) throw new Error('Failed to edit interaction')
    return res.json()
  }
)

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: { list: [], status: 'idle', submitStatus: 'idle', error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => { state.status = 'loading' })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.list = action.payload
      })
      .addCase(submitInteractionForm.pending, (state) => { state.submitStatus = 'loading' })
      .addCase(submitInteractionForm.fulfilled, (state, action) => {
        state.submitStatus = 'succeeded'
        state.list.unshift(action.payload)
      })
      .addCase(submitInteractionForm.rejected, (state, action) => {
        state.submitStatus = 'failed'
        state.error = action.error.message
      })
      .addCase(editInteraction.fulfilled, (state, action) => {
        const idx = state.list.findIndex((i) => i.id === action.payload.id)
        if (idx !== -1) state.list[idx] = action.payload
      })
  },
})

export default interactionsSlice.reducer
