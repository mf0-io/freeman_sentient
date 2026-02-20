import { useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * ExecutionVisualizer Component
 *
 * Displays execution traces from the ROMA Executor module.
 * Shows the output, sources, execution time, and timing information.
 *
 * @param {Object} props - Component props
 * @param {Array} props.executions - Array of execution messages from Executor
 * @param {boolean} props.showTimestamps - Whether to display timestamps
 * @param {boolean} props.compact - Whether to use compact layout
 * @param {boolean} props.showSources - Whether to show source references
 * @param {boolean} props.showExecutionTime - Whether to show execution time
 */
export function ExecutionVisualizer({
  executions = [],
  showTimestamps = true,
  compact = false,
  showSources = true,
  showExecutionTime = true,
}) {
  // Process execution data
  const executionData = useMemo(() => {
    return (executions || []).map((exec) => {
      // Safely extract data from various message formats
      const output = exec.data?.output || exec.output || exec.content || exec.result || '';
      const sources = exec.data?.sources || exec.sources || exec.source_references || [];
      const executionTime = exec.data?.execution_time ?? exec.execution_time ?? exec.duration ?? null;
      const timestamp = exec.timestamp || exec.data?.timestamp;

      return {
        output,
        sources: Array.isArray(sources) ? sources : [],
        executionTime,
        timestamp,
        original: exec,
      };
    }).filter((exec) => exec.output); // Filter out executions without output
  }, [executions]);

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) return '';
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return '';
    }
  };

  // Format execution time for display
  const formatExecutionTime = (time) => {
    if (time == null) return '';
    if (time < 1) {
      return `${Math.round(time * 1000)}ms`;
    }
    return `${time.toFixed(2)}s`;
  };

  // Get execution time level for styling
  const getExecutionTimeLevel = (time) => {
    if (time == null) return 'unknown';
    if (time < 0.5) return 'fast';
    if (time < 2) return 'normal';
    if (time < 5) return 'slow';
    return 'very-slow';
  };

  // Render a single execution item
  const ExecutionItem = ({ execution, index }) => {
    const { output, sources, executionTime, timestamp } = execution;
    const timeLevel = getExecutionTimeLevel(executionTime);

    return (
      <div
        className={`execution-item ${timeLevel} ${compact ? 'compact' : ''}`}
        data-index={index}
      >
        <div className="execution-header">
          {showTimestamps && timestamp && (
            <span className="execution-timestamp" aria-label="Timestamp">
              {formatTimestamp(timestamp)}
            </span>
          )}
          {showExecutionTime && executionTime != null && (
            <span className={`execution-time ${timeLevel}`} aria-label={`Execution time: ${formatExecutionTime(executionTime)}`}>
              <span className="time-icon" aria-hidden="true">
                ⏱️
              </span>
              <span className="time-value">{formatExecutionTime(executionTime)}</span>
            </span>
          )}
        </div>

        <div className="execution-output" aria-label="Execution output">
          <pre className="output-content">{output}</pre>
        </div>

        {showSources && sources.length > 0 && (
          <div className="execution-sources" aria-label="Sources">
            <span className="sources-label">
              <span className="sources-icon" aria-hidden="true">
                📚
              </span>
              Sources:
            </span>
            <div className="sources-list">
              {sources.map((source, idx) => (
                <span
                  key={idx}
                  className="source-tag"
                  aria-label={`Source: ${source}`}
                >
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  ExecutionItem.propTypes = {
    execution: PropTypes.shape({
      output: PropTypes.string.isRequired,
      sources: PropTypes.arrayOf(PropTypes.string),
      executionTime: PropTypes.number,
      timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
    }).isRequired,
    index: PropTypes.number.isRequired,
  };

  // Calculate stats
  const stats = useMemo(() => {
    const totalTime = executionData.reduce((sum, exec) => {
      return sum + (exec.executionTime ?? 0);
    }, 0);

    const avgTime = executionData.length > 0
      ? totalTime / executionData.length
      : 0;

    const sourcesCount = executionData.reduce((sum, exec) => {
      return sum + exec.sources.length;
    }, 0);

    return {
      totalTime,
      avgTime,
      sourcesCount,
    };
  }, [executionData]);

  // Empty state
  if (!executions || executions.length === 0 || executionData.length === 0) {
    return (
      <div className="execution-visualizer empty">
        <div className="empty-state">
          <svg
            className="empty-icon"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <p className="empty-message">Waiting for execution traces...</p>
          <p className="empty-hint">Executor results will appear here</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`execution-visualizer ${compact ? 'compact' : ''}`}>
      {/* Execution summary header */}
      <div className="execution-summary">
        <h2 className="summary-title">
          <span className="title-icon">⚡</span>
          Execution Traces
        </h2>
        <div className="summary-stats">
          <span className="summary-stat">
            <strong>{executionData.length}</strong> execution{executionData.length !== 1 ? 's' : ''}
          </span>
          {showExecutionTime && stats.totalTime > 0 && (
            <span className="summary-stat">
              Total: <strong>{formatExecutionTime(stats.totalTime)}</strong>
            </span>
          )}
        </div>
      </div>

      {/* Execution list */}
      <div className="execution-list">
        {executionData.map((execution, idx) => (
          <ExecutionItem key={`exec-${idx}`} execution={execution} index={idx} />
        ))}
      </div>

      {/* Stats footer */}
      <div className="execution-stats">
        <span className="stat-item">
          <strong>{executionData.length}</strong> execution{executionData.length !== 1 ? 's' : ''} total
        </span>
        {showExecutionTime && stats.avgTime > 0 && (
          <span className="stat-item">
            Avg: <strong>{formatExecutionTime(stats.avgTime)}</strong>
          </span>
        )}
        {showSources && stats.sourcesCount > 0 && (
          <span className="stat-item">
            <strong>{stats.sourcesCount}</strong> source{stats.sourcesCount !== 1 ? 's' : ''}
          </span>
        )}
      </div>
    </div>
  );
}

ExecutionVisualizer.propTypes = {
  executions: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      module: PropTypes.string,
      timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
      data: PropTypes.shape({
        output: PropTypes.string,
        sources: PropTypes.arrayOf(PropTypes.string),
        execution_time: PropTypes.number,
        timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
      }),
      output: PropTypes.string,
      sources: PropTypes.arrayOf(PropTypes.string),
      source_references: PropTypes.arrayOf(PropTypes.string),
      execution_time: PropTypes.number,
      duration: PropTypes.number,
      content: PropTypes.string,
      result: PropTypes.string,
    })
  ),
  showTimestamps: PropTypes.bool,
  compact: PropTypes.bool,
  showSources: PropTypes.bool,
  showExecutionTime: PropTypes.bool,
};

export default ExecutionVisualizer;
