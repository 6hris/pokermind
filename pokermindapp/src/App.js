// App.js
import React, { useState } from 'react';
import SetupPanel from './components/SetupPanel';
import PokerTable from './components/PokerTable';
import MessageLog from './components/MessageLog';
import './App.css';

function App() {
  const [openRouterKey, setOpenRouterKey] = useState('');
  const [rounds, setRounds] = useState('');
  const [startingAmount, setStartingAmount] = useState('');
  const [playAgainstLLMs, setPlayAgainstLLMs] = useState(true);

  const handleStartGame = () => {
    console.log('Game started with:', {
      openRouterKey,
      rounds,
      startingAmount,
      playAgainstLLMs,
    });
    // Additional logic to actually kick off the game
  };

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
          onStartGame={handleStartGame}
        />

        <PokerTable />

        <MessageLog />
      </div>
    </div>
  );
}

export default App;