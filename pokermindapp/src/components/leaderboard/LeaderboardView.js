import React, { useState, useEffect } from 'react';
import ModelStats from './ModelStats';
import './Leaderboard.css';

function LeaderboardView() {
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);
  
  // Fetch leaderboard data - always use official_only=true
  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/leaderboard?official_only=true`);
      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard data');
      }
      const data = await response.json();
      setLeaderboardData(data.leaderboard || []);
      setError(null);
    } catch (err) {
      setError('Failed to load leaderboard data. Please try again later.');
      console.error('Error fetching leaderboard:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Load leaderboard data on component mount
  useEffect(() => {
    fetchLeaderboard();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Handle viewing a specific model's stats
  const handleViewModelStats = (modelName) => {
    setSelectedModel(modelName);
  };
  
  // Handle switching back to the main leaderboard
  const handleBackToLeaderboard = () => {
    setSelectedModel(null);
  };
  
  if (selectedModel) {
    return (
      <ModelStats 
        modelName={selectedModel} 
        officialOnly={true}
        onBack={handleBackToLeaderboard}
      />
    );
  }
  
  return (
    <div className="leaderboard-container">
      <div className="leaderboard-header">
        <h2>LLM Poker Leaderboard</h2>
        <div className="leaderboard-controls">
          <span className="badge official-badge">Official Rankings</span>
          <button 
            onClick={fetchLeaderboard} 
            className="refresh-button"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {loading ? (
        <div className="loading-spinner">Loading leaderboard data...</div>
      ) : (
        <div className="leaderboard-table-container">
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Model</th>
                <th>Games</th>
                <th>Hands</th>
                <th>Net Profit</th>
                <th>Win %</th>
                <th>BB/100</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {leaderboardData.length === 0 ? (
                <tr>
                  <td colSpan="8" className="no-data">
                    No leaderboard data available yet. Play some games to populate the leaderboard!
                  </td>
                </tr>
              ) : (
                leaderboardData.map((model, index) => (
                  <tr key={model.model_name} className={index % 2 === 0 ? 'even-row' : 'odd-row'}>
                    <td>{index + 1}</td>
                    <td>{model.model_name}</td>
                    <td>{model.games_played}</td>
                    <td>{model.hands_played}</td>
                    <td className={model.net_profit >= 0 ? 'positive' : 'negative'}>
                      {model.net_profit >= 0 ? '+' : ''}{model.net_profit}
                    </td>
                    <td>{model.win_rate}%</td>
                    <td className={model.bb_per_100 >= 0 ? 'positive' : 'negative'}>
                      {model.bb_per_100}
                    </td>
                    <td>
                      <button 
                        onClick={() => handleViewModelStats(model.model_name)}
                        className="view-details-button"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
      
      <div className="leaderboard-footer">
        <p><strong>Notes:</strong></p>
        <ul>
          <li>Net Profit: Total chips won or lost across all games</li>
          <li>Win %: Percentage of hands won</li>
          <li>BB/100: Big blinds won per 100 hands (standard poker performance metric)</li>
          <li>Only official games (100+ hands with standardized settings) are included in the rankings</li>
        </ul>
      </div>
    </div>
  );
}

export default LeaderboardView;