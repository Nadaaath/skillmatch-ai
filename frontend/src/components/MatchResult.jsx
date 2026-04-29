export default function MatchResult({ result, loading, error }) {
  if (loading) {
    return <div className="result-card">Running the AI match...</div>;
  }

  if (error) {
    return <div className="result-card result-card--error">{error}</div>;
  }

  if (!result) {
    return (
      <div className="result-card result-card--empty">
        Run a match to view the AI scorecard.
      </div>
    );
  }

  return (
    <div className="result-grid">
      <div className="result-card">
        <h3>Score breakdown</h3>
        <dl>
          <div>
            <dt>Skill match ratio</dt>
            <dd>{(result.skill_match_ratio * 100).toFixed(1)}%</dd>
          </div>
          <div>
            <dt>TF-IDF similarity</dt>
            <dd>{(result.tfidf_similarity * 100).toFixed(1)}%</dd>
          </div>
          <div>
            <dt>BERT similarity</dt>
            <dd>{(result.bert_similarity * 100).toFixed(1)}%</dd>
          </div>
          <div>
            <dt>Hiring probability</dt>
            <dd className="accent">
              {(result.hiring_probability * 100).toFixed(1)}%
            </dd>
          </div>
        </dl>
      </div>
      <div className="result-card">
        <h3>Missing skills</h3>
        <ul>
          {result.missing_skills.map((skill) => (
            <li key={skill}>{skill}</li>
          ))}
        </ul>
      </div>
      <div className="result-card">
        <h3>Recommendations</h3>
        <ul>
          {result.recommendations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
