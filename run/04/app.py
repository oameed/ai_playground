###############################################
### AI Playground                           ###
### Agentic AI                              ###
### LanggRAPH                               ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import gradio
import signal 
from   dotenv                      import load_dotenv
from   pydantic                    import BaseModel, Field
from   langchain_core.tools        import tool
from   langchain.agents            import create_agent
from   langgraph.checkpoint.memory import MemorySaver
from   langchain.agents.middleware import wrap_tool_call

import pdb

def rJSON(filename):
    import json
    with open(filename, 'r') as fobj:
        x = json.load(fobj)
    return x

def rYAML(filename):
    import yaml
    with open(filename, 'r') as fobj:
        x = yaml.safe_load(fobj)
    return x

def wFILE(string, filename):
    with open(filename, "a", encoding = "utf-8") as fobj:
        fobj.write(string + "\n")

@tool
def send_email(email: str) -> str:
    '''
    Send out an email
    Args:
        email: Both the subject and the body of the email are concatenated in this variable
    '''
    filename = os.path.join(os.environ.get("MY_WORKDIR"), "output" + ".txt")
    wFILE(email, filename)
    return "OK"

@wrap_tool_call
def log_tool_calls(request, handler):
    call = request.tool_call
    print(f"[middleware] calling {call['name']} with {call['args']}")
    return handler(request)

def close_chat():
    print("Shutting Down ...")
    os.kill(os.getpid(), signal.SIGINT)

def initialize_run():
    import shutil
    params  = rJSON("config"  + ".json")
    prompts = rYAML("prompts" + ".yaml")
    workdir = os.path.join("..", "..", "workspace", params['prjname'])
    shutil.rmtree(workdir, ignore_errors = True)
    os.makedirs  (workdir, exist_ok      = True)
    os.environ["MY_WORKDIR"] = workdir
    return params, prompts

def main():
    params, prompts = initialize_run()
    load_dotenv()
    
    tools           = [send_email]
    middleware      = [log_tool_calls]
    
    agent           = create_agent(model         = params ['model'],
                                   tools         = tools           ,
                                   system_prompt = prompts['agent'],
                                   middleware    = middleware       )
    
    filename        = os.path.join(os.environ.get("MY_WORKDIR"), "graph" + ".png")
    graph.get_graph().draw_mermaid_png(output_file_path = filename) 
    
    pdb.set_trace()
    
    with gradio.Blocks() as UI:
        gradio.ChatInterface(chat)
        gradio.Button("End Chat", variant = "stop").click(fn = close_chat)
    UI.launch()
        
    print('Finished!')

if __name__ == "__main__":
    main()

