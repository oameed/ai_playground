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

class Manager():
    def __init__(self, ai, model, instructions, tools):
        self.ai           = ai
        self.model        = model
        self.instructions = instructions
        self.tools        = tools

    def chat_run(self, message, history):    
        messages       = [{"role": "system", "content": self.instructions}] + history + [{"role": "user", "content": message}]
        response       = self.ai.chat.completions.create(model = self.model, messages = messages, tools = self.tools)
        while response.choices[0].finish_reason == "tool_calls":
            message    = response.choices[0].message
            tool_calls = message.tool_calls
            results    = self.handle_tool_calls(tool_calls)
            messages.append(message)
            messages.extend(results)
            response   = self.ai.chat.completions.create(model = self.model, messages = messages, tools = self.tools)
        return response.choices[0].message.content

    def chat_close(self):
        print("Shutting Down ...")
        os.kill(os.getpid(), signal.SIGINT)

    def handle_tool_calls(self, tool_calls):
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
    
    manager                     = Manager(ai           = OpenAI()       ,
                                          model        = params['model'],
                                          instructions = instructions   ,
                                          tools        = tools           )
    
    with gradio.Blocks() as UI:
        gradio.ChatInterface(manager.chat_run)
        gradio.Button("End Chat", variant = "stop").click(fn = manager.chat_close)
    UI.launch()
    
    print('Finished!')


if __name__ == "__main__":
    main()

