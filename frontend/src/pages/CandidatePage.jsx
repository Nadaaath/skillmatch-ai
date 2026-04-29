import CandidateForm from "../components/CandidateForm";

export default function CandidatePage({ latestCandidateId, onCandidateCreated }) {
  return (
    <section className="panel">
      <header className="panel__header">
        <h2>Candidate intake</h2>
        <p className="muted">
          Capture the candidate profile and CV to populate the talent database.
        </p>
      </header>
      <CandidateForm onCreated={onCandidateCreated} />
      {latestCandidateId ? (
        <div className="summary-card">
          Latest candidate ID: <strong>{latestCandidateId}</strong>
        </div>
      ) : null}
    </section>
  );
}
