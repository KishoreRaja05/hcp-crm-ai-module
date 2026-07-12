import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  hcp_name: "",
  interaction_type: "Meeting",
  date: "",
  time: "",
  attendees: "",
  topics_discussed: "",
  materials_shared: [],
  samples_distributed: [],
  sentiment: "",
  outcomes: "",
  follow_up_actions: "",
};

const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {
    setFormState: (state, action) => {
      return { ...state, ...action.payload };
    },
    resetForm: () => initialState,
  },
});

export const { setFormState, resetForm } = interactionSlice.actions;
export default interactionSlice.reducer;
