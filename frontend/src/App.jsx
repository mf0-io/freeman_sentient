import { useMemo } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { ThoughtsVisualizer } from './components/ThoughtsVisualizer';
import { DecisionsVisualizer } from './components/DecisionsVisualizer';
import { PlanningVisualizer } from './components/PlanningVisualizer';
import { ExecutionVisualizer } from './components/ExecutionVisualizer';

// WebSocket URL from environment or default to localhost
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8765/reasoning';

function App() {
  // Initialize WebSocket connection with auto-reconnect
  const {
    connected,
    error,
    messageHistory,
    disconnect,
    reconnect,
  } = useWebSocket(WS_URL, {
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
  });

  // Group messages by module type for visualization components
  const messagesByModule = useMemo(() => {
    const grouped = {
      atomizer: [],
      planner: [],
      executor: [],
      aggregator: [],
      verifier: [],
      other: [],
    };

    (messageHistory || []).forEach((msg) => {
      const module = msg.module || msg.type || 'unknown';
      if (grouped[module] !== undefined) {
        grouped[module].push(msg);
      } else {
        grouped.other.push(msg);
      }
    });

    return grouped;
  }, [messageHistory]);

  const handleReconnect = () => {
    reconnect();
  };

  const handleDisconnect = () => {
    disconnect();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🧠 Freeman Reasoning Visualizer</h1>
        <div className="connection-status">
          <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
          <span className="message-count">
            {messageHistory.length} message{messageHistory.length !== 1 ? 's' : ''} received
          </span>
        </div>
        <div className="connection-controls">
          {connected ? (
            <button onClick={handleDisconnect} className="btn-disconnect">
              Disconnect
            </button>
          ) : (
            <button onClick={handleReconnect} className="btn-reconnect">
              Reconnect
            </button>
          )}
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <strong>Connection Error:</strong> {error.message}
        </div>
      )}

      <main className="app-main">
        {/* Thoughts/Atomizer Visualization */}
        <section className="viz-section">
          <h2>💭 Inner Thoughts</h2>
          <ThoughtsVisualizer
            messages={messagesByModule.atomizer}
            showTimestamps={true}
            compact={false}
          />
        </section>

        {/* Decisions Visualization */}
        <section className="viz-section">
          <h2>🎯 Decisions</h2>
          <DecisionsVisualizer
            messages={[...messagesByModule.atomizer, ...messagesByModule.verifier]}
            showTimestamps={true}
            showConfidence={true}
            compact={false}
          />
        </section>

        {/* Planning Visualization */}
        <section className="viz-section">
          <h2>📋 Planning Steps</h2>
          <PlanningVisualizer
            messages={messagesByModule.planner}
            showTimestamps={true}
            showDependencies={true}
            compact={false}
          />
        </section>

        {/* Execution Visualization */}
        <section className="viz-section">
          <h2>⚡ Execution Traces</h2>
          <ExecutionVisualizer
            messages={messagesByModule.executor}
            showTimestamps={true}
            showSources={true}
            showExecutionTime={true}
            compact={false}
          />
        </section>

        {/* Aggregator Results */}
        <section className="viz-section">
          <h2>📊 Aggregated Results</h2>
          {messagesByModule.aggregator.length > 0 ? (
            <div className="message-list">
              {messagesByModule.aggregator.map((msg, idx) => (
                <div key={`agg-${idx}`} className="message-card">
                  <span className="message-timestamp">
                    {new Date(msg.timestamp || Date.now()).toLocaleTimeString()}
                  </span>
                  <span className="message-type">Aggregator</span>
                  <p className="message-content">
                    {msg.data?.synthesized_result || msg.content || JSON.stringify(msg.data)}
                  </p>
                  {msg.data?.component_results && msg.data.component_results.length > 0 && (
                    <div className="component-results">
                      <strong>Component Results:</strong>
                      <ul>
                        {msg.data.component_results.map((result, ridx) => (
                          <li key={ridx}>{result}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="placeholder">Waiting for aggregated results...</p>
          )}
        </section>

        {/* Verifier Results */}
        <section className="viz-section">
          <h2>✅ Verification</h2>
          {messagesByModule.verifier.length > 0 ? (
            <div className="message-list">
              {messagesByModule.verifier.map((msg, idx) => (
                <div key={`ver-${idx}`} className="message-card">
                  <span className="message-timestamp">
                    {new Date(msg.timestamp || Date.now()).toLocaleTimeString()}
                  </span>
                  <span className={`verdict ${msg.data?.verdict === true ? 'pass' : 'fail'}`}>
                    {msg.data?.verdict === true ? '✓ Passed' : '✗ Failed'}
                  </span>
                  <p className="message-content">
                    {msg.data?.feedback || msg.content || JSON.stringify(msg.data)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="placeholder">Waiting for verification results...</p>
          )}
        </section>

        {/* Other Messages */}
        {messagesByModule.other.length > 0 && (
          <section className="viz-section">
            <h2>📨 Other Messages</h2>
            <div className="message-list">
              {messagesByModule.other.map((msg, idx) => (
                <div key={idx} className="message-card">
                  <span className="message-timestamp">
                    {new Date(msg.timestamp || Date.now()).toLocaleTimeString()}
                  </span>
                  <pre className="message-raw">{JSON.stringify(msg, null, 2)}</pre>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>ROMA Reasoning Visualizer - Real-time AI Agent Thoughts</p>
      </footer>
    </div>
  );
}

export default App;
