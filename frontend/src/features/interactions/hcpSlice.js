import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const fetchHcps = createAsyncThunk('hcps/fetch', async () => {
  const res = await fetch(`${API_BASE}/api/hcps/`)
  if (!res.ok) throw new Error('Failed to fetch HCPs')
  return res.json()
})

export const createHcp = createAsyncThunk('hcps/create', async (payload) => {
  const res = await fetch(`${API_BASE}/api/hcps/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to add HCP')
  return res.json()
})

const hcpSlice = createSlice({
  name: 'hcps',
  initialState: { list: [], selectedId: null, status: 'idle', createStatus: 'idle', error: null },
  reducers: {
    selectHcp: (state, action) => {
      state.selectedId = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => { state.status = 'loading' })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.list = action.payload
        if (!state.selectedId && action.payload.length) {
          state.selectedId = action.payload[0].id
        }
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      .addCase(createHcp.pending, (state) => { state.createStatus = 'loading' })
      .addCase(createHcp.fulfilled, (state, action) => {
        state.createStatus = 'succeeded'
        state.list.unshift(action.payload)
        state.selectedId = action.payload.id
      })
      .addCase(createHcp.rejected, (state, action) => {
        state.createStatus = 'failed'
        state.error = action.error.message
      })
  },
})

export const { selectHcp } = hcpSlice.actions
export default hcpSlice.reducer
