// PokerTable.js
import React from 'react';

// Simple card renderer
const Card = ({ card }) => {
  if (!card || typeof card !== 'string' || card.length < 2) {
    // Return a placeholder for invalid cards
    return (
      <div 
        className="card card-placeholder"
        style={{ 
          display: 'inline-block',
          padding: '3px 5px',
          margin: '2px',
          border: '1px solid #ccc',
          borderRadius: '3px',
          backgroundColor: '#f0f0f0',
          color: '#999',
          fontWeight: 'bold',
          width: '30px',
          height: '40px',
          textAlign: 'center',
          boxShadow: '1px 1px 2px rgba(0,0,0,0.2)',
          fontSize: '0.8em'
        }}
      >
        <div>?</div>
        <div>?</div>
      </div>
    );
  }
  
  // Parse card string
  let value, suit;
  
  // Special handling for 'T' which represents 10
  if (card.charAt(0) === 'T') {
    value = '10';
    suit = card.charAt(1);
  } else {
    value = card.charAt(0);
    // Handle case where value might be multi-character (although unlikely in current format)
    suit = card.charAt(1) || '';
  }
  
  // Map special values to readable form
  const valueMap = {
    'A': 'A',
    'K': 'K',
    'Q': 'Q', 
    'J': 'J',
    'T': '10'
  };
  
  const displayValue = valueMap[value] || value;
  
  // Get color based on suit
  const color = (suit === 'h' || suit === 'd') ? 'red' : 'black';
  
  // Get suit symbol with fallback
  const suitSymbol = {
    'h': '♥',
    'd': '♦',
    'c': '♣',
    's': '♠'
  }[suit] || suit || '?';
  
  return (
    <div 
      className="card"
      style={{ 
        display: 'inline-block',
        padding: '3px 5px',
        margin: '2px',
        border: '1px solid #ccc',
        borderRadius: '3px',
        backgroundColor: 'white',
        color: color,
        fontWeight: 'bold',
        width: '30px',
        height: '40px',
        textAlign: 'center',
        boxShadow: '1px 1px 2px rgba(0,0,0,0.2)',
        fontSize: '0.8em'
      }}
    >
      <div>{displayValue}</div>
      <div>{suitSymbol}</div>
    </div>
  );
};

export default function PokerTable({ 
  models, 
  userIsPlaying, 
  playerStates = [], 
  communityCards = '', 
  pot = 0,
  gameStatus = 'waiting' 
}) {
  // total players = # models + 1 if user is playing
  const totalPlayers = userIsPlaying ? models.length + 1 : models.length;

  // Circle geometry
  const centerX = 300;  // half of 600px
  const centerY = 200;  // half of 400px
  const radius = 180;

  // Each seat's (x,y)
  const seatPositions = Array.from({ length: totalPlayers }, (_, i) => {
    const angle = (2 * Math.PI * i) / totalPlayers - Math.PI / 2; // Start from top
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    return { x, y };
  });
  
  // Parse community cards for rendering - improve parsing to handle spaces
  const commCardsArray = communityCards 
    ? communityCards.trim().split(/\s+/).filter(card => card.length >= 2)
    : [];

  return (
    <div className="table">
      <div className="table-container" style={{ position: 'relative', width: '600px', height: '400px' }}>
        {/* The table background */}
        <div 
          className="poker-table" 
          style={{ 
            position: 'absolute',
            width: '400px',
            height: '200px',
            backgroundColor: '#076324',
            borderRadius: '200px / 100px',
            left: '100px',
            top: '100px',
            boxShadow: 'inset 0 0 20px rgba(0,0,0,0.5)',
            border: '15px solid #542a0a',
            zIndex: 1
          }} 
        />
        
        {/* Pot amount */}
        {pot > 0 && (
          <div 
            style={{ 
              position: 'absolute', 
              top: '130px', 
              left: '50%', 
              transform: 'translateX(-50%)',
              padding: '5px 10px',
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              borderRadius: '10px',
              fontWeight: 'bold',
              zIndex: 3
            }}
          >
            Pot: ${pot}
          </div>
        )}
        
        {/* Community cards */}
        {commCardsArray.length > 0 && (
          <div 
            style={{ 
              position: 'absolute', 
              top: '170px', 
              left: '50%', 
              transform: 'translateX(-50%)',
              display: 'flex',
              gap: '5px',
              zIndex: 3
            }}
          >
            {commCardsArray.map((card, idx) => (
              <Card key={idx} card={card} />
            ))}
          </div>
        )}
        
        {/* Game status */}
        <div 
          style={{ 
            position: 'absolute', 
            top: '20px', 
            left: '50%', 
            transform: 'translateX(-50%)',
            padding: '5px 10px',
            backgroundColor: gameStatus === 'running' ? 'rgba(0, 128, 0, 0.7)' : 'rgba(128, 128, 128, 0.7)',
            color: 'white',
            borderRadius: '5px',
            fontWeight: 'bold',
            zIndex: 3
          }}
        >
          {gameStatus === 'running' ? 'Game in Progress' : 'Waiting to Start'}
        </div>

        {/* Player seats */}
        {seatPositions.map((pos, i) => {
          // Determine if this is a user seat or AI seat
          const isUserSeat = userIsPlaying && i === 0;
          const modelIndex = userIsPlaying ? i - 1 : i;
          const modelObj = isUserSeat ? { name: 'You', color: '#fffcc0' } : models[modelIndex];
          
          if (!modelObj) return null;
          
          // Try to find player state data for this seat
          const playerName = isUserSeat ? 'You' : modelObj.name + `-${modelIndex + 1}`;
          const playerData = playerStates.find(p => p.name === playerName);
          
          // Parse hole cards if available, using improved parsing
          const holeCards = playerData?.holeCards 
            ? playerData.holeCards.trim().split(/\s+/).filter(card => card.length >= 2)
            : [];
          
          return (
            <div key={i}>
              {/* Player seat */}
              <div
                className="player-seat"
                style={{
                  position: 'absolute',
                  width: '120px',
                  left: `${pos.x}px`,
                  top: `${pos.y}px`,
                  transform: 'translate(-50%, -50%)',
                  backgroundColor: modelObj.color,
                  borderColor: '#333',
                  padding: '10px',
                  borderRadius: '10px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  textAlign: 'center',
                  zIndex: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center'
                }}
              >
                {/* Player name */}
                <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                  {playerName}
                  {playerData?.is_dealer && ' 🎲'} 
                  {playerData?.is_sb && ' (SB)'} 
                  {playerData?.is_bb && ' (BB)'}
                </div>
                
                {/* Chips */}
                {playerData && (
                  <div style={{ marginBottom: '5px' }}>
                    ${playerData.chips || 0}
                  </div>
                )}
                
                {/* Last action */}
                {playerData?.lastAction && (
                  <div 
                    style={{ 
                      marginBottom: '5px',
                      padding: '2px 5px',
                      backgroundColor: 'rgba(0,0,0,0.1)',
                      borderRadius: '3px',
                      fontSize: '0.8em'
                    }}
                  >
                    {playerData.lastAction} 
                    {playerData.lastBet > 0 && ` $${playerData.lastBet}`}
                  </div>
                )}
                
                {/* Hole cards */}
                {holeCards.length > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '2px' }}>
                    {holeCards.map((card, idx) => (
                      <Card key={idx} card={card} />
                    ))}
                  </div>
                )}
                
                {/* Status indicator */}
                {playerData?.status && playerData.status !== 'active' && (
                  <div 
                    style={{ 
                      position: 'absolute',
                      top: '-10px',
                      right: '-10px',
                      padding: '2px 5px',
                      backgroundColor: playerData.status === 'folded' ? 'red' : 'gray',
                      color: 'white',
                      borderRadius: '10px',
                      fontSize: '0.7em',
                      fontWeight: 'bold'
                    }}
                  >
                    {playerData.status.toUpperCase()}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}