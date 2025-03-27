import React, { useEffect, useRef } from 'react';

// Helper function to format card strings for better display
function formatCardString(cardStr) {
  if (!cardStr) return '';
  
  return cardStr.trim().split(/\s+/).map(card => {
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
      return `💰 Blinds posted - SB: ${data.sb_player} (${data.sb_amount}), BB: ${data.bb_player} (${data.bb_amount})`;
    case "HOLE_CARDS_DEALT":
      return data.players
        .map((p) => `🂠 ${p.name}'s cards: ${formatCardString(p.hole_cards)}`)
        .join('\\n');
    case "BETTING_STARTED":
      return `♠️ Betting started - Round: ${data.round}, Current Bet: ${data.current_bet}`;
    case "PLAYER_ACTION":
      return `🎲 ${data.player} ${data.action}${data.amount ? ' ' + data.amount + ' chips' : ''}`;
    case "COMMUNITY_CARDS_DEALT":
      return `🃏 ${data.stage.toUpperCase()} dealt: ${formatCardString(data.new_cards)}`;
    case "HAND_COMPLETE":
      return data.winners
        .map((w) => `🏆 ${w.name} wins ${w.winnings} chips with ${formatCardString(w.hand)} (${w.description})`)
        .join('\\n');
    case "GAME_COMPLETE":
      return (
        '✅ Game over! Players:\\n' +
        data.players.map((p) => `- ${p.name}: ${p.chips} chips`).join('\\n')
      );
    case "GAME_STATE":
      return `🧠 Game status: ${data.status}, Pot: ${data.pot}`;
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
          return (
            <div key={index} style={{ marginBottom: '10px' }}>
              <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>
                [{log.type.toUpperCase()}]
              </div>

              {summary ? (
                <div
                  style={{
                    margin: '4px 0',
                    fontStyle: 'italic',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {summary}
                </div>
              ) : (
                // If there's no summary, show a basic fallback
                <div style={{ fontStyle: 'italic', color: '#555' }}>
                  (No summary for this event)
                </div>
              )}

              <details style={{ marginTop: '4px' }}>
                <summary>JSON Details</summary>
                <pre style={{ textAlign: 'left', whiteSpace: 'pre-wrap', marginTop: '4px' }}>
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