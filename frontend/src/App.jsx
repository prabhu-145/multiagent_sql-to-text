import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const sendQuery = async () => {
    if (!query.trim()) {
      alert("Please enter a query");
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/chat",
        {
          query: query,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      setResponse(res.data);
    } catch (error) {
      console.error("Frontend API Error:", error);

      setResponse({
        error:
          error.response?.data?.detail ||
          error.response?.data ||
          error.message ||
          "Unable to connect to backend. Check FastAPI server and CORS.",
      });
    } finally {
      setLoading(false);
    }
  };

  const renderResult = () => {
    if (!response) return null;

    if (response.error) {
      return (
        <div className="error-box">
          <strong>Error:</strong>
          <pre>{JSON.stringify(response.error, null, 2)}</pre>
        </div>
      );
    }

    const intent = response.intent;
    const result = response.result;

    return (
      <div className="result-card">
        <h2>Response</h2>

        <div className="badge">Intent: {intent}</div>

        {result?.agent && (
          <div className="badge secondary">Agent: {result.agent}</div>
        )}

        {result?.method && (
          <div className="section">
            <h3>Method</h3>
            <p>{result.method}</p>
          </div>
        )}

        {result?.generated_sql && (
          <div className="section">
            <h3>Generated SQL</h3>
            <pre>{result.generated_sql}</pre>
          </div>
        )}

        {result?.sql && (
          <div className="section">
            <h3>SQL Used</h3>
            <pre>{result.sql}</pre>
          </div>
        )}

        {result?.summary && (
          <div className="section">
            <h3>Summary</h3>
            <p>{result.summary}</p>
          </div>
        )}

        {result?.interpretation && (
          <div className="section">
            <h3>Interpretation</h3>
            <p>{result.interpretation}</p>
          </div>
        )}

        {result?.pubmed_ids && (
          <div className="section">
            <h3>PubMed IDs</h3>
            <p>{result.pubmed_ids.join(", ")}</p>
          </div>
        )}

        {result?.retrieved_context_count !== undefined && (
          <div className="section">
            <h3>Retrieved Context Count</h3>
            <p>{result.retrieved_context_count}</p>
          </div>
        )}

        {result?.correlation !== undefined && (
          <div className="section">
            <h3>Correlation</h3>
            <p>{result.correlation}</p>
          </div>
        )}

        {result?.p_value !== undefined && (
          <div className="section">
            <h3>P-Value</h3>
            <p>{result.p_value}</p>
          </div>
        )}

        {result?.t_statistic !== undefined && (
          <div className="section">
            <h3>T-Statistic</h3>
            <p>{result.t_statistic}</p>
          </div>
        )}

        {result?.f_statistic !== undefined && (
          <div className="section">
            <h3>F-Statistic</h3>
            <p>{result.f_statistic}</p>
          </div>
        )}

        {result?.chi_square !== undefined && (
          <div className="section">
            <h3>Chi-Square</h3>
            <p>{result.chi_square}</p>
          </div>
        )}

        {result?.r_squared !== undefined && (
          <div className="section">
            <h3>R-Squared</h3>
            <p>{result.r_squared}</p>
          </div>
        )}

        {result?.standard_deviation !== undefined && (
          <div className="section">
            <h3>Standard Deviation</h3>
            <p>{result.standard_deviation}</p>
          </div>
        )}

        {result?.results && (
          <div className="section">
            <h3>Results</h3>
            <pre>{JSON.stringify(result.results, null, 2)}</pre>
          </div>
        )}

        <div className="section">
          <h3>Raw JSON</h3>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      <div className="container">
        <h1>Life Sciences AI Assistant</h1>

        <p className="subtitle">
          Multi-Agent Assistant for SQL Analytics, Biomarker Research, RAG, and Statistics
        </p>

        <div className="query-box">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask something like: show ctdna records"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendQuery();
              }
            }}
          />

          <button onClick={sendQuery} disabled={loading}>
            {loading ? "Processing..." : "Send"}
          </button>
        </div>

        <div className="examples">
          <button onClick={() => setQuery("show ctdna records")}>
            SQL Query
          </button>

          <button onClick={() => setQuery("average os by treatment group")}>
            Statistics
          </button>

          <button
            onClick={() =>
              setQuery("kaplan meier survival analysis by treatment group")
            }
          >
            Survival Analysis
          </button>

          <button onClick={() => setQuery("standard deviation of os")}>
            Std Dev
          </button>

          <button onClick={() => setQuery("regression between dose and os")}>
            Regression
          </button>

          <button onClick={() => setQuery("What is HER2 biomarker?")}>
            Biomarker Research
          </button>
        </div>

        {loading && <div className="loading">Processing request...</div>}

        {renderResult()}
      </div>
    </div>
  );
}

export default App;