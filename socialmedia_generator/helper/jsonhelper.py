

#Method to parse string and extract json and return as json
def parse_json_from_string(input_string: str) -> dict:
    import json
    import re

    try:
        # Find JSON object within the string
        json_match = re.search(r'\{.*\}', input_string, re.DOTALL)
        if json_match:
            json_data = json.loads(json_match.group())
            return json_data
        else:
            raise ValueError("No JSON object found in the input string.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")        
    except Exception as e:
        raise ValueError(f"An error occurred: {e}")