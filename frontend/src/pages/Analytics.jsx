import { useEffect, useState } from 'react';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const user = getUser();

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/analytics/', 'GET');
      setAnalytics(data);
    } catch (err) {
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-panel">
        <div className="loading-spinner" />
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="page-panel">
        <div className="form-error">{error || 'No analytics data available'}</div>
      </div>
    );
  }

  const { 
    total_cases, 
    cases_by_status, 
    cases_per_admin, 
    resolution_time, 
    cases_timeline, 
    user_satisfaction 
  } = analytics;

  const getPercentage = (value, total) => {
    if (!total) return 0;
    return Math.round((value / total) * 100);
  };

  const getStatusColor = (status) => {
    const colors = {
      open: '#3b82f6',
      assigned: '#f59e0b',
      resolved: '#8b5cf6',
      closed: '#10b981'
    };
    return colors[status] || '#6b7280';
  };

  const getRatingColor = (rating) => {
    if (rating >= 4) return '#10b981';
    if (rating >= 3) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="page-panel">
      <div className="panel-header">
        <h1>📊 Analytics & Reports</h1>
        <p>Comprehensive system statistics and performance metrics</p>
      </div>

      {/* Overview Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-value">{total_cases}</span>
          <span className="stat-label">Total Cases</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{cases_by_status.open}</span>
          <span className="stat-label">Open Cases</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{cases_by_status.assigned}</span>
          <span className="stat-label">Assigned</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{cases_by_status.resolved}</span>
          <span className="stat-label">Resolved</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{cases_by_status.closed}</span>
          <span className="stat-label">Closed</span>
        </div>
      </div>

      {/* Cases by Status - Bar Chart */}
      <div className="glass-panel" style={{ marginTop: '2rem' }}>
        <h2>Cases by Status</h2>
        <div style={{ marginTop: '1.5rem' }}>
          {Object.entries(cases_by_status).map(([status, count]) => {
            const percentage = getPercentage(count, total_cases);
            return (
              <div key={status} style={{ marginBottom: '1rem' }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  marginBottom: '0.5rem',
                  fontSize: '0.9rem'
                }}>
                  <span style={{ textTransform: 'capitalize', fontWeight: 500 }}>
                    {status}
                  </span>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    {count} ({percentage}%)
                  </span>
                </div>
                <div style={{ 
                  width: '100%', 
                  height: '24px', 
                  background: 'rgba(0,0,0,0.05)', 
                  borderRadius: '12px',
                  overflow: 'hidden'
                }}>
                  <div style={{ 
                    width: `${percentage}%`, 
                    height: '100%', 
                    background: getStatusColor(status),
                    transition: 'width 0.3s ease',
                    borderRadius: '12px'
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Cases Per Admin (Owner only) */}
      {user?.role === 'owner' && cases_per_admin && cases_per_admin.length > 0 && (
        <div className="glass-panel" style={{ marginTop: '2rem' }}>
          <h2>Performance by Admin</h2>
          <div style={{ marginTop: '1.5rem', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid rgba(0,0,0,0.1)' }}>
                  <th style={{ textAlign: 'left', padding: '12px 8px' }}>Admin</th>
                  <th style={{ textAlign: 'center', padding: '12px 8px' }}>Total</th>
                  <th style={{ textAlign: 'center', padding: '12px 8px' }}>Open</th>
                  <th style={{ textAlign: 'center', padding: '12px 8px' }}>Assigned</th>
                  <th style={{ textAlign: 'center', padding: '12px 8px' }}>Resolved</th>
                  <th style={{ textAlign: 'center', padding: '12px 8px' }}>Closed</th>
                </tr>
              </thead>
              <tbody>
                {cases_per_admin.map((admin, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                    <td style={{ padding: '12px 8px', fontWeight: 500 }}>
                      {admin.admin_name}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px 8px', fontWeight: 600 }}>
                      {admin.total}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px 8px' }}>
                      {admin.open}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px 8px' }}>
                      {admin.assigned}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px 8px' }}>
                      {admin.resolved}
                    </td>
                    <td style={{ textAlign: 'center', padding: '12px 8px' }}>
                      {admin.closed}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Resolution Time */}
      <div className="glass-panel" style={{ marginTop: '2rem' }}>
        <h2>⏱️ Resolution Performance</h2>
        <div className="stats-row" style={{ marginTop: '1.5rem' }}>
          <div className="stat-card">
            <span className="stat-value">
              {resolution_time.average_hours !== null 
                ? `${resolution_time.average_hours}h`
                : 'N/A'}
            </span>
            <span className="stat-label">Avg. Resolution Time</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{resolution_time.total_closed_cases}</span>
            <span className="stat-label">Cases with Time Data</span>
          </div>
        </div>
        {resolution_time.average_hours !== null && (
          <p style={{ 
            marginTop: '1rem', 
            fontSize: '0.9rem', 
            color: 'var(--text-secondary)',
            textAlign: 'center'
          }}>
            Average time from assignment to closure: <strong>{resolution_time.average_hours} hours</strong>
            {resolution_time.average_hours < 24 && ' 🎉 Excellent response time!'}
          </p>
        )}
      </div>

      {/* Timeline */}
      <div className="glass-panel" style={{ marginTop: '2rem' }}>
        <h2>📅 Case Timeline</h2>
        <div className="stats-row" style={{ marginTop: '1.5rem' }}>
          <div className="stat-card">
            <span className="stat-value">{cases_timeline.today}</span>
            <span className="stat-label">Today</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{cases_timeline.last_7_days}</span>
            <span className="stat-label">Last 7 Days</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{cases_timeline.last_30_days}</span>
            <span className="stat-label">Last 30 Days</span>
          </div>
        </div>

        {/* Daily Cases Chart */}
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Last 30 Days Activity</h3>
          <div style={{ 
            display: 'flex', 
            alignItems: 'flex-end', 
            gap: '2px', 
            height: '150px',
            padding: '0 8px'
          }}>
            {cases_timeline.daily && cases_timeline.daily.slice(-30).map((day, idx) => {
              const maxCount = Math.max(...cases_timeline.daily.map(d => d.count), 1);
              const heightPercent = (day.count / maxCount) * 100;
              return (
                <div 
                  key={idx}
                  style={{ 
                    flex: 1,
                    height: `${heightPercent}%`,
                    minHeight: day.count > 0 ? '4px' : '2px',
                    background: day.count > 0 
                      ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
                      : 'rgba(0,0,0,0.1)',
                    borderRadius: '2px 2px 0 0',
                    position: 'relative',
                    cursor: 'pointer'
                  }}
                  title={`${new Date(day.date).toLocaleDateString()}: ${day.count} cases`}
                >
                  {day.count > 0 && (
                    <span style={{
                      position: 'absolute',
                      top: '-20px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      color: 'var(--text-secondary)'
                    }}>
                      {day.count}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginTop: '8px',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            padding: '0 8px'
          }}>
            <span>30 days ago</span>
            <span>Today</span>
          </div>
        </div>
      </div>

      {/* User Satisfaction */}
      <div className="glass-panel" style={{ marginTop: '2rem' }}>
        <h2>⭐ User Satisfaction</h2>
        <div className="stats-row" style={{ marginTop: '1.5rem' }}>
          <div className="stat-card">
            <span 
              className="stat-value" 
              style={{ 
                color: user_satisfaction.average_rating 
                  ? getRatingColor(user_satisfaction.average_rating)
                  : undefined
              }}
            >
              {user_satisfaction.average_rating !== null 
                ? `${user_satisfaction.average_rating}★`
                : 'N/A'}
            </span>
            <span className="stat-label">Average Rating</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{user_satisfaction.total_feedbacks}</span>
            <span className="stat-label">Total Feedbacks</span>
          </div>
        </div>

        {/* Rating Distribution */}
        {user_satisfaction.rating_distribution && user_satisfaction.rating_distribution.length > 0 && (
          <div style={{ marginTop: '2rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Rating Distribution</h3>
            {user_satisfaction.rating_distribution.sort((a, b) => b.rating - a.rating).map((item) => {
              const percentage = user_satisfaction.total_feedbacks > 0
                ? getPercentage(item.count, user_satisfaction.total_feedbacks)
                : 0;
              return (
                <div key={item.rating} style={{ marginBottom: '1rem' }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    marginBottom: '0.5rem',
                    fontSize: '0.9rem'
                  }}>
                    <span style={{ fontWeight: 500 }}>
                      {item.rating}⭐
                    </span>
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {item.count} ({percentage}%)
                    </span>
                  </div>
                  <div style={{ 
                    width: '100%', 
                    height: '20px', 
                    background: 'rgba(0,0,0,0.05)', 
                    borderRadius: '10px',
                    overflow: 'hidden'
                  }}>
                    <div style={{ 
                      width: `${percentage}%`, 
                      height: '100%', 
                      background: getRatingColor(item.rating),
                      transition: 'width 0.3s ease',
                      borderRadius: '10px'
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {user_satisfaction.total_feedbacks === 0 && (
          <p style={{ 
            marginTop: '1rem', 
            textAlign: 'center', 
            color: 'var(--text-secondary)',
            fontStyle: 'italic'
          }}>
            No feedback received yet
          </p>
        )}
      </div>

      {/* Refresh Button */}
      <div style={{ marginTop: '2rem', textAlign: 'center' }}>
        <button 
          className="button button-primary"
          onClick={fetchAnalytics}
          disabled={loading}
        >
          🔄 Refresh Data
        </button>
      </div>
    </div>
  );
}
