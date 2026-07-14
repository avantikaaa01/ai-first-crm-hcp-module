import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const fetchHcps = createAsyncThunk('hcps/fetch', async () => {
  const res = await fetch(`${API_BASE}/api/hcps/`)
  if (!res.ok) throw new Error('Failed to fetch HCPs')
  return res.json()
})

const hcpSlice = createSlice({
  name: 'hcps',
  initialState: { list: [], selectedId: null, status: 'idle', error: null },
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
  },
})

export const { selectHcp } = hcpSlice.actions
export default hcpSlice.reducer
