import { useState } from "react";
import { createJob } from "../api/api";

export default function JobForm({ onCreated }) {
  const [title, setTitle] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setError("");

    try {
      setLoading(true);
      const response = await createJob({
        title: title.trim(),
        requiredSkills: requiredSkills.trim(),
      });

      if (response.detail || response.error) {
        throw new Error(response.detail || response.error);
      }

      setMessage(response.message || "Job created.");
      if (response.job_id) {
        onCreated?.(response.job_id);
      }
    } catch (err) {
      setError(err.message || "Failed to create job.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form__grid">
        <label className="field">
          Job title
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Machine Learning Engineer"
            required
          />
        </label>
        <label className="field field--full">
          Required skills (comma separated)
          <textarea
            rows="3"
            value={requiredSkills}
            onChange={(event) => setRequiredSkills(event.target.value)}
            placeholder="python, tensorflow, mlops, feature engineering"
            required
          />
        </label>
      </div>
      <div className="form__footer">
        <button className="btn btn--primary" type="submit" disabled={loading}>
          {loading ? "Saving..." : "Create job"}
        </button>
        {message && <span className="tag tag--success">{message}</span>}
        {error && <span className="tag tag--error">{error}</span>}
      </div>
    </form>
  );
}
