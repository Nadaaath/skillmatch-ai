import { useState } from "react";
import { uploadCandidateCv } from "../api/api";

export default function CandidateForm({ onCreated }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [experienceYears, setExperienceYears] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setError("");

    if (!file) {
      setError("Please attach a PDF CV.");
      return;
    }

    try {
      setLoading(true);
      const response = await uploadCandidateCv({
        fullName: fullName.trim(),
        email: email.trim(),
        experienceYears: Number(experienceYears),
        file,
      });

      if (response.detail || response.error) {
        throw new Error(response.detail || response.error);
      }

      setMessage(response.message || "Candidate created.");
      if (response.candidate_id) {
        onCreated?.(response.candidate_id);
      }
    } catch (err) {
      setError(err.message || "Failed to upload CV.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form__grid">
        <label className="field">
          Full name
          <input
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="e.g. Lina Alvarez"
            required
          />
        </label>
        <label className="field">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="lina@talentmail.com"
            required
          />
        </label>
        <label className="field">
          Years of experience
          <input
            type="number"
            min="0"
            step="0.5"
            value={experienceYears}
            onChange={(event) => setExperienceYears(event.target.value)}
            placeholder="3"
            required
          />
        </label>
        <label className="field field--file">
          Upload PDF CV
          <input
            type="file"
            accept="application/pdf"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
            required
          />
          <span className="field__hint">
            {file ? file.name : "Attach a single PDF file."}
          </span>
        </label>
      </div>
      <div className="form__footer">
        <button className="btn btn--primary" type="submit" disabled={loading}>
          {loading ? "Uploading..." : "Upload CV"}
        </button>
        {message && <span className="tag tag--success">{message}</span>}
        {error && <span className="tag tag--error">{error}</span>}
      </div>
    </form>
  );
}
