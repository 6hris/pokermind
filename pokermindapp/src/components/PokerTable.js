// PokerTable.js
import React from 'react';

export default function PokerTable({ models, userIsPlaying }) {
  // total players = # models + 1 if user is playing
  const totalPlayers = userIsPlaying ? models.length + 1 : models.length;

  // Circle geometry
  const centerX = 200;  // half of 400px
  const centerY = 100;  // half of 200px
  const radius = 70;

  // Each seat's (x,y)
  const seatPositions = Array.from({ length: totalPlayers }, (_, i) => {
    const angle = (2 * Math.PI * i) / totalPlayers;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    return { x, y };
  });

  return (
    <div className="table">
      <div className="table-container">
        <div className="poker-table" />

        {seatPositions.map((pos, i) => {
          // Distinguish the user seat (0 if user is playing)
          if (userIsPlaying && i === 0) {
            return (
              <div
                key={i}
                className="player-seat"
                style={{
                  left: `${pos.x}px`,
                  top: `${pos.y}px`,
                  transform: 'translate(-50%, -50%)',
                  // Maybe give the user seat a unique color or style
                  backgroundColor: '#fffcc0', // light yellow
                  borderColor: '#333',
                }}
              >
                You
              </div>
            );
          } else {
            // AI seats
            const modelIndex = userIsPlaying ? i - 1 : i;
            const modelObj = models[modelIndex];
            if (!modelObj) {
              // no model -> skip or default
              return null;
            }

            return (
              <div
                key={i}
                className="player-seat"
                style={{
                  left: `${pos.x}px`,
                  top: `${pos.y}px`,
                  transform: 'translate(-50%, -50%)',
                  backgroundColor: modelObj.color,
                  borderColor: '#333',
                }}
              >
                {modelObj.name}
              </div>
            );
          }
        })}
      </div>
    </div>
  );
}