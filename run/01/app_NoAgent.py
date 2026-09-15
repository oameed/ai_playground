###############################################
### AI Playground                           ###
### Agentic AI                              ###
### OpenAI API                              ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import json
import gradio
import signal
from   dotenv import load_dotenv
from   openai import OpenAI

def rJSON(filename):
    with open(filename, 'r') as fobj:
        content = json.load(fobj)
    return content

def rYAML(filename):
    import yaml
    with open(filename, 'r') as fobj:
        x = yaml.safe_load(fobj)
    return x

def dFILE(url, filename):
    import gdown
    gdown.download(url, filename)

def rPDF(filename):
    from pypdf import PdfReader
    reader  = PdfReader(filename)
    content = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            content += text
    return content

def wFILE(string, filename):
    with open(filename, "a", encoding = "utf-8") as fobj:
        fobj.write(string + "\n")

def record_user_details(email, name = "NOT PROVIDED", notes = "NOT PROVIDED"):
    filename = os.path.join(os.environ.get("MY_WORKDIR"), "output" + ".txt")
    string   = f"Recording interest from {name} with email {email} and notes {notes}"
    wFILE(string, filename)
    return "OK"

def record_unknown_question(question):
    filename = os.path.join(os.environ.get("MY_WORKDIR"), "output" + ".txt")
    string   = f"Recording-- {question} --asked that I couldn't answer"
    wFILE(string, filename)
    return "OK"

def handle_tool_calls(tool_calls):
    tooloptions   = {"record_user_details"    : record_user_details    ,
                     "record_unknown_question": record_unknown_question }
    results       = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        result    = tooloptions[tool_name](**arguments)        
        results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
    return results

def chat_func(message, history, ai, model, instructions, tools):    
    messages       = [{"role": "system", "content": instructions}] + history + [{"role": "user", "content": message}]
    response       = ai.chat.completions.create(model = model, messages = messages, tools = tools)
    while response.choices[0].finish_reason == "tool_calls":
        message    = response.choices[0].message
        tool_calls = message.tool_calls
        results    = handle_tool_calls(tool_calls)
        messages.append(message)
        messages.extend(results)
        response   = ai.chat.completions.create(model = model, messages = messages, tools = tools)
    return response.choices[0].message.content

def close_chat():
    print("Shutting Down ...")
    os.kill(os.getpid(), signal.SIGINT)

def initialize_run():
    import shutil
    params   = rJSON("config"  + ".json")
    prompts  = rYAML("prompts" + ".yaml")
    tools    = rYAML("tools"   + ".yaml")
    workdir  = os.path.join("..", "..", "workspace", params['prjname'])
    shutil.rmtree(workdir, ignore_errors = True)
    os.makedirs  (workdir, exist_ok      = True)
    os.environ["MY_WORKDIR"] = workdir
    filename = os.path.join(workdir, "resume" + ".pdf")
    dFILE(params['url'], filename)
    prompts['resume' ] = rPDF(filename)
    return params, prompts, tools

def main():
    params, prompts, tools_dict = initialize_run()
    load_dotenv()
    
    instructions                = prompts['agent_01'].format(x = prompts['summary'], y = prompts['resume']) 
   
    tools                       = [{"type"    : "function"                           ,
                                    "function": tools_dict['record_user_details'    ] },
                                   {"type"    : "function"                           , 
                                     "function": tools_dict['record_unknown_question'] } ]
    
    ai                           = OpenAI()
    
    chat                         = lambda message, history: chat_func(message, history, ai, params['model'], instructions, tools)
    
    with gradio.Blocks() as UI:
        gradio.ChatInterface(chat)
        gradio.Button("End Chat", variant = "stop").click(fn = close_chat)
    UI.launch()
    
    print('Finished!')


if __name__ == "__main__":
    main()

