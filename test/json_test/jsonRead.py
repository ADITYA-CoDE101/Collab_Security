import json

# Example JSON string
json_string = '{"name": "John Doe", ' \
'               "age": 30, ' \
'               "isStudent": false, ' \
'               "courses": [' \
'               {"title": "History", "credits": 3}, {"title": "Math", "credits": 4}]}'

try:
    # Parse the JSON string into a Python dictionary
    data = json.loads(json_string)

    # Now you can work with the data as a Python dictionary
    print("Successfully parsed JSON string.")
    print("Name:", data["name"])
    print("Age:", data["age"])
    print("Is Student:", data["isStudent"])
    print("First course title:", data["courses"][0]["title"])

except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
