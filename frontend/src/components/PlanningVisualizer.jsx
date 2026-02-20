import { useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * PlanningVisualizer Component
 *
 * Displays planning steps and dependency graph from the ROMA Planner module.
 * Shows subtask progression, execution status, and dependencies between steps.
 *
 * @param {Object} props - Component props
 * @param {Array} props.plans - Array of planning messages from Planner
 * @param {boolean} props.showTimestamps - Whether to display timestamps
 * @param {boolean} props.compact - Whether to use compact layout
 * @param {boolean} props.showDependencies - Whether to show dependency graph visualization
 */
export function PlanningVisualizer({
  plans = [],
  showTimestamps = true,
  compact = false,
  showDependencies = true,
}) {
  // Extract and flatten subtasks from all planning messages
  const planningData = useMemo(() => {
    const allSubtasks = [];
    const dependenciesGraph = {};
    let currentStep = 0;
    let latestTimestamp = null;

    (plans || []).forEach((plan) => {
      // Safely extract data from various message formats
      const subtasks = plan.data?.subtasks || plan.subtasks || [];
      const graph = plan.data?.dependencies_graph || plan.dependencies_graph || {};
      const step = plan.data?.current_step ?? plan.current_step ?? 0;
      const timestamp = plan.timestamp || plan.data?.timestamp;

      // Merge subtasks
      subtasks.forEach((subtask) => {
        allSubtasks.push(subtask);
      });

      // Merge dependency graphs
      Object.assign(dependenciesGraph, graph);

      // Update current step (take the latest)
      if (step > currentStep) {
        currentStep = step;
      }

      // Track latest timestamp
      if (timestamp) {
        try {
          const ts = new Date(timestamp);
          if (!latestTimestamp || ts > new Date(latestTimestamp)) {
            latestTimestamp = timestamp;
          }
        } catch {
          // Invalid timestamp, ignore
        }
      }
    });

    // Deduplicate subtasks by ID
    const uniqueSubtasks = [];
    const seenIds = new Set();
    allSubtasks.forEach((subtask) => {
      if (!seenIds.has(subtask.id)) {
        seenIds.add(subtask.id);
        uniqueSubtasks.push(subtask);
      }
    });

    return {
      subtasks: uniqueSubtasks,
      dependenciesGraph,
      currentStep,
      latestTimestamp,
    };
  }, [plans]);

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

  // Get status display properties
  const getStatusInfo = (status) => {
    const statusMap = {
      pending: { label: 'Pending', icon: '⏳', className: 'pending' },
      in_progress: { label: 'In Progress', icon: '🔄', className: 'in-progress' },
      completed: { label: 'Completed', icon: '✅', className: 'completed' },
      failed: { label: 'Failed', icon: '❌', className: 'failed' },
    };
    return statusMap[status] || statusMap.pending;
  };

  // Check if a subtask can be executed based on dependencies
  const canExecute = (subtask) => {
    if (!subtask.dependencies || subtask.dependencies.length === 0) return true;
    return subtask.dependencies.every((depId) => {
      const depTask = planningData.subtasks.find((st) => st.id === depId);
      return depTask && depTask.status === 'completed';
    });
  };

  // Get dependent tasks (tasks that depend on this one)
  const getDependents = (subtaskId) => {
    return planningData.subtasks.filter((st) =>
      st.dependencies?.includes(subtaskId)
    );
  };

  // Render a single subtask item
  const SubtaskItem = ({ subtask, index, isCurrent }) => {
    const statusInfo = getStatusInfo(subtask.status);
    const canRun = canExecute(subtask);
    const dependents = getDependents(subtask.id);
    const timestamp = subtask.timestamp || subtask.created_at;

    return (
      <div
        className={`subtask-item ${statusInfo.className} ${isCurrent ? 'current' : ''} ${!canRun ? 'blocked' : ''} ${compact ? 'compact' : ''}`}
        data-index={index}
        data-subtask-id={subtask.id}
      >
        <div className="subtask-header">
          <span className="subtask-id" aria-label="Subtask ID">
            #{subtask.id}
          </span>
          {showTimestamps && timestamp && (
            <span className="subtask-timestamp" aria-label="Timestamp">
              {formatTimestamp(timestamp)}
            </span>
          )}
          <span className={`subtask-status ${statusInfo.className}`} aria-label={`Status: ${statusInfo.label}`}>
            <span className="status-icon" aria-hidden="true">
              {statusInfo.icon}
            </span>
            <span className="status-label">{statusInfo.label}</span>
          </span>
          {isCurrent && (
            <span className="current-badge" aria-label="Current step">
              📍 Current
            </span>
          )}
        </div>

        <p className="subtask-goal">{subtask.goal}</p>

        {/* Dependencies */}
        {showDependencies && subtask.dependencies && subtask.dependencies.length > 0 && (
          <div className="subtask-dependencies" aria-label="Dependencies">
            <span className="dependencies-label">Depends on:</span>
            <div className="dependencies-list">
              {subtask.dependencies.map((depId) => {
                const depTask = planningData.subtasks.find((st) => st.id === depId);
                const depStatus = depTask ? getStatusInfo(depTask.status) : null;
                return (
                  <span
                    key={depId}
                    className={`dependency-tag ${depStatus ? depStatus.className : 'unknown'}`}
                    aria-label={`Dependency: ${depId}`}
                  >
                    #{depId}
                    {depStatus && (
                      <span className="dep-status-icon" aria-hidden="true">
                        {depStatus.icon}
                      </span>
                    )}
                  </span>
                );
              })}
            </div>
            {!canRun && (
              <span className="blocked-indicator" aria-label="Blocked by dependencies">
                🔒 Blocked
              </span>
            )}
          </div>
        )}

        {/* Dependents */}
        {showDependencies && dependents.length > 0 && (
          <div className="subtask-dependents" aria-label="Dependents">
            <span className="dependents-label">Blocks:</span>
            <div className="dependents-list">
              {dependents.map((dep) => (
                <span
                  key={dep.id}
                  className="dependent-tag"
                  aria-label={`Dependent: ${dep.id}`}
                >
                  #{dep.id}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Estimated effort */}
        {subtask.estimated_effort != null && (
          <div className="subtask-effort" aria-label={`Estimated effort: ${subtask.estimated_effort}`}>
            <span className="effort-label">Effort:</span>
            <div className="effort-bar-container">
              <div
                className="effort-bar"
                style={{ width: `${(subtask.estimated_effort / 10) * 100}%` }}
                aria-label={`${subtask.estimated_effort} out of 10`}
              />
            </div>
            <span className="effort-value">{subtask.estimated_effort}/10</span>
          </div>
        )}
      </div>
    );
  };

  SubtaskItem.propTypes = {
    subtask: PropTypes.object.isRequired,
    index: PropTypes.number.isRequired,
    isCurrent: PropTypes.bool.isRequired,
  };

  // Empty state
  if (!plans || plans.length === 0) {
    return (
      <div className="planning-visualizer empty">
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
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
          <p className="empty-message">Waiting for planning data...</p>
          <p className="empty-hint">Planner subtasks and dependencies will appear here</p>
        </div>
      </div>
    );
  }

  const { subtasks, currentStep, latestTimestamp } = planningData;

  // Group subtasks by status
  const groupedSubtasks = {
    pending: subtasks.filter((st) => st.status === 'pending'),
    in_progress: subtasks.filter((st) => st.status === 'in_progress'),
    completed: subtasks.filter((st) => st.status === 'completed'),
    failed: subtasks.filter((st) => st.status === 'failed'),
  };

  return (
    <div className={`planning-visualizer ${compact ? 'compact' : ''}`}>
      {/* Planning summary header */}
      <div className="planning-summary">
        <h2 className="summary-title">
          <span className="title-icon">📋</span>
          Planning Progress
        </h2>
        <div className="summary-stats">
          <span className="summary-stat">
            <strong>{currentStep + 1}</strong> / <strong>{subtasks.length}</strong> steps
          </span>
          {latestTimestamp && showTimestamps && (
            <span className="summary-timestamp">
              Updated: {formatTimestamp(latestTimestamp)}
            </span>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="planning-progress-bar" role="progressbar" aria-valuenow={currentStep + 1} aria-valuemin={1} aria-valuemax={subtasks.length}>
        <div
          className="progress-fill"
          style={{ width: `${((currentStep + 1) / subtasks.length) * 100}%` }}
        />
      </div>

      {/* In Progress subtasks */}
      {groupedSubtasks.in_progress.length > 0 && (
        <div className="subtask-group in-progress-group">
          <h3 className="group-title">
            <span className="group-icon">🔄</span>
            In Progress
            <span className="group-count">{groupedSubtasks.in_progress.length}</span>
          </h3>
          <div className="subtask-list">
            {groupedSubtasks.in_progress.map((subtask, idx) => (
              <SubtaskItem
                key={subtask.id}
                subtask={subtask}
                index={idx}
                isCurrent={subtasks.indexOf(subtask) === currentStep}
              />
            ))}
          </div>
        </div>
      )}

      {/* Pending subtasks */}
      {groupedSubtasks.pending.length > 0 && (
        <div className="subtask-group pending-group">
          <h3 className="group-title">
            <span className="group-icon">⏳</span>
            Pending
            <span className="group-count">{groupedSubtasks.pending.length}</span>
          </h3>
          <div className="subtask-list">
            {groupedSubtasks.pending.map((subtask, idx) => (
              <SubtaskItem
                key={subtask.id}
                subtask={subtask}
                index={idx}
                isCurrent={subtasks.indexOf(subtask) === currentStep}
              />
            ))}
          </div>
        </div>
      )}

      {/* Completed subtasks */}
      {groupedSubtasks.completed.length > 0 && (
        <div className="subtask-group completed-group">
          <h3 className="group-title">
            <span className="group-icon">✅</span>
            Completed
            <span className="group-count">{groupedSubtasks.completed.length}</span>
          </h3>
          <div className="subtask-list">
            {groupedSubtasks.completed.map((subtask, idx) => (
              <SubtaskItem
                key={subtask.id}
                subtask={subtask}
                index={idx}
                isCurrent={false}
              />
            ))}
          </div>
        </div>
      )}

      {/* Failed subtasks */}
      {groupedSubtasks.failed.length > 0 && (
        <div className="subtask-group failed-group">
          <h3 className="group-title">
            <span className="group-icon">❌</span>
            Failed
            <span className="group-count">{groupedSubtasks.failed.length}</span>
          </h3>
          <div className="subtask-list">
            {groupedSubtasks.failed.map((subtask, idx) => (
              <SubtaskItem
                key={subtask.id}
                subtask={subtask}
                index={idx}
                isCurrent={false}
              />
            ))}
          </div>
        </div>
      )}

      {/* Stats footer */}
      <div className="planning-stats">
        <span className="stat-item">
          <strong>{subtasks.length}</strong> step{subtasks.length !== 1 ? 's' : ''} total
        </span>
        {groupedSubtasks.completed.length > 0 && (
          <span className="stat-item completed-stat">
            <strong>{groupedSubtasks.completed.length}</strong> completed
          </span>
        )}
        {groupedSubtasks.in_progress.length > 0 && (
          <span className="stat-item in-progress-stat">
            <strong>{groupedSubtasks.in_progress.length}</strong> in progress
          </span>
        )}
        {groupedSubtasks.failed.length > 0 && (
          <span className="stat-item failed-stat">
            <strong>{groupedSubtasks.failed.length}</strong> failed
          </span>
        )}
      </div>
    </div>
  );
}

PlanningVisualizer.propTypes = {
  plans: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      module: PropTypes.string,
      timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
      data: PropTypes.shape({
        subtasks: PropTypes.arrayOf(
          PropTypes.shape({
            id: PropTypes.string.isRequired,
            goal: PropTypes.string.isRequired,
            dependencies: PropTypes.arrayOf(PropTypes.string),
            status: PropTypes.oneOf(['pending', 'in_progress', 'completed', 'failed']),
            estimated_effort: PropTypes.number,
          })
        ),
        dependencies_graph: PropTypes.object,
        current_step: PropTypes.number,
        timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)]),
      }),
      subtasks: PropTypes.array,
      dependencies_graph: PropTypes.object,
      current_step: PropTypes.number,
    })
  ),
  showTimestamps: PropTypes.bool,
  compact: PropTypes.bool,
  showDependencies: PropTypes.bool,
};

export default PlanningVisualizer;
