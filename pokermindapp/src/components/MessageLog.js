import React, { useEffect, useRef } from 'react';

// Helper function to format card strings for better display
function formatCardString(cardStr) {
  if (!cardStr) return '';
  
  return cardStr.trim().split(/\s+/).map(card => {
    // Skip if card is already numeric (like "10" without a suit)
    if (card === "10") return card;
    
    // Handle special case for 'T' (10)
    if (card.startsWith('T')) {
      const suit = card.charAt(1);
      const suitSymbol = {
        'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'
      }[suit] || suit;
      return `10${suitSymbol}`;
    }
    
    // Regular card formatting
    if (card.length >= 2) {
      const value = card.charAt(0);
      const suit = card.charAt(1);
      const suitSymbol = {
        'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'
      }[suit] || suit;
      return `${value}${suitSymbol}`;
    }
    
    return card;
  }).join(' ');
}

function summarizeLogEntry(type, data) {
  switch (type.toUpperCase()) {
    case "HAND_STARTED":
      return `🃏 Hand #${data.hand_number} started. Dealer: ${data.dealer}`;
    case "BLINDS_POSTED":
      return `💰 Blinds posted - SB: ${data.sb_player} ($${data.sb_amount}), BB: ${data.bb_player} ($${data.bb_amount})`;
    case "HOLE_CARDS_DEALT":
      return data.players
        .map((p) => `🂠 ${p.name}'s cards: ${formatCardString(p.hole_cards)}`)
        .join('\n');
    case "BETTING_STARTED":
      return `♠️ Betting round: ${data.round.toUpperCase()}, Current bet: $${data.current_bet}`;
    case "PLAYER_ACTION":
      const actionEmoji = {
        'fold': '❌',
        'check': '👌',
        'call': '📞',
        'raise': '⬆️',
        'all-in': '💥'
      }[data.action] || '🎲';
      return `${actionEmoji} ${data.player} ${data.action}${data.amount ? ' $' + data.amount : ''}`;
    case "COMMUNITY_CARDS_DEALT":
      const stageEmoji = {
        'flop': '🌟',
        'turn': '🎯',
        'river': '🌊'
      }[data.stage.toLowerCase()] || '🃏';
      return `${stageEmoji} ${data.stage.toUpperCase()}: ${formatCardString(data.new_cards)}`;
    case "HAND_COMPLETE":
      return data.winners
        .map((w) => `🏆 ${w.name} wins $${w.winnings} with ${formatCardString(w.hand)} - ${w.description}`)
        .join('\n');
    case "GAME_COMPLETE":
      const sortedPlayers = [...data.players].sort((a, b) => b.chips - a.chips);
      return (
        '🏁 GAME OVER! Final standings:\n' +
        sortedPlayers.map((p, i) => {
          const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '  ';
          return `${medal} ${i+1}. ${p.name}: $${p.chips}`;
        }).join('\n')
      );
    case "GAME_STATE":
      // Skip displaying game state updates, as they're often redundant
      return null;
    default:
      // if we don't recognize it, return nothing
      return null;
  }
}

export default function MessageLog({ logs = [] }) {
  const logEndRef = useRef(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <div className="message-log">
      <h2>Message Log</h2>
      <div className="log-content" style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {logs.map((log, index) => {
          const summary = summarizeLogEntry(log.type, log.data);
          
          // Skip rendering this log entry if there's no summary
          if (!summary) return null;
          
          // Determine background color based on message type
          let bgColor = '#f9f9f9'; // default light gray
          
          if (log.type.toUpperCase() === 'HAND_STARTED') {
            bgColor = '#e6f7ff'; // light blue for new hand
          } else if (log.type.toUpperCase() === 'COMMUNITY_CARDS_DEALT') {
            bgColor = '#f6ffed'; // light green for community cards
          } else if (log.type.toUpperCase() === 'HAND_COMPLETE') {
            bgColor = '#fff7e6'; // light orange for hand complete
          } else if (log.type.toUpperCase() === 'GAME_COMPLETE') {
            bgColor = '#f5f0ff'; // light purple for game complete
          }
          
          return (
            <div 
              key={index} 
              style={{ 
                marginBottom: '8px',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #eee',
                backgroundColor: bgColor
              }}
            >
              <div style={{ 
                fontWeight: 'bold',
                color: '#555',
                fontSize: log.type.toUpperCase() === 'HAND_STARTED' ? '0.95em' : '0.85em',
                lineHeight: '1.5',
                whiteSpace: 'pre-line' // This properly handles newlines in the text
              }}>
                {log.type.toUpperCase() === 'HAND_STARTED' && 
                  <div style={{
                    display: 'block',
                    width: '100%',
                    borderBottom: '1px solid #ddd',
                    paddingBottom: '6px',
                    marginBottom: '6px',
                    color: '#0066cc'
                  }}>
                    {summary}
                  </div>
                }
                {log.type.toUpperCase() !== 'HAND_STARTED' && summary}
              </div>

              <details style={{ 
                marginTop: '4px', 
                fontSize: '0.8em',
                color: '#888' 
              }}>
                <summary>Details</summary>
                <pre style={{ 
                  textAlign: 'left', 
                  whiteSpace: 'pre-wrap', 
                  marginTop: '4px',
                  padding: '6px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '3px',
                  fontSize: '0.9em'
                }}>
                  {JSON.stringify(log.data, null, 2)}
                </pre>
              </details>
            </div>
          );
        })}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}