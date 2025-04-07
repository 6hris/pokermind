# PokerMind Testing Plan

| Test Case | Type | Description | Expected Output | Actual Output |
|-----------|------|-------------|----------------|--------------|
| TC-01: Valid Response Parsing | Unit | Test that valid JSON responses from LLM are parsed correctly | Parsed responses match expected actions and amounts | All assertions pass; valid fold/call/raise actions correctly interpreted |
| TC-02: Invalid Response Handling | Unit | Test that invalid responses are properly rejected | Exceptions raised for all invalid formats | All assertions pass; exceptions raised for non-JSON, invalid actions, etc. |
| TC-03: Retry Logic | Unit | Test that LLM retries work after invalid responses | After valid response received, return correct action | After 2 invalid responses, 3rd valid response successfully used |
| TC-04: Default Behavior | Unit | Test behavior when all retries fail | Default to FOLD action | After 3 invalid responses, player folds as expected |
| TC-05: Prompt Generation | Unit | Test that the prompt includes all necessary information | Prompt contains cards, betting info, and instructions | All required elements found in generated prompt |
| TC-06: Real API Response | Integration | Test with real API to verify valid actions are returned | Valid poker action (fold/call/raise) returned | Valid actions returned with appropriate amounts |
| TC-07: Action Variety | Integration | Test that LLM doesn't always make the same decision | Some variety in responses over multiple identical inputs | Different actions observed across multiple runs |
| TC-08: Controlled Hand Simulation | Simulation | Test a full hand with predetermined LLM responses | Game progresses according to mocked responses | LLM raises pre-flop and calls on flop as configured |
| TC-09: Multi-LLM Game | System | Run a full game with multiple LLM players | Complete game with meaningful decisions | Game completes with chip redistribution among AI players |
| TC-10: WebSocket Events | System | Test WebSocket-based observation of a running game | Real-time game updates sent over WebSocket | Events received for game actions, betting rounds, etc. |
| TC-11: Game Setup | Functional | Test basic setup of game and players | Game initialized with correct players and blinds | Players, SB, and BB correctly displayed |
| TC-12: Position Rotation | Functional | Test setting and rotating player positions | Positions rotate correctly after each hand | Dealer, SB, and BB positions move to next players |
| TC-13: Card Dealing | Functional | Test dealing hole and community cards | Cards dealt to players and community | Each player receives 2 cards; community cards dealt in stages |
| TC-14: Betting Round | Functional | Test a complete betting round | Players act in order; pot updated correctly | Bet amounts reflected in pot; player statuses updated |
| TC-15: Full Hand | Functional | Test playing a full poker hand | Complete hand with winner determination | Hand completes with chips awarded to winner |