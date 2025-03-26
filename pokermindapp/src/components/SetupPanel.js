// SetupPanel.js
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
  modelsInGame,
  setModelsInGame,
  onStartGame
}) {
  // Example model names and a small color palette
  const availableModels = ['gpt-4o', 'gpt-3.5', 'CustomModel'];
  const colorPalette = ['red', 'blue', 'green', 'orange', 'purple', 'magenta'];

  // Track the currently selected model from the dropdown
  const [selectedModel, setSelectedModel] = useState(availableModels[0]);
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  // Pick a random color from the palette
  const getRandomColor = () => {
    const randomIndex = Math.floor(Math.random() * colorPalette.length);
    return colorPalette[randomIndex];
  };

  // Add a new model (with a color) to the parent array
  const addModel = () => {
    const maxAIs = playAgainstLLMs ? 5 : 6;
    if (modelsInGame.length >= maxAIs) {
      alert(
        playAgainstLLMs
          ? 'Cannot add more than 5 AI if the user is playing.'
          : 'Cannot add more than 6 AI if the user is not playing.'
      );
      return;
    }

    // Create an object containing the model name + color
    const newModel = {
      name: selectedModel,
      color: getRandomColor(),
    };

    setModelsInGame((prev) => [...prev, newModel]);
    setShowModelDropdown(false);
  };

  // Remove a model by index
  const removeModel = (index) => {
    setModelsInGame((prev) => prev.filter((_, i) => i !== index));
  };

  // Start game
  const handleStartGameClick = () => {
    onStartGame();
  };

  return (
    <div className="settings">
      <button
        onClick={() => setShowModelDropdown(!showModelDropdown)}
        style={{ marginBottom: '10px' }}
      >
        +Add Models
      </button>

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
          <button onClick={() => setShowModelDropdown(false)}>X</button>
        </div>
      )}

      {/* Show the list of models with color dots */}
      <ul style={{ textAlign: 'left' }}>
        {modelsInGame.map((modelObj, index) => (
          <li key={index} style={{ margin: '5px 0' }}>
            {/* color dot */}
            <span
              style={{
                display: 'inline-block',
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: modelObj.color,
                marginRight: '8px',
              }}
            />
            {modelObj.name}{' '}
            <button onClick={() => removeModel(index)}>Remove</button>
          </li>
        ))}
      </ul>

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

      <button onClick={handleStartGameClick}>Start Game</button>
    </div>
  );
}