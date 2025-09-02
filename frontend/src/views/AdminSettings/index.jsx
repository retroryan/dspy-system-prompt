import { useState, useEffect, useCallback } from 'react';
import ConfigSection from './ConfigSection';
import SystemHealth from './SystemHealth';
import { api } from '../../services/api';
import { transformConfigFromAPI, transformConfigToAPI, transformSystemAction } from '../../utils/configTransforms';
import { useNotification } from '../../contexts/NotificationContext';
import { POLLING_INTERVALS, LIMITS } from '../../constants/app';
import './styles.css';

const DEFAULT_CONFIG = {
  llm: {
    provider: 'ollama',
    model: 'llama3.2:3b',
    temperature: 0.7,
    maxTokens: 1024
  },
  agent: {
    maxIterations: 10,
    timeout: 120,
    memorySize: 100,
    debugMode: false
  },
  tools: {
    weatherEnabled: true,
    searchEnabled: true,
    calculatorEnabled: true,
    memoryEnabled: true
  },
  api: {
    endpoint: 'http://localhost:8000',
    timeout: 30,
    retries: 3
  }
};

export default function AdminSettings() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [originalConfig, setOriginalConfig] = useState(DEFAULT_CONFIG);
  const [systemHealth, setSystemHealth] = useState(null);
  const [activeSection, setActiveSection] = useState('llm');
  const [hasChanges, setHasChanges] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  
  const { showSuccess, showError, showInfo } = useNotification();

  // Load initial configuration and system health
  useEffect(() => {
    loadConfiguration();
    loadSystemHealth();
  }, []);

  // Periodic health checks
  useEffect(() => {
    const interval = setInterval(() => {
      loadSystemHealth();
    }, POLLING_INTERVALS.SYSTEM_HEALTH);

    return () => clearInterval(interval);
  }, []);

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const sections = ['llm', 'agent', 'tools', 'api'];
      const configPromises = sections.map(section => 
        api.getConfig(section).catch(err => ({ section, error: err }))
      );
      
      const results = await Promise.all(configPromises);
      const newConfig = {};
      
      results.forEach((result, index) => {
        const section = sections[index];
        if (result.error) {
          console.error(`Failed to load ${section} config:`, result.error);
          newConfig[section] = DEFAULT_CONFIG[section];
        } else {
          newConfig[section] = transformConfigFromAPI(result.config, section);
        }
      });
      
      setConfig(newConfig);
      setOriginalConfig(newConfig);
      setHasChanges(false);
      
    } catch (err) {
      console.error('Failed to load configuration:', err);
      setError('Failed to load configuration');
      setConfig(DEFAULT_CONFIG);
      setOriginalConfig(DEFAULT_CONFIG);
    } finally {
      setLoading(false);
    }
  };

  const loadSystemHealth = async () => {
    try {
      const health = await api.getSystemStatus();
      
      // Transform API response to frontend format
      setSystemHealth({
        status: health.status,
        uptime: health.uptime,
        memory: {
          used: Math.round(health.memory.used || 0),
          total: Math.round(health.memory.total || 100)
        },
        cpu: Math.round(health.cpu || 0),
        activeConnections: health.active_connections || 0,
        lastCheck: health.last_check
      });
      
    } catch (err) {
      console.error('Failed to load system health:', err);
      // Keep previous health data if available, otherwise show error state
      if (!systemHealth) {
        setSystemHealth({
          status: 'error',
          uptime: 'Unknown',
          memory: { used: 0, total: 100 },
          cpu: 0,
          activeConnections: 0,
          lastCheck: new Date().toISOString()
        });
      }
    }
  };

  const handleConfigChange = (section, field, value) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (saving) return;
    
    try {
      setSaving(true);
      setError(null);
      
      const sections = ['llm', 'agent', 'tools', 'api'];
      const savePromises = sections.map(section => {
        const apiConfig = transformConfigToAPI(config[section], section);
        return api.updateConfig(section, {
          section,
          config: apiConfig
        }).catch(err => ({ section, error: err }));
      });
      
      const results = await Promise.all(savePromises);
      const errors = results.filter(result => result.error);
      
      if (errors.length > 0) {
        console.error('Failed to save some configurations:', errors);
        setError(`Failed to save configuration for: ${errors.map(e => e.section).join(', ')}`);
      } else {
        setOriginalConfig(config);
        setHasChanges(false);
        showSuccess('Configuration saved successfully!');
      }
      
    } catch (err) {
      console.error('Failed to save configuration:', err);
      setError('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig(originalConfig);
    setHasChanges(false);
  };

  const handleSystemAction = useCallback(async (action, parameters = null) => {
    try {
      const apiAction = transformSystemAction(action);
      if (!apiAction) {
        console.error('Unknown system action:', action);
        showError('Unknown system action');
        return;
      }
      
      const result = await api.performSystemAction(apiAction, parameters);
      
      if (result.success) {
        showSuccess(result.message);
        
        // Refresh health data after certain actions
        if (['restart_services', 'clear_cache'].includes(apiAction)) {
          setTimeout(loadSystemHealth, POLLING_INTERVALS.ACTIVITY_REFRESH);
        }
        
        // Handle special actions that return data
        if (result.data) {
          if (apiAction === 'view_logs') {
            showInfo('System logs retrieved - check console for details');
            console.log('System logs:', result.data);
          } else if (apiAction === 'export_diagnostics') {
            showInfo('Diagnostics exported - check console for details');
            console.log('Diagnostics data:', result.data);
          }
        }
      } else {
        showError(`Action failed: ${result.message}`);
      }
      
    } catch (err) {
      console.error('System action failed:', err);
      showError('System action failed: ' + err.message);
    }
  }, [showSuccess, showError, showInfo]);

  return (
    <div className="admin-settings-view">
      <header className="page-header">
        <h1 className="page-title">Admin Settings</h1>
        <p className="page-subtitle">System configuration and health monitoring</p>
      </header>

      <div className="admin-container">
        <div className="settings-sidebar">
          <h3 className="sidebar-title">Configuration</h3>
          <nav className="settings-nav">
            <button
              className={`settings-nav-item ${activeSection === 'llm' ? 'active' : ''}`}
              onClick={() => setActiveSection('llm')}
            >
              🤖 LLM Settings
            </button>
            <button
              className={`settings-nav-item ${activeSection === 'agent' ? 'active' : ''}`}
              onClick={() => setActiveSection('agent')}
            >
              🎯 Agent Configuration
            </button>
            <button
              className={`settings-nav-item ${activeSection === 'tools' ? 'active' : ''}`}
              onClick={() => setActiveSection('tools')}
            >
              🔧 Tool Management
            </button>
            <button
              className={`settings-nav-item ${activeSection === 'api' ? 'active' : ''}`}
              onClick={() => setActiveSection('api')}
            >
              🌐 API Settings
            </button>
          </nav>

          <div className="sidebar-divider"></div>

          <h3 className="sidebar-title">System</h3>
          <nav className="settings-nav">
            <button
              className={`settings-nav-item ${activeSection === 'health' ? 'active' : ''}`}
              onClick={() => setActiveSection('health')}
            >
              💚 Health Status
            </button>
          </nav>
        </div>

        <div className="settings-content">
          {loading && (
            <div className="settings-loading">
              <div className="loading-spinner"></div>
              <p>Loading configuration...</p>
            </div>
          )}
          
          {error && (
            <div className="settings-error">
              <span className="error-icon">❌</span>
              <span>{error}</span>
              <button onClick={loadConfiguration} className="btn-secondary">
                Retry
              </button>
            </div>
          )}
          
          {!loading && !error && (
            activeSection === 'health' ? (
              <SystemHealth 
                health={systemHealth} 
                onAction={(action, params) => handleSystemAction(action, params)}
              />
            ) : (
              <>
                <ConfigSection
                  title={getSectionTitle(activeSection)}
                  section={activeSection}
                  config={config[activeSection]}
                  onChange={handleConfigChange}
                />
                
                {hasChanges && (
                  <div className="settings-actions">
                    <button className="btn-secondary" onClick={handleReset} disabled={saving}>
                      Reset Changes
                    </button>
                    <button className="btn-primary" onClick={handleSave} disabled={saving}>
                      {saving ? 'Saving...' : 'Save Configuration'}
                    </button>
                  </div>
                )}
              </>
            )
          )}
        </div>
      </div>
    </div>
  );
}

function getSectionTitle(section) {
  const titles = {
    llm: 'LLM Configuration',
    agent: 'Agent Settings',
    tools: 'Tool Management',
    api: 'API Configuration'
  };
  return titles[section] || 'Settings';
}