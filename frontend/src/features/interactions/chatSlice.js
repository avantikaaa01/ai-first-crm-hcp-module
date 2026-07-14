import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const sendChatMessage = createAsyncThunk(
  'chat/send',
  async ({ sessionId, message, hcpId }) => {
    const res = await fetch(`${API_BASE}/api/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message, hcp_id: hcpId }),
    })
    if (!res.ok) throw new Error('Chat request failed')
    const data = await res.json()
    return { ...data, hcpId }
  }
)

function emptySession() {
  return {
    sessionId: crypto.randomUUID(),
    messages: [],        // {role: 'user'|'agent', text}
    extractedFields: [], // running log of tool calls, for the "live extraction" panel
    status: 'idle',
  }
}

const chatSlice = createSlice({
  name: 'chat',
  // Each HCP gets its own isolated session, so switching doctors in the
  // sidebar doesn't leak one doctor's chat history/tool calls into another's.
  initialState: { sessionsByHcp: {} },
  reducers: {
    addUserMessage: (state, action) => {
      const { hcpId, text } = action.payload
      if (!state.sessionsByHcp[hcpId]) state.sessionsByHcp[hcpId] = emptySession()
      state.sessionsByHcp[hcpId].messages.push({ role: 'user', text })
    },
    resetSession: (state, action) => {
      const hcpId = action.payload
      state.sessionsByHcp[hcpId] = emptySession()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state, action) => {
        const { hcpId } = action.meta.arg
        if (!state.sessionsByHcp[hcpId]) state.sessionsByHcp[hcpId] = emptySession()
        state.sessionsByHcp[hcpId].status = 'loading'
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        const { hcpId, reply, tool_calls } = action.payload
        const session = state.sessionsByHcp[hcpId] || emptySession()
        session.status = 'succeeded'
        session.messages.push({ role: 'agent', text: reply })
        if (tool_calls) tool_calls.forEach((tc) => session.extractedFields.push(tc))
        state.sessionsByHcp[hcpId] = session
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        const { hcpId } = action.meta.arg
        if (state.sessionsByHcp[hcpId]) state.sessionsByHcp[hcpId].status = 'failed'
      })
  },
})

export const { addUserMessage, resetSession } = chatSlice.actions
export default chatSlice.reducer
