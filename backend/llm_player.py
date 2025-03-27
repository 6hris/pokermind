from player import Player, PlayerAction, PlayerStatus
import json
from litellm import completion
from pydantic import BaseModel, ValidationError, Field
import re

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
        hole_cards_str = "".join([card.to_treys_str() for card in self.hand])
        call_amount = max(0, current_bet - self.current_bet)
        
        prompt_text = f"""
        You are an expert-level poker AI tasked with making optimal decisions in a poker game. Your job is to WIN! You will be given the current game state and your goal is to determine the best action to take.

        Here's the current game state:

        Game history: {game_history}

        Your Hole Cards: {hole_cards_str}
        Community Cards: {game_state['community_cards']}
        Pot: {game_state['pot']}
        Your Chips: {self.chips}
        Amount to call: {call_amount}
        Minimum raise over current bet: {game_state['min_raise']}
        Current bet to match: {current_bet}

        RESPONSE FORMAT REQUIREMENTS:
        You MUST respond with ONLY a valid JSON object in the following exact format:

        For folding:
        {{
          "action": "fold",
          "raise_amount": null
        }}

        For calling:
        {{
          "action": "call",
          "raise_amount": null
        }}

        For raising:
        {{
          "action": "raise",
          "raise_amount": [your raise amount as integer]
        }}

        CRITICAL RULES:
        1. Output ONLY the JSON object - no explanations, thoughts, or other text
        2. Only use actions "fold", "call", or "raise" (lowercase only)
        3. If action is "raise", raise_amount must be a positive integer (minimum {game_state['min_raise']})
        4. If action is "fold" or "call", raise_amount MUST be null (not a number)
        5. Do not use any other fields in your JSON response

        EXAMPLE VALID RESPONSES:
        {{
          "action": "fold",
          "raise_amount": null
        }}

        {{
          "action": "call",
          "raise_amount": null
        }}

        {{
          "action": "raise",
          "raise_amount": 50
        }}

        Any deviation from this exact format will cause errors. Respond with JSON only.
        """

        return prompt_text.strip()
    
    async def choose_action(self, current_bet, game_state):
        original_prompt = self.generate_prompt(current_bet, game_state)
        max_attempts = 3
        prompt = original_prompt
        error_context = ""
        
        for attempt in range(max_attempts):
            try:
                messages = [{"role": "user", "content": prompt}]
                
                response = completion(
                    model=self.model_name,
                    api_key=self.api_key,
                    messages=messages,
                )
                response_text = response["choices"][0]["message"]["content"]
                print(f"{self.name} raw response: {response_text}")

                action, raise_amount = self.parse_response(response_text)
                return action, raise_amount
                
            except Exception as e:
                error_message = str(e)
                if attempt < max_attempts - 1:
                    print(f"Error parsing {self.name}'s response (attempt {attempt+1}/{max_attempts}): {error_message}. Retrying...")
                    
                    # Add error feedback to the prompt for the next attempt
                    error_context += f"\nYour previous response failed validation: {error_message}\n"
                    error_context += "Please correct your response to match EXACTLY one of the valid formats shown above.\n"
                    error_context += "Remember: The action MUST be 'fold', 'call', or 'raise' with correct raise_amount handling.\n"
                    
                    # Create a new prompt with error feedback
                    prompt = original_prompt + "\n" + error_context
                else:
                    print(f"Error parsing {self.name}'s response after {max_attempts} attempts: {error_message}. Defaulting to FOLD.")
                    action, raise_amount = PlayerAction.FOLD, None
        
        return action, raise_amount
    
    def parse_response(self, response_text: str):
        # First, try to find a JSON object with regex
        json_match = re.search(r"\{.*?\}", response_text, re.DOTALL)
        
        if not json_match:
            # If no JSON found, check if there are simple keywords we can use
            if "fold" in response_text.lower():
                return PlayerAction.FOLD, None
            elif "call" in response_text.lower():
                return PlayerAction.CALL, None
            else:
                raise ValueError("LLM response did not contain any JSON content or recognizable action keywords.")

        json_str = json_match.group()
        
        # Clean up potential JSON formatting issues
        json_str = json_str.replace("'", "\"")
        
        try:
            response_json = json.loads(json_str)
            
            # Add basic validation if fields are missing
            if "action" not in response_json:
                raise ValueError("Missing 'action' field in response")
            
            # Normalize action field (lowercase, trim whitespace)
            if isinstance(response_json["action"], str):
                response_json["action"] = response_json["action"].lower().strip()
            
            # Check for raise with missing raise_amount and try to fix
            if response_json["action"] == "raise" and "raise_amount" not in response_json:
                # Look for a number in the response
                amount_match = re.search(r"\d+", response_text)
                if amount_match:
                    response_json["raise_amount"] = int(amount_match.group())
                else:
                    raise ValueError("Action is 'raise' but no raise_amount provided")
            
            # Run through proper validation
            validated_response = PokerActionResponse.validate_action(response_json)
            
            action = PlayerAction(validated_response.action.lower())
            raise_amount = validated_response.raise_amount
            
            return action, raise_amount
            
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            raise ValueError(f"LLM response validation error: {e}")
        
        except Exception as e:
            raise ValueError(f"Unexpected error parsing LLM response: {e}")