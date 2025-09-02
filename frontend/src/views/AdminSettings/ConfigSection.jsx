import React from 'react';

export default function ConfigSection({ title, section, config, onChange }) {
  const renderField = (key, value) => {
    const fieldType = typeof value;
    
    if (fieldType === 'boolean') {
      return (
        <div className="config-field" key={key}>
          <label className="config-label">
            <span>{formatLabel(key)}</span>
            <div className="toggle-switch">
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => onChange(section, key, e.target.checked)}
              />
              <span className="toggle-slider"></span>
            </div>
          </label>
        </div>
      );
    }
    
    if (fieldType === 'number') {
      return (
        <div className="config-field" key={key}>
          <label className="config-label">
            <span>{formatLabel(key)}</span>
            <input
              type="number"
              className="config-input"
              value={value}
              onChange={(e) => onChange(section, key, parseFloat(e.target.value))}
              step={key.includes('temperature') ? 0.1 : 1}
              min={key.includes('temperature') ? 0 : 1}
              max={key.includes('temperature') ? 2 : undefined}
            />
          </label>
        </div>
      );
    }
    
    // String or other types
    return (
      <div className="config-field" key={key}>
        <label className="config-label">
          <span>{formatLabel(key)}</span>
          <input
            type="text"
            className="config-input"
            value={value}
            onChange={(e) => onChange(section, key, e.target.value)}
          />
        </label>
      </div>
    );
  };
  
  const formatLabel = (key) => {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .replace(/Llm/g, 'LLM')
      .replace(/Api/g, 'API');
  };
  
  return (
    <div className="config-section">
      <h2 className="section-title">{title}</h2>
      <div className="config-grid">
        {Object.entries(config).map(([key, value]) => renderField(key, value))}
      </div>
      {section === 'llm' && (
        <div className="config-note">
          <span className="note-icon">ℹ️</span>
          <span>Changes to LLM settings will apply to new sessions only</span>
        </div>
      )}
    </div>
  );
}