import { useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * ThoughtsVisualizer Component
 *
 * Displays inner thoughts and reasoning from the ROMA Atomizer module.
 * Shows the AI's internal decision-making process in real-time.
 *
 * @param {Object} props - Component props
 * @param {Array} props.messages - Array of reasoning messages from Atomizer
 * @param {boolean} props.showTimestamps - Whether to display timestamps
 * @param {boolean} props.compact - Whether to use compact layout
 */
export function ThoughtsVisualizer({
  messages = [],
  showTimestamps = true,
  compact = false,
}) {
  // Group messages by node_type for better organization
  const groupedThoughts = useMemo(() => {
    const groups = {
      PLAN: [],
      EXECUTE: [],
      OTHER: [],
    };

    (messages || []).forEach((msg) => {
      // Safely extract data from various message formats
      const nodeType = msg.data?.node_type || msg.node_type || msg.type || 'OTHER';

      if (nodeType === 'PLAN' || nodeType === 'EXECUTE') {
        groups[nodeType].push(msg);
      } else {
        groups.OTHER.push(msg);
      }
    });

    return groups;
  }, [messages]);

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

  // Get the reasoning text from a message
  const getReasoning = (msg) => {
    if (!msg) return '';
    return msg.data?.reasoning || msg.reasoning || msg.content || '';
  };

  // Get the node type from a message
  const getNodeType = (msg) => {
    if (!msg) return '';
    return msg.data?.node_type || msg.node_type || msg.type || '';
  };

  // Render a single thought item
  const ThoughtItem = ({ msg, index }) => {
    const reasoning = getReasoning(msg);
    const nodeType = getNodeType(msg);
    const timestamp = msg.timestamp || msg.data?.timestamp;

    if (!reasoning) return null;

    return (
      <div
        className={`thought-item ${nodeType.toLowerCase()} ${compact ? 'compact' : ''}`}
        data-index={index}
      >
        {showTimestamps && timestamp && (
          <span className="thought-timestamp" aria-label="Timestamp">
            {formatTimestamp(timestamp)}
          </span>
        )}
        {nodeType && (
          <span className={`thought-badge thought-${nodeType.toLowerCase()}`} aria-label="Node type">
            {nodeType}
          </span>
        )}
        <p className="thought-content">{reasoning}</p>
      </div>
    );
  };

  ThoughtItem.propTypes = {
    msg: PropTypes.object.isRequired,
    index: PropTypes.number.isRequired,
  };

  // Empty state
  if (!messages || messages.length === 0) {
    return (
      <div className="thoughts-visualizer empty">
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
            <path d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p className="empty-message">Waiting for inner thoughts...</p>
          <p className="empty-hint">Atomizer reasoning will appear here</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`thoughts-visualizer ${compact ? 'compact' : ''}`}>
      {/* PLAN type thoughts */}
      {groupedThoughts.PLAN.length > 0 && (
        <div className="thought-group plan-group">
          <h3 className="group-title">
            <span className="group-icon">📋</span>
            Planning Thoughts
            <span className="group-count">{groupedThoughts.PLAN.length}</span>
          </h3>
          <div className="thought-list">
            {groupedThoughts.PLAN.map((msg, idx) => (
              <ThoughtItem key={`plan-${idx}`} msg={msg} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* EXECUTE type thoughts */}
      {groupedThoughts.EXECUTE.length > 0 && (
        <div className="thought-group execute-group">
          <h3 className="group-title">
            <span className="group-icon">⚡</span>
            Execution Thoughts
            <span className="group-count">{groupedThoughts.EXECUTE.length}</span>
          </h3>
          <div className="thought-list">
            {groupedThoughts.EXECUTE.map((msg, idx) => (
              <ThoughtItem key={`exec-${idx}`} msg={msg} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Other thoughts */}
      {groupedThoughts.OTHER.length > 0 && (
        <div className="thought-group other-group">
          <h3 className="group-title">
            <span className="group-icon">💭</span>
            Other Thoughts
            <span className="group-count">{groupedThoughts.OTHER.length}</span>
          </h3>
          <div className="thought-list">
            {groupedThoughts.OTHER.map((msg, idx) => (
              <ThoughtItem key={`other-${idx}`} msg={msg} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Stats footer */}
      <div className="thoughts-stats">
        <span className="stat-item">
          <strong>{messages.length}</strong> thought{messages.length !== 1 ? 's' : ''} total
        </span>
        {groupedThoughts.PLAN.length > 0 && (
          <span className="stat-item">
            <strong>{groupedThoughts.PLAN.length}</strong> planning
          </span>
        )}
        {groupedThoughts.EXECUTE.length > 0 && (
          <span className="stat-item">
            <strong>{groupedThoughts.EXECUTE.length}</strong> execution
          </span>
        )}
      </div>
    </div>
  );
}

ThoughtsVisualizer.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      module: PropTypes.string,
      timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
      data: PropTypes.shape({
        reasoning: PropTypes.string,
        node_type: PropTypes.oneOf(['PLAN', 'EXECUTE']),
        timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
      }),
      reasoning: PropTypes.string,
      node_type: PropTypes.oneOf(['PLAN', 'EXECUTE']),
      content: PropTypes.string,
    })
  ),
  showTimestamps: PropTypes.bool,
  compact: PropTypes.bool,
};

export default ThoughtsVisualizer;
