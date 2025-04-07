import React, { useState, useEffect } from 'react';
import './Leaderboard.css';

function ModelStats({ modelName, officialOnly, onBack }) {
  const [modelData, setModelData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchModelStats = async () => {
      setLoading(true);
      try {
        // Always use official_only=true
        const response = await fetch(
          `http://localhost:8000/leaderboard/${modelName}?official_only=true`
        );
        if (!response.ok) {
          throw new Error('Failed to fetch model stats');
        }
        const data = await response.json();
        setModelData(data);
        setError(null);
      } catch (err) {
        setError('Failed to load model statistics. Please try again later.');
        console.error('Error fetching model stats:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchModelStats();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modelName]);
  
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };
  
  return (
    <div className="model-stats-container">
      <div className="model-stats-header">
        <button onClick={onBack} className="back-button">
          &larr; Back to Leaderboard
        </button>
        <h2>{modelName} Performance Stats</h2>
        <span className="badge official-badge">
          Official Games
        </span>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {loading ? (
        <div className="loading-spinner">Loading model statistics...</div>
      ) : modelData ? (
        <div className="model-stats-content">
          <div className="stats-summary">
            <div className="stat-card">
              <h3>Games Played</h3>
              <div className="stat-value">{modelData.games_played}</div>
            </div>
            <div className="stat-card">
              <h3>Hands Played</h3>
              <div className="stat-value">{modelData.hands_played}</div>
            </div>
            <div className="stat-card">
              <h3>Net Profit</h3>
              <div className={`stat-value ${modelData.net_profit >= 0 ? 'positive' : 'negative'}`}>
                {modelData.net_profit >= 0 ? '+' : ''}{modelData.net_profit}
              </div>
            </div>
            <div className="stat-card">
              <h3>Win Rate</h3>
              <div className="stat-value">{modelData.win_rate}%</div>
            </div>
            <div className="stat-card">
              <h3>BB/100</h3>
              <div className={`stat-value ${modelData.bb_per_100 >= 0 ? 'positive' : 'negative'}`}>
                {modelData.bb_per_100}
              </div>
            </div>
          </div>
          
          
          {modelData.recent_games && modelData.recent_games.length > 0 && (
            <div className="recent-games">
              <h3>Recent Games</h3>
              <table className="recent-games-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Game ID</th>
                    <th>Starting Chips</th>
                    <th>Final Chips</th>
                    <th>Profit/Loss</th>
                    <th>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {modelData.recent_games.map((game) => (
                    <tr key={game.game_id}>
                      <td>{formatDate(game.end_time)}</td>
                      <td>{game.game_id.slice(0, 8)}...</td>
                      <td>{game.starting_chips}</td>
                      <td>{game.final_chips}</td>
                      <td className={game.profit_loss >= 0 ? 'positive' : 'negative'}>
                        {game.profit_loss >= 0 ? '+' : ''}{game.profit_loss}
                      </td>
                      <td>
                        <span className={`game-type ${game.is_official ? 'official' : 'exhibition'}`}>
                          {game.is_official ? 'Official' : 'Exhibition'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="no-data">No statistics available for {modelName}</div>
      )}
    </div>
  );
}

export default ModelStats;