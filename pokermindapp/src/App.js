import React, { useState, useEffect } from 'react';
import SetupPanel from './components/SetupPanel';
import PokerTable from './components/PokerTable';
import MessageLog from './components/MessageLog';
import './App.css';

function App() {
  // Basic states
  const [openRouterKey, setOpenRouterKey] = useState('');
  const [rounds, setRounds] = useState('');
  const [startingAmount, setStartingAmount] = useState('');
  const [playAgainstLLMs, setPlayAgainstLLMs] = useState(true);

  // NEW: Store the array of selected models in the parent
  const [modelsInGame, setModelsInGame] = useState([]);
  const [gameId, setGameId] = useState(null);
  const [gameLogs, setGameLogs] = useState([]);

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
        {/*
          Pass down:
          1) The states for openRouterKey, rounds, etc.
          2) The states for whether user is playing.
          3) The modelsInGame + setModelsInGame so SetupPanel can add or remove models.
          4) The handleStartGame function.
        */}
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
          onStartGame={handleStartGame}
        />

        {/*
          Pass the same "modelsInGame" and "playAgainstLLMs" to PokerTable.
          That way, it can dynamically render seats for each model.
        */}
        <PokerTable
          models={modelsInGame}
          userIsPlaying={playAgainstLLMs}
        />

        <MessageLog logs={gameLogs} />
      </div>
    </div>
  );
}

export default App;