import openai
import json
import re

import weaviate


# This is the prompt organization and API key for the GPT-3 API
openai.organization = "org-swBTVHqAVDidEQXbYWMx0YVl"
openai.api_key = "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"


model_id = "gpt-3.5-turbo"



# This prompt will set the conditions for the conversation
prompt1 = """
Assume the role of a highly knowledgeable AI doctor, utilizing all the medical journals and data available on the internet up until 2021. As you engage in conversation, mimic the behavior of a real-world physician.

In this role, you will be tasked with the following:
1 - Listen to a description of symptoms or conditions presented by a user.
2 - Based on the information provided, attempt to offer a potential diagnosis. Remember, your purpose is not to replace a doctor's diagnosis but to provide a preliminary assessment.
3 - Provide concise, understandable answers or suggestions related to their health concerns.

During this conversation, ensure your responses are as detailed and accurate as possible. Take your time to think through each situation before providing a conclusion. If certain information is missing or if the symptoms are too vague, ask appropriate questions to gather more information.

Once you believe you have enough information to make a preliminary assessment, provide a potential diagnosis in following format [JSON OBJECT]: {'diagnosis': 'string', 'cure': 'string' , 'confidence': 'number', 'symptoms': ['string', 'string', ...]} . 

To signal the end of the diagnosis process, you should conclude with the statement 'diagnosis-done'.
"""

# This function will parse the diagnosis from the model's response


def parse_diagnosis(text):
    match = re.search(
        "diagnosis: (.*), cure: (.*), confidence: (.*), symptoms: (\[.*\])", text)
    # will return a dictionary with the diagnosis, confidence, and symptoms
    # if the model's response matches the regex
    if match:
        diagnosis = match.group(1).strip()
        cure = match.group(2).strip()
        confidence = float(match.group(3).strip())
        symptoms = json.loads(match.group(4).strip())

        return {
            "diagnosis": diagnosis,
            "cure": cure,
            "confidence": confidence,
            "symptoms": symptoms
        }
    else:
        return None
# This function will ask the user for input until the model's response


def ask_until_done():
    messages = [
        {"role": "system", "content": prompt1},
    ]
# This while loop will continue to ask the user for input until the model's response
    while True:
        user_input = input("What can I help you with? ")
# This if statement will break the loop if the user's input contains the string 'diagnosis-done'
        if 'diagnosis-done' in user_input.lower():
            break
# This will append the user's input to the messages list
        messages.append({"role": "user", "content": user_input})
# This will send the messages list to the GPT-3 API
        response = openai.ChatCompletion.create(
            model=model_id,
            messages=messages,
            temperature=0.5,
        )
# This will parse the model's response from the API
        model_message = response['choices'][0]['message']['content']
# This will print the model's response
        print("Model: ", model_message)
        messages.append({"role": "assistant", "content": model_message})
# This will parse the diagnosis from the model's response
        diagnosis = parse_diagnosis(model_message)
        if diagnosis:
            print("Parsed Diagnosis: ", diagnosis)


# This will save the diagnosis to a JSON file
ask_until_done()

## ----------------------------------------------------------------------------------------------- ##
# This will set the conditions for the conversation to ask for the search terms
prompt2 = """
Assume the role of a highly knowledgeable AI doctor, utilizing all the medical journals and data available on the internet up until 2021. As you engage in conversation, mimic the behavior of a real-world physician.

In this role, you will be tasked with the following:
1. Listen to JSON object given by a user, which contains a description of symptoms or conditions presented by a user.
2. Create JSON object with the searchable query terms that will help identify papers that are relevant to the user's symptoms. Optimize the query terms for pub med, the medical archive.

To signal the end of the diagnosis process, you should conclude with the statement 'query-terms-complete'.
"""

# This function will parse the search terms from the model's response


def parse_search_terms(text):
    match = re.search("'search_terms': (\[.*\])", text)
    if match:
        search_terms = json.loads(match.group(1).strip())
        return {"search_terms": search_terms}
    else:
        return None

# This function will ask the user for input until the model's response


def ask_until_done_query_terms():
    messages = [
        {"role": "system", "content": prompt2},
    ]

    while True:
        user_input = input("What can I help you with? ")

        if 'query-terms-complete' in user_input.lower():
            break

        messages.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model=model_id,
            messages=messages,
            temperature=0.5,
        )

# This will parse the model's response from the API
        model_message = response['choices'][0]['message']['content']

        print("Model: ", model_message)
        messages.append({"role": "assistant", "content": model_message})
# This will parse the search terms from the model's response
        search_terms = parse_search_terms(model_message)
        if search_terms:
            with open('search_terms.json', 'w') as f:
                json.dump(search_terms, f)
            print("Search terms saved to 'search_terms.json'.")


# This will save the search terms to a JSON file
ask_until_done_query_terms()
