import json
import os
from openai import OpenAI
from prompt import prompt_sys

async def ai_chat(message, model="gpt-3.5-turbo"):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system", 
                "content": prompt_sys
            },
            {
                "role": "user",
                "content": message,
            }
        ],
        model=model,
    )

    # print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content

record_point = 0

def set_point(point):
    global record_point
    record_point = point
    return record_point

async def run_conversation(message, model="gpt-4o"):
    client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE"),
    )
    messages=[
            {
                "role": "system", 
                "content": "帮我准确地记录下用户积分"
            },
            {
                "role": "user",
                "content": message,
            }
        ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "set_point",
                "description": "Record user points based on their interactions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "point": {"type": "string", "description": "The number of points to set for a user."},
                    },
                    "required": ["point"],
                },
            },
        },
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    print(response)
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "set_point": set_point,
        }
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)
            print(function_response)

# print(run_conversation())
