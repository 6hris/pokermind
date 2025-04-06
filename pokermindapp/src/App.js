import React, { useState, useEffect } from 'react';
import SetupPanel from './components/SetupPanel';
import PokerTable from './components/PokerTable';
import MessageLog from './components/MessageLog';
import './App.css';

function App() {
  // Basic states
  const [openRouterKey, setOpenRouterKey] = useState('');
  const [rounds, setRounds] = useState('10');
  const [startingAmount, setStartingAmount] = useState('1000');
  const [playAgainstLLMs, setPlayAgainstLLMs] = useState(false);
  const [gameSpeed, setGameSpeed] = useState('medium');

  // NEW: Store the array of selected models in the parent
  const [modelsInGame, setModelsInGame] = useState([]);
  const [gameId, setGameId] = useState(null);
  const [gameLogs, setGameLogs] = useState([]);
  
  // Game state tracking
  const [communityCards, setCommunityCards] = useState('');
  const [pot, setPot] = useState(0);
  const [playerStates, setPlayerStates] = useState([]);
  const [gameStatus, setGameStatus] = useState('waiting');
  const [gameCompleted, setGameCompleted] = useState(false);
  
  // Popup for showing round winner
  const [showWinnerPopup, setShowWinnerPopup] = useState(false);
  const [roundWinner, setRoundWinner] = useState(null);

  // Reset everything to initial state
  const resetGame = () => {
    // Reset all game state
    setGameId(null);
    setGameLogs([]);
    setCommunityCards('');
    setPot(0);
    setPlayerStates([]);
    setGameStatus('waiting');
    setGameCompleted(false);
    setShowWinnerPopup(false);
    
    // Close websocket connection if needed
    // (The useEffect will handle this when gameId changes)
  };

  // Called when user hits "Start Game", "Stop Game", or "New Game"
  const handleStartGame = async () => {
    // If game is running, ask for confirmation before stopping
    if (gameStatus === 'running') {
      const confirmStop = window.confirm("Are you sure you want to stop the current game? All progress will be lost.");
      
      if (confirmStop) {
        // Try to stop the game on the server
        if (gameId) {
          try {
            await fetch(`http://localhost:8000/games/${gameId}/stop`, {
              method: 'POST',
            }).catch(err => console.log('Failed to stop game on server, but continuing cleanup.'));
          } catch (error) {
            console.log('Error stopping game:', error);
            // Continue with client-side cleanup even if server request fails
          }
        }
        
        // Reset everything to initial state
        resetGame();
      }
      return;
    }
    
    // If game completed, reset everything
    if (gameCompleted) {
      resetGame();
    }
    
    // Start a new game
    setGameStatus('running');
    
    try {
      const response = await fetch('http://localhost:8000/games', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          small_blind: 5,
          big_blind: 10,
          player_stack: parseInt(startingAmount),
          num_hands: parseInt(rounds),
          game_speed: gameSpeed,
          llm_players: modelsInGame.map((modelObj, i) => ({
            name: modelObj.name + `-${i + 1}`,
            model: modelObj.name.toLowerCase(),
            //api_key: openRouterKey,
          })),
        }),
      });

      const data = await response.json();
      const gameId = data.game_id;
      console.log('Game created:', gameId);
      setGameId(gameId);

      await fetch(`http://localhost:8000/games/${gameId}/start`, {
        method: 'POST',
      });

      console.log(`Game ${gameId} started`);
    } catch (error) {
      console.error('Failed to start game:', error);
      setGameStatus('waiting');
    }
  };

  useEffect(() => {
    if (!gameId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/games/${gameId}`);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log(`[${message.event}]`, message.data);
      setGameLogs((prevLogs) => [...prevLogs, { type: message.event, data: message.data }]);
      
      // Update game state based on message type
      switch(message.event) {
        case 'game_state':
          setGameStatus(message.data.status);
          setPot(message.data.pot || 0);
          setCommunityCards(message.data.community_cards || '');
          if (message.data.players) {
            // Store player information
            setPlayerStates(message.data.players);
          }
          break;
          
        case 'community_cards_dealt':
          console.log("Received community cards:", message.data.all_cards);
          setCommunityCards(message.data.all_cards);
          break;
          
        case 'hand_started':
          console.log("Hand started:", message.data);
          
          // Update player positions (dealer, SB, BB) from hand_started event
          if (message.data.players) {
            setPlayerStates(prev => {
              // Start with a fresh copy of the previous state
              const updated = [...prev];
              
              // Update player positions based on the new hand
              message.data.players.forEach(player => {
                const playerIndex = updated.findIndex(p => p.name === player.name);
                if (playerIndex >= 0) {
                  updated[playerIndex] = {
                    ...updated[playerIndex],
                    is_dealer: player.is_dealer,
                    is_sb: player.is_sb,
                    is_bb: player.is_bb,
                    position: player.position
                  };
                }
              });
              
              return updated;
            });
          }
          break;
        
        case 'betting_started':
          console.log("Betting started:", message.data);
          break;
          
        case 'player_action':
          console.log("Player action:", message.data.player, message.data.action);
          setPot(message.data.pot);
          
          // Update the specific player's state
          setPlayerStates(prev => {
            const updated = [...prev];
            
            // Find the player who acted
            const playerIndex = updated.findIndex(p => p.name === message.data.player);
            if (playerIndex >= 0) {
              // Update this player's state
              updated[playerIndex] = {
                ...updated[playerIndex],
                chips: message.data.remaining_chips,
                lastAction: message.data.action,
                lastBet: message.data.amount
              };
              
              // If player folded, update their status
              if (message.data.action === 'fold') {
                updated[playerIndex].status = 'folded';
              }
            }
            
            return updated;
          });
          break;
          
        case 'hole_cards_dealt':
          // Log hole cards for debugging
          console.log("Received hole cards:", message.data.players.map(p => `${p.name}: ${p.hole_cards}`));
          
          // Update player hands
          if (message.data.players) {
            setPlayerStates(prev => {
              const updated = [...prev];
              message.data.players.forEach(player => {
                const playerIndex = updated.findIndex(p => p.name === player.name);
                if (playerIndex >= 0) {
                  updated[playerIndex] = {
                    ...updated[playerIndex],
                    holeCards: player.hole_cards
                  };
                }
              });
              return updated;
            });
          }
          break;
          
        case 'hand_complete':
          console.log("Hand complete data:", message.data);
          
          // Get winner info from the winners array
          let winnerName = 'Unknown Player';
          let winningHand = '';
          let winningAmount = message.data.pot || pot;
          let description = '';
          
          // Check if we have winners array in the data
          if (message.data.winners && message.data.winners.length > 0) {
            const winner = message.data.winners[0];
            winnerName = winner.name || 'Unknown Player';
            winningHand = winner.hand || '';
            winningAmount = winner.winnings || winningAmount;
            description = winner.description || '';
          }
          
          setRoundWinner({
            player: winnerName,
            hand: winningHand,
            amount: winningAmount,
            description: description
          });
          
          // Show the winner popup
          setShowWinnerPopup(true);
          
          // Set a timer to hide the popup and reset for next round
          setTimeout(() => {
            setShowWinnerPopup(false);
            
            // Reset pot and cards after the popup is dismissed
            setPot(0);
            setCommunityCards(''); // Reset community cards
            
            // Reset all player states for next round
            setPlayerStates(prev => {
              return prev.map(player => ({
                ...player,
                holeCards: '',  // Clear hole cards
                lastAction: '', // Clear last action
                lastBet: 0,     // Reset last bet
                status: 'active' // Reset folded status to active
              }));
            });
          }, 3000); // Show for 3 seconds
          break;
          
        case 'game_complete':
          console.log("Game completed! Data:", message.data);
          
          // Check if we have a final game winner in the data
          if (message.data && message.data.winners && message.data.winners.length > 0) {
            const gameWinner = message.data.winners[0];
            
            setRoundWinner({
              player: gameWinner.name || 'Overall Winner',
              hand: 'Game Champion',
              amount: gameWinner.total_chips || gameWinner.winnings || 'Champion!',
              description: 'Tournament Winner!'
            });
            
            setShowWinnerPopup(true);
          } else if (message.data && message.data.winner) {
            // Fallback to old format if winners array is not present
            let winnerName = 'Overall Winner';
            
            if (typeof message.data.winner === 'string') {
              winnerName = message.data.winner;
            } else if (typeof message.data.winner === 'object' && message.data.winner.name) {
              winnerName = message.data.winner.name;
            }
            
            setRoundWinner({
              player: winnerName,
              hand: 'Game Champion',
              amount: message.data.total_chips || 'Winner!',
              description: 'Tournament Winner!'
            });
            setShowWinnerPopup(true);
            
            // Hide popup after a delay
            setTimeout(() => {
              setShowWinnerPopup(false);
            }, 5000); // Show for 5 seconds
          }
          
          // Reset all UI state for a clean end
          setPot(0);
          setCommunityCards('');
          setPlayerStates(prev => {
            return prev.map(player => ({
              ...player,
              holeCards: '',
              lastAction: '',
              lastBet: 0
            }));
          });
          
          // Set game completed status
          setGameStatus('completed');
          setGameCompleted(true);
          break;
          
        default:
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
    };

    return () => {
      ws.close();
    };
  }, [gameId]);

  return (
    <div className="App">
      <header>
        <h1>Pokermind</h1>
      </header>

      <div className="container">
        <SetupPanel
          openRouterKey={openRouterKey}
          setOpenRouterKey={setOpenRouterKey}
          rounds={rounds}
          setRounds={setRounds}
          startingAmount={startingAmount}
          setStartingAmount={setStartingAmount}
          playAgainstLLMs={playAgainstLLMs}
          setPlayAgainstLLMs={setPlayAgainstLLMs}
          modelsInGame={modelsInGame}
          setModelsInGame={setModelsInGame}
          gameSpeed={gameSpeed}
          setGameSpeed={setGameSpeed}
          onStartGame={handleStartGame}
          gameStatus={gameStatus}
          gameCompleted={gameCompleted}
        />

        <PokerTable
          models={modelsInGame}
          userIsPlaying={playAgainstLLMs}
          playerStates={playerStates}
          communityCards={communityCards}
          pot={pot}
          gameStatus={gameStatus}
        />

        <MessageLog logs={gameLogs} />
        
        {/* Winner Popup */}
        {showWinnerPopup && roundWinner && (
          <div className="winner-popup" style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '20px',
            borderRadius: '10px',
            boxShadow: '0 0 20px rgba(255, 215, 0, 0.5)',
            textAlign: 'center',
            zIndex: 1000,
            minWidth: '300px',
            border: '2px solid gold'
          }}>
            <h2 style={{ color: 'gold', marginTop: 0 }}>Hand Complete!</h2>
            <p style={{ fontSize: '1.2rem', marginBottom: '8px' }}>
              <strong>{roundWinner.player}</strong> wins!
            </p>
            {roundWinner.hand && (
              <p style={{ marginBottom: '8px' }}>
                Hand: <strong>{roundWinner.hand}</strong>
              </p>
            )}
            {roundWinner.description && (
              <p style={{ marginBottom: '8px', fontStyle: 'italic' }}>
                {roundWinner.description}
              </p>
            )}
            <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'gold' }}>
              ${roundWinner.amount}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;