// components/SetupPanel.js
import React, { useState } from 'react';

export default function SetupPanel({
  openRouterKey,
  setOpenRouterKey,
  rounds,
  setRounds,
  startingAmount,
  setStartingAmount,
  playAgainstLLMs,
  setPlayAgainstLLMs,
  onStartGame
}) {
  // You can expand/modify these model names as you like:
  const availableModels = ['GPT4o', 'GPT-3.5', 'CustomModel'];

  // (A) Controls whether the dropdown is visible when you click "+Add Models"
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  // (B) Which model is currently selected in the dropdown
  const [selectedModel, setSelectedModel] = useState(availableModels[0]);

  // (C) The array of models that have been "added" to the game
  const [modelsInGame, setModelsInGame] = useState([]);

  // (D) Add button logic
  const addModel = () => {
    // You can add additional checks (max 5 or 6 AI) if needed
    setModelsInGame((prev) => [...prev, selectedModel]);
    // Optionally hide the dropdown after adding
    setShowModelDropdown(false);
  };

  // (E) Remove a model from the array
  const removeModel = (index) => {
    setModelsInGame((prev) => prev.filter((_, i) => i !== index));
  };

  // (F) Wrap your "start game" logic to pass along selected AI models
  const handleStartGameWithModels = () => {
    // If you need the chosen models at the parent level, pass them here
    onStartGame(modelsInGame);
  };

  return (
    <div className="settings">
      {/* ---- The +Add Models Button ---- */}
      <button
        onClick={() => setShowModelDropdown((prev) => !prev)}
        style={{ marginBottom: '10px' }}
      >
        +Add Models
      </button>

      {/* ---- Show the dropdown when showModelDropdown === true ---- */}
      {showModelDropdown && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            {availableModels.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
          <button onClick={addModel}>Add</button>
          {/* A small 'close' or 'delete' button to hide the dropdown, if desired */}
          <button onClick={() => setShowModelDropdown(false)}>X</button>
        </div>
      )}

      {/* ---- List of models that the user has added ---- */}
      <ul style={{ textAlign: 'left' }}>
        {modelsInGame.map((model, index) => (
          <li key={index} style={{ margin: '5px 0' }}>
            {model}{' '}
            <button onClick={() => removeModel(index)}>Remove</button>
          </li>
        ))}
      </ul>

      {/* ---- Toggle for whether user is playing ---- */}
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

      {/* ---- Game Settings ---- */}
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

      <button onClick={handleStartGameWithModels}>Start Game</button>
    </div>
  );
}