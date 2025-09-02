import { useState, useEffect, useCallback } from 'react';
import MetricCard from './MetricCard';
import ActivityFeed from './ActivityFeed';
import QuickActions from './QuickActions';
import { api } from '../../services/api';
import { useNotification } from '../../contexts/NotificationContext';
import { POLLING_INTERVALS, LIMITS, PERFORMANCE } from '../../constants/app';
import './styles.css';

// Sample activities for demo
const SAMPLE_ACTIVITIES = [
  {
    type: 'demo',
    title: 'E-commerce Demo Completed',
    description: 'Successfully processed 15 test cases with 100% accuracy',
    time: '5 min ago'
  },
  {
    type: 'tool',
    title: 'Weather Tool Executed',
    description: 'Retrieved weather data for Tokyo and Paris',
    time: '12 min ago'
  },
  {
    type: 'system',
    title: 'System Optimization',
    description: 'Memory cache cleared, performance improved by 15%',
    time: '1 hour ago'
  },
  {
    type: 'demo',
    title: 'Agriculture Demo Started',
    description: 'Analyzing weather patterns for crop recommendations',
    time: '2 hours ago'
  }
];

export default function Dashboard() {
  const [metrics, setMetrics] = useState({
    totalQueries: 0,
    activeSessions: 0,
    toolExecutions: 0,
    avgResponseTime: 0,
    activeDemo: 0,
    completedDemos: 0,
    failedDemos: 0
  });
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { showSuccess, showError, showInfo } = useNotification();

  useEffect(() => {
    fetchData();
    // Set up interval for real-time updates
    const interval = setInterval(fetchData, POLLING_INTERVALS.DASHBOARD_METRICS);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    await Promise.all([fetchMetrics(), fetchActivities()]);
  };

  const fetchMetrics = async () => {
    try {
      setError(null);
      // Use enhanced system metrics API
      const data = await api.getEnhancedMetrics();
      
      if (data) {
        // Calculate total tool executions from tool_executions object
        const totalToolExecutions = Object.values(data.tool_executions || {})
          .reduce((sum, count) => sum + count, 0);
          
        setMetrics({
          totalQueries: data.total_queries || 0,
          activeSessions: data.active_sessions || 0,
          toolExecutions: totalToolExecutions,
          avgResponseTime: parseFloat((data.average_query_time || 0).toFixed(2)),
          activeDemos: data.active_demos || 0,
          completedDemos: data.completed_demos || 0,
          failedDemos: data.failed_demos || 0
        });
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      setError('Failed to load metrics');
      // Use fallback data
      setMetrics({
        totalQueries: 0,
        activeSessions: 0,
        toolExecutions: 0,
        avgResponseTime: 0,
        activeDemos: 0,
        completedDemos: 0,
        failedDemos: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchActivities = async () => {
    try {
      // Get recent demo executions to generate activity feed
      const demos = await api.listDemos(null, LIMITS.MAX_RECENT_DEMOS);
      
      const activities = demos.demos.map(demo => {
        const timeAgo = getTimeAgo(demo.started_at);
        
        if (demo.status === 'completed') {
          return {
            type: 'demo',
            title: `${demo.demo_type.charAt(0).toUpperCase() + demo.demo_type.slice(1)} Demo Completed`,
            description: `Execution time: ${demo.execution_time?.toFixed(1)}s, Queries: ${demo.total_queries || 'N/A'}`,
            time: timeAgo
          };
        } else if (demo.status === 'failed') {
          return {
            type: 'system',
            title: `${demo.demo_type.charAt(0).toUpperCase() + demo.demo_type.slice(1)} Demo Failed`,
            description: demo.error_message || 'Demo execution failed',
            time: timeAgo
          };
        } else if (demo.status === 'running') {
          return {
            type: 'demo',
            title: `${demo.demo_type.charAt(0).toUpperCase() + demo.demo_type.slice(1)} Demo Running`,
            description: 'Demo execution in progress...',
            time: timeAgo
          };
        }
        
        return {
          type: 'demo',
          title: `${demo.demo_type.charAt(0).toUpperCase() + demo.demo_type.slice(1)} Demo ${demo.status}`,
          description: `Status: ${demo.status}`,
          time: timeAgo
        };
      }).slice(0, LIMITS.MAX_ACTIVITIES); // Show only last activities
      
      setActivities(activities);
      
    } catch (error) {
      console.error('Failed to fetch activities:', error);
      // Use sample activities as fallback
      setActivities(SAMPLE_ACTIVITIES);
    }
  };

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  const handleQuickAction = useCallback(async (actionId) => {
    try {
      switch (actionId) {
        case 'demo':
          // Start a quick agriculture demo
          const demoResult = await api.startDemo('agriculture', 'dashboard_user', true);
          showSuccess(`Quick demo started! Demo ID: ${demoResult.demo_id}`);
          // Refresh activities to show the new demo
          setTimeout(fetchActivities, POLLING_INTERVALS.ACTIVITY_REFRESH);
          break;
          
        case 'logs':
          // Use system action API to view logs
          const logsResult = await api.performSystemAction('view_logs');
          if (logsResult.success) {
            showInfo('System logs retrieved - check console for details');
            console.log('System logs:', logsResult.data);
          } else {
            showError(`Failed to retrieve logs: ${logsResult.message}`);
          }
          break;
          
        case 'diagnostics':
          // Use system action API to export diagnostics
          const diagResult = await api.performSystemAction('export_diagnostics');
          if (diagResult.success) {
            showInfo('Diagnostics generated - check console for details');
            console.log('Diagnostics data:', diagResult.data);
          } else {
            showError(`Failed to run diagnostics: ${diagResult.message}`);
          }
          break;
          
        case 'docs':
          window.open('https://github.com/your-repo/docs', '_blank');
          showInfo('Opening documentation in new tab');
          break;
          
        default:
          showInfo(`Action: ${actionId}`);
      }
    } catch (error) {
      console.error('Quick action failed:', error);
      showError(`Action failed: ${error.message}`);
    }
  }, [showSuccess, showError, showInfo]);

  if (loading) {
    return (
      <div className="dashboard-view">
        <header className="page-header">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Welcome to DSPy Agent System</p>
        </header>
        
        <div className="dashboard-loading">
          <div className="loading-spinner"></div>
          <p>Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-view">
      <header className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Welcome to DSPy Agent System</p>
      </header>
      
      {error && (
        <div className="dashboard-error">
          <span className="error-icon">❌</span>
          <span>{error}</span>
          <button onClick={fetchData} className="btn-secondary">
            Retry
          </button>
        </div>
      )}
      
      {/* Stats Grid */}
      <div className="stats-grid">
        <MetricCard
          label="Total Queries"
          value={metrics.totalQueries.toLocaleString()}
          change={`${metrics.activeSessions} active sessions`}
          isPositive={metrics.activeSessions > 0}
        />
        <MetricCard
          label="Active Demos"
          value={metrics.activeDemos}
          change={`${metrics.completedDemos} completed`}
          isPositive={metrics.completedDemos > 0}
        />
        <MetricCard
          label="Tool Executions"
          value={metrics.toolExecutions.toLocaleString()}
          change={`${metrics.failedDemos} failed demos`}
          isPositive={metrics.failedDemos === 0}
        />
        <MetricCard
          label="Avg Response Time"
          value={`${metrics.avgResponseTime}s`}
          change={metrics.avgResponseTime > PERFORMANCE.GOOD_RESPONSE_TIME ? "Slow response" : "Good performance"}
          isPositive={metrics.avgResponseTime <= PERFORMANCE.GOOD_RESPONSE_TIME}
        />
      </div>
      
      {/* Recent Activity */}
      <ActivityFeed activities={activities} />
      
      {/* Quick Actions */}
      <QuickActions onAction={handleQuickAction} />
    </div>
  );
}