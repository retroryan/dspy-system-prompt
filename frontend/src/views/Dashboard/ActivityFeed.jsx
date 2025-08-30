import React from 'react';

const ACTIVITY_TYPES = {
  demo: { icon: '🚀', bgClass: 'demo' },
  tool: { icon: '🔧', bgClass: 'tool' },
  system: { icon: '⚡', bgClass: 'system' }
};

export default function ActivityFeed({ activities }) {
  return (
    <div className="recent-activity">
      <div className="section-header">
        <h2 className="section-title">Recent Activity</h2>
        <button className="view-all-btn">View all →</button>
      </div>
      
      <ul className="activity-list">
        {activities.map((activity, index) => {
          const activityType = ACTIVITY_TYPES[activity.type] || ACTIVITY_TYPES.system;
          
          return (
            <li key={index} className="activity-item">
              <div className={`activity-icon ${activityType.bgClass}`}>
                {activityType.icon}
              </div>
              <div className="activity-content">
                <div className="activity-title">{activity.title}</div>
                <div className="activity-description">{activity.description}</div>
              </div>
              <div className="activity-time">{activity.time}</div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}