// App.js
import React, { useState } from 'react';
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

  // Called when user hits "Start Game." For now, just logs everything.
  const handleStartGame = () => {
    console.log('Starting game with:', {
      openRouterKey,
      rounds,
      startingAmount,
      playAgainstLLMs,
      modelsInGame,
    });
  };

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

        <MessageLog />
      </div>
    </div>
  );
}

export default App;