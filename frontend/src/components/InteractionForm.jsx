import { useState } from "react";
import { useSelector } from "react-redux";
import { saveInteraction } from "../api/client";

const SENTIMENTS = ["Positive", "Neutral", "Negative"];

export default function InteractionForm() {
  const form = useSelector((state) => state.interaction);
  const [saveStatus, setSaveStatus] = useState("");

  const handleSave = async () => {
    setSaveStatus("Saving...");
    try {
      await saveInteraction(form);
      setSaveStatus("Saved ✓");
    } catch {
      setSaveStatus("Save failed");
    }
    setTimeout(() => setSaveStatus(""), 2500);
  };

  return (
    <div className="panel form-panel">
      <h2 className="panel-title">Log HCP Interaction</h2>
      <div className="panel-subtitle">Interaction Details</div>

      <div className="field-row">
        <div className="field">
          <label>HCP Name</label>
          <input value={form.hcp_name} readOnly placeholder="Search or select HCP..." />
        </div>
        <div className="field">
          <label>Interaction Type</label>
          <input value={form.interaction_type} readOnly />
        </div>
      </div>

      <div className="field-row">
        <div className="field">
          <label>Date</label>
          <input value={form.date} readOnly placeholder="DD-MM-YYYY" />
        </div>
        <div className="field">
          <label>Time</label>
          <input value={form.time} readOnly placeholder="HH:MM" />
        </div>
      </div>

      <div className="field">
        <label>Attendees</label>
        <input value={form.attendees} readOnly placeholder="Enter names or search..." />
      </div>

      <div className="field">
        <label>Topics Discussed</label>
        <textarea value={form.topics_discussed} readOnly placeholder="Enter key discussion points..." />
      </div>

      <div className="field">
        <label>Materials Shared</label>
        <div className="chip-row">
          {form.materials_shared.length === 0 && (
            <span className="muted">No materials added</span>
          )}
          {form.materials_shared.map((m) => (
            <span className="chip" key={m}>
              {m}
            </span>
          ))}
        </div>
      </div>

      <div className="field">
        <label>Samples Distributed</label>
        <div className="chip-row">
          {form.samples_distributed.length === 0 && (
            <span className="muted">No samples added</span>
          )}
          {form.samples_distributed.map((s) => (
            <span className="chip" key={s}>
              {s}
            </span>
          ))}
        </div>
      </div>

      <div className="field">
        <label>Observed / Inferred HCP Sentiment</label>
        <div className="sentiment-row">
          {SENTIMENTS.map((s) => (
            <label key={s} className={`sentiment-pill ${form.sentiment === s ? "active" : ""}`}>
              <input type="radio" checked={form.sentiment === s} onChange={() => {}} />
              {s}
            </label>
          ))}
        </div>
      </div>

      <div className="field">
        <label>Outcomes</label>
        <textarea value={form.outcomes} readOnly placeholder="Key outcomes or agreements..." />
      </div>

      <div className="field">
        <label>Follow-up Actions</label>
        <textarea value={form.follow_up_actions} readOnly placeholder="Enter next steps or tasks..." />
      </div>

      <button className="save-btn" onClick={handleSave}>
        {saveStatus || "Save Interaction"}
      </button>
    </div>
  );
}