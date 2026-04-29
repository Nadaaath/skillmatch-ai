import { useState } from "react";
import "./App.css";
import CandidatePage from "./pages/CandidatePage";
import RecruiterPage from "./pages/RecruiterPage";
import MatchPage from "./pages/MatchPage";

const PAGES = [
  { id: "candidate", label: "Candidate intake" },
  { id: "recruiter", label: "Recruiter workspace" },
  { id: "match", label: "Match intelligence" },
];

export default function App() {
  const [activePage, setActivePage] = useState("candidate");
  const [latestCandidateId, setLatestCandidateId] = useState("");
  const [latestJobId, setLatestJobId] = useState("");

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <p className="eyebrow">SkillMatch AI</p>
          <h1>Explainable talent matching</h1>
          <p className="lead">
            Upload CVs, define job profiles, and review transparent AI hiring
            signals in one flow.
          </p>
        </div>
        <nav className="app__nav">
          {PAGES.map((page) => (
            <button
              key={page.id}
              type="button"
              className={`tab ${activePage === page.id ? "tab--active" : ""}`}
              onClick={() => setActivePage(page.id)}
            >
              {page.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="app__content">
        {activePage === "candidate" && (
          <CandidatePage
            latestCandidateId={latestCandidateId}
            onCandidateCreated={setLatestCandidateId}
          />
        )}
        {activePage === "recruiter" && (
          <RecruiterPage
            latestJobId={latestJobId}
            onJobCreated={setLatestJobId}
          />
        )}
        {activePage === "match" && (
          <MatchPage
            defaultCandidateId={latestCandidateId}
            defaultJobId={latestJobId}
          />
        )}
      </main>
    </div>
  );
}
