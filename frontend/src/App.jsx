import InteractionForm from "./components/InteractionForm";
import AIChatPanel from "./components/AIChatPanel";

export default function App() {
  return (
    <div className="app-shell">
      <div className="split-screen">
        <InteractionForm />
        <AIChatPanel />
      </div>
    </div>
  );
}
