import { useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * DecisionsVisualizer Component
 *
 * Displays decisions made during the AI reasoning process.
 * Shows the decision type, rationale, confidence level, and timing.
 *
 * @param {Object} props - Component props
 * @param {Array} props.decisions - Array of decision objects
 * @param {boolean} props.showTimestamps - Whether to display timestamps
 * @param {boolean} props.compact - Whether to use compact layout
 * @param {boolean} props.showConfidence - Whether to show confidence bars
 */
export function DecisionsVisualizer({
  decisions = [],
  showTimestamps = true,
  compact = false,
  showConfidence = true,
}) {
  // Group decisions by decision_type for better organization
  const groupedDecisions = useMemo(() => {
    const groups = {
      ATOMICITY: [],
      DECOMPOSITION: [],
      EXECUTION: [],
      VERIFICATION: [],
      OTHER: [],
    };

    (decisions || []).forEach((decision) => {
      // Safely extract decision_type from various message formats
      const decisionType = decision.data?.decision_type || decision.decision_type || decision.type || 'OTHER';

      if (groups[decisionType] !== undefined) {
        groups[decisionType].push(decision);
      } else {
        groups.OTHER.push(decision);
      }
    });

    return groups;
  }, [decisions]);

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

  // Get confidence level for styling
  const getConfidenceLevel = (confidence) => {
    if (confidence == null) return 'unknown';
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  };

  // Render a single decision item
  const DecisionItem = ({ decision, index }) => {
    const decisionType = decision.data?.decision_type || decision.decision_type || decision.type || 'UNKNOWN';
    const rationale = decision.data?.rationale || decision.rationale || decision.reasoning || decision.content || '';
    const confidence = decision.data?.confidence ?? decision.confidence ?? null;
    const timestamp = decision.timestamp || decision.data?.timestamp;

    if (!rationale && !decisionType) return null;

    const confidenceLevel = getConfidenceLevel(confidence);

    return (
      <div
        className={`decision-item ${decisionType.toLowerCase()} ${confidenceLevel} ${compact ? 'compact' : ''}`}
        data-index={index}
      >
        {showTimestamps && timestamp && (
          <span className="decision-timestamp" aria-label="Timestamp">
            {formatTimestamp(timestamp)}
          </span>
        )}
        <span className={`decision-badge decision-${decisionType.toLowerCase()}`} aria-label="Decision type">
          {decisionType}
        </span>
        {showConfidence && confidence != null && (
          <div className="decision-confidence" aria-label={`Confidence: ${Math.round(confidence * 100)}%`}>
            <span className="confidence-label">Confidence:</span>
            <div className="confidence-bar-container">
              <div
                className={`confidence-bar confidence-${confidenceLevel}`}
                style={{ width: `${Math.max(0, Math.min(1, confidence)) * 100}%` }}
                aria-label={`${Math.round(confidence * 100)}% confidence`}
              />
            </div>
            <span className="confidence-value">{Math.round(confidence * 100)}%</span>
          </div>
        )}
        <p className="decision-rationale">{rationale}</p>
      </div>
    );
  };

  DecisionItem.propTypes = {
    decision: PropTypes.object.isRequired,
    index: PropTypes.number.isRequired,
  };

  // Empty state
  if (!decisions || decisions.length === 0) {
    return (
      <div className="decisions-visualizer empty">
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
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="empty-message">Waiting for decisions...</p>
          <p className="empty-hint">AI decisions will appear here with rationales</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`decisions-visualizer ${compact ? 'compact' : ''}`}>
      {/* ATOMICITY decisions */}
      {groupedDecisions.ATOMICITY.length > 0 && (
        <div className="decision-group atomicity-group">
          <h3 className="group-title">
            <span className="group-icon">🔬</span>
            Atomicity Decisions
            <span className="group-count">{groupedDecisions.ATOMICITY.length}</span>
          </h3>
          <div className="decision-list">
            {groupedDecisions.ATOMICITY.map((decision, idx) => (
              <DecisionItem key={`atomicity-${idx}`} decision={decision} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* DECOMPOSITION decisions */}
      {groupedDecisions.DECOMPOSITION.length > 0 && (
        <div className="decision-group decomposition-group">
          <h3 className="group-title">
            <span className="group-icon">🔨</span>
            Decomposition Decisions
            <span className="group-count">{groupedDecisions.DECOMPOSITION.length}</span>
          </h3>
          <div className="decision-list">
            {groupedDecisions.DECOMPOSITION.map((decision, idx) => (
              <DecisionItem key={`decomp-${idx}`} decision={decision} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* EXECUTION decisions */}
      {groupedDecisions.EXECUTION.length > 0 && (
        <div className="decision-group execution-group">
          <h3 className="group-title">
            <span className="group-icon">⚙️</span>
            Execution Decisions
            <span className="group-count">{groupedDecisions.EXECUTION.length}</span>
          </h3>
          <div className="decision-list">
            {groupedDecisions.EXECUTION.map((decision, idx) => (
              <DecisionItem key={`exec-${idx}`} decision={decision} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* VERIFICATION decisions */}
      {groupedDecisions.VERIFICATION.length > 0 && (
        <div className="decision-group verification-group">
          <h3 className="group-title">
            <span className="group-icon">✅</span>
            Verification Decisions
            <span className="group-count">{groupedDecisions.VERIFICATION.length}</span>
          </h3>
          <div className="decision-list">
            {groupedDecisions.VERIFICATION.map((decision, idx) => (
              <DecisionItem key={`verif-${idx}`} decision={decision} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Other decisions */}
      {groupedDecisions.OTHER.length > 0 && (
        <div className="decision-group other-group">
          <h3 className="group-title">
            <span className="group-icon">💭</span>
            Other Decisions
            <span className="group-count">{groupedDecisions.OTHER.length}</span>
          </h3>
          <div className="decision-list">
            {groupedDecisions.OTHER.map((decision, idx) => (
              <DecisionItem key={`other-${idx}`} decision={decision} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Stats footer */}
      <div className="decisions-stats">
        <span className="stat-item">
          <strong>{decisions.length}</strong> decision{decisions.length !== 1 ? 's' : ''} total
        </span>
        {showConfidence && (
          <span className="stat-item">
            <strong>
              {decisions.filter((d) => {
                const conf = d.data?.confidence ?? d.confidence;
                return conf != null && conf >= 0.8;
              }).length}
            </strong>{' '}
            high confidence
          </span>
        )}
      </div>
    </div>
  );
}

DecisionsVisualizer.propTypes = {
  decisions: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      module: PropTypes.string,
      timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
      data: PropTypes.shape({
        decision_type: PropTypes.string,
        rationale: PropTypes.string,
        confidence: PropTypes.number,
        timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
      }),
      decision_type: PropTypes.string,
      rationale: PropTypes.string,
      reasoning: PropTypes.string,
      content: PropTypes.string,
      confidence: PropTypes.number,
    })
  ),
  showTimestamps: PropTypes.bool,
  compact: PropTypes.bool,
  showConfidence: PropTypes.bool,
};

export default DecisionsVisualizer;
