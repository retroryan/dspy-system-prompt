import { memo } from 'react';

function MetricCard({ label, value, change, isPositive }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {change && (
        <span className={`stat-change ${isPositive ? 'positive' : 'negative'}`}>
          {change}
        </span>
      )}
    </div>
  );
}

export default memo(MetricCard);