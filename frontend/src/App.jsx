import { useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/chat";
// If accessing from your laptop browser, use:
// const API_URL = "http://YOUR_EC2_PUBLIC_IP:8000/api/chat";

function App() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const sendQuery = async (customQuery = null) => {
    const finalQuery = customQuery || query;

    if (!finalQuery.trim()) {
      alert("Please enter a query");
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      const res = await axios.post(
        API_URL,
        { query: finalQuery },
        {
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 300000,
        }
      );

      setResponse(res.data);
      setQuery(finalQuery);
    } catch (error) {
      console.error("Frontend API Error:", error);

      setResponse({
        intent: "frontend_error",
        result: {
          agent: "frontend",
          status: "failed",
          message: "Unable to connect to backend or backend request failed.",
          error:
            error.response?.data?.detail ||
            error.response?.data ||
            error.message ||
            "Unknown frontend error",
        },
      });
    } finally {
      setLoading(false);
    }
  };

  const renderTable = (data) => {
    if (!Array.isArray(data) || data.length === 0) {
      return <p className="muted">No table data available.</p>;
    }

    const columns = Object.keys(data[0]);

    return (
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {data.map((row, index) => (
              <tr key={index}>
                {columns.map((col) => (
                  <td key={col}>
                    {typeof row[col] === "object"
                      ? JSON.stringify(row[col])
                      : String(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderStatusBadge = (status) => {
    if (!status) return null;

    return (
      <span className={status === "success" ? "badge success" : "badge danger"}>
        {status}
      </span>
    );
  };

  const renderQueryGuard = (result) => {
    return (
      <div className="result-card">
        <div className="card-header">
          <h2>Query Guard Response</h2>
          <span className="badge warning">Clarification Required</span>
        </div>

        <p>{result.message}</p>

        {result.reason && (
          <p className="muted">
            <strong>Reason:</strong> {result.reason}
          </p>
        )}

        {result.attempts_remaining !== undefined && (
          <p className="muted">
            <strong>Attempts remaining:</strong> {result.attempts_remaining}
          </p>
        )}

        {result.suggestions && (
          <div className="section">
            <h3>Suggested Queries</h3>
            <div className="suggestions">
              {result.suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  className="suggestion-btn"
                  onClick={() => sendQuery(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderStatistical = (result) => {
    return (
      <div className="result-card">
        <div className="card-header">
          <h2>Statistical Analysis</h2>
          <span className="badge success">Statistical Agent</span>
        </div>

        <div className="stats-grid">
          {result.method && (
            <div className="stat-card">
              <span>Method</span>
              <strong>{result.method}</strong>
            </div>
          )}

          {result.p_value !== undefined && (
            <div className="stat-card">
              <span>P-Value</span>
              <strong>{result.p_value}</strong>
            </div>
          )}

          {result.correlation !== undefined && (
            <div className="stat-card">
              <span>Correlation</span>
              <strong>{result.correlation}</strong>
            </div>
          )}

          {result.t_statistic !== undefined && (
            <div className="stat-card">
              <span>T-Statistic</span>
              <strong>{result.t_statistic}</strong>
            </div>
          )}

          {result.f_statistic !== undefined && (
            <div className="stat-card">
              <span>F-Statistic</span>
              <strong>{result.f_statistic}</strong>
            </div>
          )}

          {result.chi_square !== undefined && (
            <div className="stat-card">
              <span>Chi-Square</span>
              <strong>{result.chi_square}</strong>
            </div>
          )}

          {result.r_squared !== undefined && (
            <div className="stat-card">
              <span>R-Squared</span>
              <strong>{result.r_squared}</strong>
            </div>
          )}
        </div>

        {result.interpretation && (
          <div className="section">
            <h3>Interpretation</h3>
            <p>{result.interpretation}</p>
          </div>
        )}

        {result.sql && (
          <div className="section">
            <h3>SQL Used</h3>
            <pre>{result.sql}</pre>
          </div>
        )}

        {result.results && (
          <div className="section">
            <h3>Results</h3>
            {renderTable(result.results)}
          </div>
        )}
      </div>
    );
  };

  const renderBiomarker = (result) => {
    return (
      <div className="result-card">
        <div className="card-header">
          <h2>Biomarker Research</h2>
          {renderStatusBadge(result.status)}
        </div>

        {result.summary && (
          <div className="summary-box">
            <h3>Summary</h3>
            <p>{result.summary}</p>
          </div>
        )}

        <div className="stats-grid">
          {result.articles_found !== undefined && (
            <div className="stat-card">
              <span>Articles Found</span>
              <strong>{result.articles_found}</strong>
            </div>
          )}

          {result.chunks_stored !== undefined && (
            <div className="stat-card">
              <span>Chunks Stored</span>
              <strong>{result.chunks_stored}</strong>
            </div>
          )}

          {result.retrieved_context_count !== undefined && (
            <div className="stat-card">
              <span>Retrieved Context</span>
              <strong>{result.retrieved_context_count}</strong>
            </div>
          )}
        </div>

        {result.pubmed_ids && (
          <div className="section">
            <h3>PubMed IDs</h3>
            <div className="pill-row">
              {result.pubmed_ids.map((id) => (
                <span className="pill" key={id}>
                  {id}
                </span>
              ))}
            </div>
          </div>
        )}

        {result.sources && (
          <div className="section">
            <h3>Sources</h3>
            {renderTable(result.sources)}
          </div>
        )}
      </div>
    );
  };

  const renderSQL = (result) => {
    return (
      <div className="result-card">
        <div className="card-header">
          <h2>Text-to-SQL Result</h2>
          {renderStatusBadge(result.status)}
        </div>

        {result.message && (
          <div className="warning-box">
            <strong>Message:</strong> {result.message}
          </div>
        )}

        {result.error && (
          <div className="error-box">
            <strong>Error:</strong>
            <pre>{String(result.error)}</pre>
          </div>
        )}

        {result.generated_sql && (
          <div className="section">
            <h3>Generated SQL</h3>
            <pre>{result.generated_sql}</pre>
          </div>
        )}

        {result.results && (
          <div className="section">
            <h3>SQL Results</h3>
            {renderTable(result.results)}
          </div>
        )}

        {result.suggestion && (
          <p className="muted">
            <strong>Suggestion:</strong> {result.suggestion}
          </p>
        )}
      </div>
    );
  };

  const renderError = (result) => {
    return (
      <div className="result-card">
        <div className="card-header">
          <h2>Error</h2>
          <span className="badge danger">Failed</span>
        </div>

        <div className="error-box">
          <p>{result.message || "Something went wrong."}</p>
          {result.error && <pre>{String(result.error)}</pre>}
        </div>

        {result.suggestion && (
          <p className="muted">
            <strong>Suggestion:</strong> {result.suggestion}
          </p>
        )}
      </div>
    );
  };

  const renderResponse = () => {
    if (!response) return null;

    const intent = response.intent;
    const result = response.result || {};

    if (result.status === "failed" || intent === "frontend_error") {
      if (intent === "sql_query") return renderSQL(result);
      return renderError(result);
    }

    if (intent === "clarification_required" || intent === "invalid_query") {
      return renderQueryGuard(result);
    }

    if (intent === "statistical_analysis") {
      return renderStatistical(result);
    }

    if (intent === "biomarker_research") {
      return renderBiomarker(result);
    }

    if (intent === "sql_query") {
      return renderSQL(result);
    }

    return (
      <div className="result-card">
        <h2>Raw Response</h2>
        <pre>{JSON.stringify(response, null, 2)}</pre>
      </div>
    );
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Life Sciences Multi-Agent AI Assistant</h1>
          <p>
            Query Guard · Biomarker RAG · Statistical Analysis · Text-to-SQL
          </p>
        </header>

        <div className="query-panel">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a clinical, biomarker, statistical, or SQL query..."
            onKeyDown={(e) => {
              if (e.key === "Enter") sendQuery();
            }}
          />

          <button onClick={() => sendQuery()} disabled={loading}>
            {loading ? "Processing..." : "Send"}
          </button>
        </div>

        <div className="examples">
          <button onClick={() => sendQuery("what is search in genomics")}>
            Query Guard
          </button>

          <button onClick={() => sendQuery("average os by treatment group")}>
            Statistics
          </button>

          <button onClick={() => sendQuery("What is HER2?")}>
            Biomarker
          </button>

          <button onClick={() => sendQuery("show ctdna records")}>
            SQL Query
          </button>
        </div>

        {loading && (
          <div className="loading-box">
            Processing request... Please wait.
          </div>
        )}

        {renderResponse()}

        {response && (
          <details className="raw-json">
            <summary>View Raw JSON</summary>
            <pre>{JSON.stringify(response, null, 2)}</pre>
          </details>
        )}
      </div>
    </div>
  );
}

export default App;