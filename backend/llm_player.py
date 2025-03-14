from player import Player, PlayerAction, PlayerStatus
import json
from litellm import completion
from pydantic import BaseModel, ValidationError, Field

class PokerActionResponse(BaseModel):
    action: str = Field(..., pattern="^(fold|call|raise)$")
    raise_amount: int | None = Field(default=None, ge=1)

    @classmethod
    def validate_action(cls, action_data):
        response = cls(**action_data)
        if response.action == "raise":
            if response.raise_amount is None:
                raise ValueError("'raise_amount' must be provided for 'raise' action.")
        else:
            if response.raise_amount is not None:
                raise ValueError(f"'raise_amount' must be null when action is '{response.action}'.")
        return response
    
class LLMPlayer(Player):
    def __init__(self, name, chips, position, model_name, api_key):
        super().__init__(name, False, chips, position)
        self.model_name = model_name
        self.api_key = api_key
    
    def generate_prompt(self, current_bet, game_state):
        game_history = "\n".join(game_state['actions_so_far'])
        prompt_text = f"""
        You are an expert-level poker AI tasked with making optimal decisions in a poker game. Your job is to WIN! WIN! You will be given the current game state and your goal is to determine the best action to take.

        Here's the current game state:

        Game history: {game_history}

        Your Hole Cards: {self.hand}
        Community Cards: {game_state['community_cards']}
        Pot: {game_state['pot']}
        Chips: {self.chips}
        Amount to call: {max(0, current_bet - self.current_bet)}
        Minimum raise over current bet: {game_state['min_raise']}

        Important rules:
        - Determine optimal action: fold, call, or raise.
        - If raising, provide an appropriate raise amount.
        - Output your decision in valid JSON format.

        Output example:
        {{
          "action": "call",
          "raise_amount": null
        }}
        """

        return prompt_text.strip()
    
    def choose_action(self, current_bet, game_state):
        prompt = self.generate_prompt(current_bet, game_state)

        try:
            response = completion(
                model=self.model_name,
                api_key=self.api_key,
                messages=[{"role": "user", "content": prompt}],
            )
            action, raise_amount = self.parse_response(response["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Error parsing LLM response: {e}. Defaulting to FOLD.")
            action, raise_amount = PlayerAction.FOLD, None

        return action, raise_amount
    
    def parse_response(self, response_text: str):
        try:
            response_json = json.loads(response_text.strip())
            validated_response = PokerActionResponse.validate_action(response_json)
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            raise ValueError(f"LLM response validation error: {e}")

        action = PlayerAction(validated_response.action.upper())
        raise_amount = validated_response.raise_amount

        return action, raise_amount