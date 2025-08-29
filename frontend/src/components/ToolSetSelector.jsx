import { useState, useEffect } from 'react';
import { api } from '../services/api';

const TOOL_SET_DESCRIPTIONS = {
  ecommerce: 'E-commerce workflows: orders, products, checkout',
  agriculture: 'Agricultural workflows: weather, planting, farming decisions',
  events: 'Event management: scheduling, venues, registrations'
};

export default function ToolSetSelector({ currentToolSet, onToolSetChange, disabled }) {
  const [availableToolSets, setAvailableToolSets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchToolSets = async () => {
      try {
        const toolSets = await api.getToolSets();
        // Extract tool set names from the API response
        const names = toolSets.map(toolSet => toolSet.name);
        setAvailableToolSets(names);
      } catch (err) {
        console.error('Failed to fetch tool sets:', err);
        // Fallback to default tool sets
        setAvailableToolSets(['ecommerce', 'agriculture', 'events']);
      } finally {
        setLoading(false);
      }
    };

    fetchToolSets();
  }, []);

  const handleChange = (event) => {
    const newToolSet = event.target.value;
    if (newToolSet !== currentToolSet) {
      onToolSetChange(newToolSet);
    }
  };

  if (loading) {
    return (
      <div className="tool-set-selector">
        <label>Tool Set:</label>
        <select disabled>
          <option>Loading...</option>
        </select>
      </div>
    );
  }

  return (
    <div className="tool-set-selector">
      <label htmlFor="toolset-select">Tool Set:</label>
      <select 
        id="toolset-select"
        value={currentToolSet} 
        onChange={handleChange}
        disabled={disabled}
        className="tool-set-dropdown"
      >
        {availableToolSets.map(toolSet => (
          <option key={toolSet} value={toolSet}>
            {toolSet.charAt(0).toUpperCase() + toolSet.slice(1)} - {TOOL_SET_DESCRIPTIONS[toolSet] || 'Description not available'}
          </option>
        ))}
      </select>
    </div>
  );
}