import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: BASE_URL });

export async function sendChatMessage(message, formState, chatHistory) {
  const { data } = await api.post("/chat", {
    message,
    form_state: formState,
    chat_history: chatHistory,
  });
  return data;
}

export async function saveInteraction(formState) {
  const { data } = await api.post("/interactions", formState);
  return data;
}
