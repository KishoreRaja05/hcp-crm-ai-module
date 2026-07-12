import { createSlice } from "@reduxjs/toolkit";

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: [], // { role: 'user' | 'assistant', content: string }
    loading: false,
    lastToolCalls: [],
  },
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setLastToolCalls: (state, action) => {
      state.lastToolCalls = action.payload;
    },
  },
});

export const { addMessage, setLoading, setLastToolCalls } = chatSlice.actions;
export default chatSlice.reducer;
