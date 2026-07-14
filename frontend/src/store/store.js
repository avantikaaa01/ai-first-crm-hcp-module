import { configureStore } from '@reduxjs/toolkit'
import interactionsReducer from '../features/interactions/interactionsSlice'
import hcpReducer from '../features/interactions/hcpSlice'
import chatReducer from '../features/interactions/chatSlice'

export const store = configureStore({
  reducer: {
    interactions: interactionsReducer,
    hcps: hcpReducer,
    chat: chatReducer,
  },
})
