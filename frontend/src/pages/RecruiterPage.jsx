import JobForm from "../components/JobForm";

export default function RecruiterPage({ latestJobId, onJobCreated }) {
  return (
    <section className="panel">
      <header className="panel__header">
        <h2>Recruiter workspace</h2>
        <p className="muted">
          Create roles and define the skill profile before running matches.
        </p>
      </header>
      <JobForm onCreated={onJobCreated} />
      {latestJobId ? (
        <div className="summary-card">
          Latest job ID: <strong>{latestJobId}</strong>
        </div>
      ) : null}
    </section>
  );
}
