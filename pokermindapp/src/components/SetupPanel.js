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
  gameSpeed,
  setGameSpeed,
  onStartGame,
  gameStatus,
  gameCompleted
}) {
  // Model names that are supported by the backend and tracked in the leaderboard
  const availableModels = ['gpt-4o', 'claude-3-5-sonnet-20240620'];
  const colorPalette = [
    '#FFD6CC', // Light peach
    '#CCE6FF', // Light blue
    '#D6FFCC', // Light mint
    '#FFF2CC', // Light yellow
    '#E6CCFF', // Light lavender
    '#FFCCE6'  // Light pink
  ];
  const gameSpeedOptions = ['fast', 'medium', 'slow'];

  // Track the currently selected model from the dropdown
  const [selectedModel, setSelectedModel] = useState(availableModels[0]);
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  // Get a unique color from the palette to ensure no two players have the same color
  const getUniqueColor = () => {
    // Find all colors already in use
    const usedColors = modelsInGame.map(model => model.color);
    
    // Filter out the used colors to get available colors
    const availableColors = colorPalette.filter(color => !usedColors.includes(color));
    
    if (availableColors.length > 0) {
      // If we have available colors, choose one randomly
      const randomIndex = Math.floor(Math.random() * availableColors.length);
      return availableColors[randomIndex];
    } else {
      // If all colors are used (shouldn't happen with max 6 players), create a slightly different shade
      const randomIndex = Math.floor(Math.random() * colorPalette.length);
      const baseColor = colorPalette[randomIndex];
      
      // Slightly adjust the color by randomly changing RGB values
      const adjustColor = (hexColor) => {
        // Convert hex to RGB
        let r = parseInt(hexColor.slice(1, 3), 16);
        let g = parseInt(hexColor.slice(3, 5), 16);
        let b = parseInt(hexColor.slice(5, 7), 16);
        
        // Adjust each channel slightly
        r = Math.max(180, Math.min(255, r + Math.floor(Math.random() * 40 - 20)));
        g = Math.max(180, Math.min(255, g + Math.floor(Math.random() * 40 - 20)));
        b = Math.max(180, Math.min(255, b + Math.floor(Math.random() * 40 - 20)));
        
        // Convert back to hex
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
      };
      
      return adjustColor(baseColor);
    }
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

    // Create an object containing the model name + unique color
    const newModel = {
      name: selectedModel,
      color: getUniqueColor(),
    };

    setModelsInGame((prev) => [...prev, newModel]);
    setShowModelDropdown(false);
  };
  
  // Determine if controls should be disabled during an active game
  const controlsDisabled = gameStatus === 'running';

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
        style={{ 
          marginBottom: '10px',
          opacity: controlsDisabled ? 0.6 : 1 
        }}
        disabled={controlsDisabled}
      >
        +Add Models
      </button>

      {showModelDropdown && !controlsDisabled && (
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
            <button 
              onClick={() => removeModel(index)}
              disabled={controlsDisabled}
              style={{ opacity: controlsDisabled ? 0.6 : 1 }}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>

      <div className="play-against">
        <label style={{ opacity: controlsDisabled ? 0.6 : 1 }}>
          <input
            type="checkbox"
            checked={playAgainstLLMs}
            onChange={() => setPlayAgainstLLMs(!playAgainstLLMs)}
            disabled={controlsDisabled}
          />
          Play against LLMs?
        </label>
      </div>

      <div className="input-fields">
        <label style={{ opacity: controlsDisabled ? 0.6 : 1 }}>Enter OpenRouter Key:</label>
        <input
          type="text"
          value={openRouterKey}
          onChange={(e) => setOpenRouterKey(e.target.value)}
          disabled={controlsDisabled}
          style={{ opacity: controlsDisabled ? 0.6 : 1 }}
        />

        <label style={{ opacity: controlsDisabled ? 0.6 : 1 }}>Rounds:</label>
        <input
          type="number"
          value={rounds}
          onChange={(e) => setRounds(e.target.value)}
          disabled={controlsDisabled}
          style={{ opacity: controlsDisabled ? 0.6 : 1 }}
        />

        <label style={{ opacity: controlsDisabled ? 0.6 : 1 }}>Starting Amounts ($):</label>
        <input
          type="number"
          value={startingAmount}
          onChange={(e) => setStartingAmount(e.target.value)}
          disabled={controlsDisabled}
          style={{ opacity: controlsDisabled ? 0.6 : 1 }}
        />
        
        <label style={{ opacity: controlsDisabled ? 0.6 : 1 }}>Game Speed:</label>
        <select 
          value={gameSpeed}
          onChange={(e) => setGameSpeed(e.target.value)}
          style={{ 
            marginBottom: '15px',
            opacity: controlsDisabled ? 0.6 : 1
          }}
          disabled={controlsDisabled}
        >
          {gameSpeedOptions.map(speed => (
            <option key={speed} value={speed}>
              {speed.charAt(0).toUpperCase() + speed.slice(1)} {/* Capitalize first letter */}
            </option>
          ))}
        </select>
        <div style={{ 
          fontSize: '0.8em', 
          marginTop: '-12px', 
          color: '#666', 
          textAlign: 'left',
          opacity: controlsDisabled ? 0.6 : 1
        }}>
          {gameSpeed === 'fast' && 'Faster gameplay with minimal delays'}
          {gameSpeed === 'medium' && 'Balanced gameplay with moderate delays'}
          {gameSpeed === 'slow' && 'Slower gameplay with longer delays between actions'}
        </div>
      </div>

      <button 
        onClick={handleStartGameClick} 
        style={{
          backgroundColor: gameCompleted ? '#3366cc' : (gameStatus === 'running' ? '#cc3333' : 'green'),
          padding: '10px 15px',
          fontSize: '16px',
        }}
      >
        {gameCompleted ? 'New Game' : (gameStatus === 'running' ? 'Stop Game' : 'Start Game')}
      </button>
    </div>
  );
}