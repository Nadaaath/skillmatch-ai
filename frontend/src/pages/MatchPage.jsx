import { useEffect, useState } from "react";
import { matchJob } from "../api/api";
import MatchResult from "../components/MatchResult";

export default function MatchPage({ defaultCandidateId, defaultJobId }) {
  const [candidateId, setCandidateId] = useState(defaultCandidateId || "");
  const [jobId, setJobId] = useState(defaultJobId || "");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (defaultCandidateId && !candidateId) {
      setCandidateId(String(defaultCandidateId));
    }
  }, [defaultCandidateId, candidateId]);

  useEffect(() => {
    if (defaultJobId && !jobId) {
      setJobId(String(defaultJobId));
    }
  }, [defaultJobId, jobId]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    try {
      setLoading(true);
      const response = await matchJob({
        candidateId: Number(candidateId),
        jobId: Number(jobId),
      });

      if (response.detail || response.error) {
        throw new Error(response.detail || response.error);
      }

      setResult(response);
    } catch (err) {
      setError(err.message || "Match request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <header className="panel__header">
        <h2>Match intelligence</h2>
        <p className="muted">
          Run the explainable AI scoring and review the candidate fit.
        </p>
      </header>
      <form className="form form--inline" onSubmit={handleSubmit}>
        <label className="field">
          Candidate ID
          <input
            type="number"
            value={candidateId}
            onChange={(event) => setCandidateId(event.target.value)}
            placeholder="1"
            required
          />
        </label>
        <label className="field">
          Job ID
          <input
            type="number"
            value={jobId}
            onChange={(event) => setJobId(event.target.value)}
            placeholder="1"
            required
          />
        </label>
        <button className="btn btn--primary" type="submit" disabled={loading}>
          {loading ? "Matching..." : "Run match"}
        </button>
      </form>
      <MatchResult result={result} loading={loading} error={error} />
    </section>
  );
}
