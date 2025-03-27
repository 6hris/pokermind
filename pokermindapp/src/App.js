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

  // Called when user hits "Start Game." For now, just logs everything.
  const handleStartGame = async () => {
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
            setPlayerStates(message.data.players);
          }
          break;
          
        case 'community_cards_dealt':
          console.log("Received community cards:", message.data.all_cards);
          setCommunityCards(message.data.all_cards);
          break;
          
        case 'player_action':
          setPot(message.data.pot);
          // Update the specific player's state
          setPlayerStates(prev => {
            const updated = [...prev];
            const playerIndex = updated.findIndex(p => p.name === message.data.player);
            if (playerIndex >= 0) {
              updated[playerIndex] = {
                ...updated[playerIndex],
                chips: message.data.remaining_chips,
                lastAction: message.data.action,
                lastBet: message.data.amount
              };
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
          setPot(0);
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
      </div>
    </div>
  );
}

export default App;