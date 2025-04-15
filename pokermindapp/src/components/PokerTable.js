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
          width: '25px',
          height: '35px',
          textAlign: 'center',
          boxShadow: '1px 1px 2px rgba(0,0,0,0.2)',
          fontSize: '0.75em'
        }}
      >
        <div>?</div>
        <div>?</div>
      </div>
    );
  }
  
  // Parse card string - handling both formats:
  // Format 1: "Ts" (value + suit code)
  // Format 2: "10♠" (numeric value + suit symbol)
  let displayValue, suitSymbol;
  
  // Check if the card already contains a suit symbol
  if (card.includes('♥') || card.includes('♦') || card.includes('♣') || card.includes('♠')) {
    // Format 2: Card already has suit symbol
    const suitIndex = Math.max(
      card.indexOf('♥'), 
      card.indexOf('♦'), 
      card.indexOf('♣'), 
      card.indexOf('♠')
    );
    
    displayValue = card.substring(0, suitIndex);
    suitSymbol = card.substring(suitIndex);
    
    // Determine color based on suit symbol
    const color = (suitSymbol === '♥' || suitSymbol === '♦') ? 'red' : 'black';
  } else {
    // Format 1: Traditional code format
    let value, suit;
    
    // Special handling for 'T' which represents 10
    if (card.charAt(0) === 'T') {
      value = 'T';
      suit = card.charAt(1);
    } else {
      value = card.charAt(0);
      // Handle case where value might be multi-character
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
    
    displayValue = valueMap[value] || value;
    
    // Convert suit code to symbol
    suitSymbol = {
      'h': '♥',
      'd': '♦',
      'c': '♣',
      's': '♠'
    }[suit] || suit || '?';
  }
  
  // Get color based on suit
  const color = (suitSymbol === '♥' || suitSymbol === '♦') ? 'red' : 'black';
  
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
        width: '25px',
        height: '35px',
        textAlign: 'center',
        boxShadow: '1px 1px 2px rgba(0,0,0,0.2)',
        fontSize: '0.75em'
      }}
    >
      <div>{displayValue}</div>
      <div>{suitSymbol}</div>
    </div>
  );
};

export default function PokerTable({ 
  models, 
  playerStates = [], 
  communityCards = '', 
  pot = 0,
  gameStatus = 'waiting'
}) {
  // total players = number of models
  const totalPlayers = models.length;

  // Circle geometry - centered in the container
  const centerX = 375;  // half of 750px (container width)
  const centerY = 320;  // half of 600px (container height)
  const radius = 240;  // Increased radius to spread out player seats

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
      <div className="table-container" style={{ position: 'relative', width: '750px', height: '600px', padding: '25px 0' }}>
        {/* The table background */}
        <div 
          className="poker-table" 
          style={{ 
            position: 'absolute',
            width: '500px',
            height: '250px',
            backgroundColor: '#076324',
            borderRadius: '250px / 125px',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)', // Perfect centering
            boxShadow: 'inset 0 0 30px rgba(0,0,0,0.5)',
            border: '15px solid #542a0a',
            zIndex: 1
          }} 
        />
        
        {/* Pot amount */}
        {pot > 0 && (
          <div 
            style={{ 
              position: 'absolute', 
              top: '33%', // Positioned above the center (which is at 50%)
              left: '50%', // Centered horizontally
              transform: 'translate(-50%, -50%)', // Center both horizontally and vertically
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
        
        {/* Community cards - properly centered and slightly larger */}
        {commCardsArray.length > 0 && (
          <div 
            style={{ 
              position: 'absolute', 
              top: '50%', // Centered on the table
              left: '50%', // Centered on the table
              transform: 'translate(-50%, -50%)', // Center both horizontally and vertically
              display: 'flex',
              gap: '4px', // Slightly increased gap between cards
              zIndex: 3,
              backgroundColor: 'rgba(7, 99, 36, 0.7)', // Semi-transparent background to highlight cards
              padding: '6px 10px',
              borderRadius: '8px'
            }}
          >
            {commCardsArray.map((card, idx) => (
              <div key={idx} style={{transform: 'scale(0.95)'}}>
                <Card card={card} />
              </div>
            ))}
          </div>
        )}

        {/* Player seats */}
        {seatPositions.map((pos, i) => {
          const modelObj = models[i];
          
          if (!modelObj) return null;
          
          // Try to find player state data for this seat
          // Only add numbers to models if there are multiple of the same type
          const hasDuplicate = models.filter(m => m.name === modelObj.name).length > 1;
          const playerName = hasDuplicate ? modelObj.name + `-${i + 1}` : modelObj.name;
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
                  width: '130px',
                  left: `${pos.x}px`,
                  top: `${pos.y}px`,
                  transform: 'translate(-50%, -50%)',
                  backgroundColor: modelObj.color,
                  border: '1px solid #333',
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