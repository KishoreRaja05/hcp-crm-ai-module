import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "";

export const api = axios.create({ baseURL: BASE_URL });

if (!import.meta.env.VITE_API_URL) {
  api.defaults.baseURL = "http://127.0.0.1:8000";
}

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
