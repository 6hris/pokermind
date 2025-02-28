// src/App.js
import React, { useState } from 'react';
import './App.css';

function App() {
    const [openRouterKey, setOpenRouterKey] = useState('');
    const [rounds, setRounds] = useState('');
    const [startingAmount, setStartingAmount] = useState('');
    const [playAgainstLLMs, setPlayAgainstLLMs] = useState(true);

    const handleStartGame = () => {
        // Logic to start the game
        console.log('Game started with:', { openRouterKey, rounds, startingAmount, playAgainstLLMs });
    };

    return (
        <div className="App">
            <header>
                <h1>Pokermind</h1>
            </header>
            <div className="container">
                <div className="settings">
                    <div className="model-selection">
                        <label>+Add models</label>
                        <select>
                            <option value="GPT4o">GPT4o</option>
                            {/* Add more models as needed */}
                        </select>
                    </div>
                    <div className="play-against">
                        <label>
                            <input
                                type="checkbox"
                                checked={playAgainstLLMs}
                                onChange={() => setPlayAgainstLLMs(!playAgainstLLMs)}
                            />
                            Play against LLMs?
                        </label>
                    </div>
                    <div className="input-fields">
                        <label>Enter OpenRouter Key:</label>
                        <input
                            type="text"
                            value={openRouterKey}
                            onChange={(e) => setOpenRouterKey(e.target.value)}
                        />
                        <label>Rounds:</label>
                        <input
                            type="number"
                            value={rounds}
                            onChange={(e) => setRounds(e.target.value)}
                        />
                        <label>Starting Amounts ($):</label>
                        <input
                            type="number"
                            value={startingAmount}
                            onChange={(e) => setStartingAmount(e.target.value)}
                        />
                    </div>
                    <button onClick={handleStartGame}>Start Game</button>
                </div>
                <div className="table">
                    <div className="poker-table"></div>
                </div>
                <div className="message-log">
                    <h2>Message Log</h2>
                    <div className="log-content"></div>
                </div>
            </div>
        </div>
    );
}

export default App;