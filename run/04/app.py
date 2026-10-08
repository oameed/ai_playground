###############################################
### AI Playground                           ###
### Agentic AI                              ###
### LangChain                               ###
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

@tool
def record_user_details(email: str, name: str = "NOT PROVIDED", notes: str = "NOT PROVIDED") -> str:
    '''
    Use this tool to record that a user is interested in being in touch and provided an email address
    
    Args:
        email: The email address of this user
        name : The user's name, if they provided it
        notes: Any additional info about the conversation that's worth recording to give context
    '''
    filename = os.path.join(os.environ.get("MY_WORKDIR"), "output" + ".txt")
    string   = f"Recording interest from {name} with email {email} and notes {notes}"
    wFILE(string, filename)
    return "OK"

@tool
def record_unknown_question(question: str) -> str:
    '''
    Always use this tool to record any question that couldn't be answered as you didn't know the answer

    Args:
        question: The question that couldn't be answered
    '''
    filename = os.path.join(os.environ.get("MY_WORKDIR"), "output" + ".txt")
    string   = f"Recording {question} asked that I couldn't answer"
    wFILE(string, filename)
    return "OK"

@wrap_tool_call
def log_tool_calls(request, handler):
    call = request.tool_call
    print(f"[middleware] calling {call['name']} with {call['args']}")
    return handler(request)

class DualLanguageResponse(BaseModel):
    reply_original  : str = Field(description = "The natural response to the user's query in English.")
    reply_translated: str = Field(description = "The exact translation of reply_original into Farsi." )

class Manager():
    def __init__(self, params, agent):
        self.params = params
        self.agent  = agent
    
    def chat(self, message, history):
        config = {"configurable": {"thread_id": self.params['thread_id']}}
        result = self.agent.invoke({"messages": [{"role": "user", "content": message}]}, config)
        return f"{result['structured_response'].reply_original}\n\n*{result['structured_response'].reply_translated}*"

    def close_chat(self):
        print("Shutting Down ...")
        os.kill(os.getpid(), signal.SIGINT)

    def visualize_graph(self):
        filename = os.path.join(os.environ.get("MY_WORKDIR"), "graph" + ".png")
        self.agent.get_graph().draw_mermaid_png(output_file_path = filename) 

def initialize_run():
    import shutil
    params  = rJSON("config"  + ".json")
    prompts = rYAML("prompts" + ".yaml")
    workdir = os.path.join("..", "..", "workspace", params['prjname'])
    shutil.rmtree(workdir, ignore_errors = True)
    os.makedirs  (workdir, exist_ok      = True)
    os.environ["MY_WORKDIR"] = workdir
    filename = os.path.join(workdir, "resume" + ".pdf")
    dFILE(params['url'], filename)
    prompts['resume' ] = rPDF(filename)
    return params, prompts

def main():
    params, prompts = initialize_run()
    load_dotenv()
    
    system_prompt   = prompts['agent'].format(x = prompts['summary'], y = prompts['resume'])
    tools           = [record_user_details, record_unknown_question]
    middleware      = [log_tool_calls]
    memory          = MemorySaver()
    
    agent           = create_agent(system_prompt   = system_prompt       ,
                                   model           = params['model']     ,
                                   tools           = tools               ,
                                   response_format = DualLanguageResponse,
                                   middleware      = middleware          ,
                                   checkpointer    = memory               )
    
    manager         = Manager(params, agent)
    
    with gradio.Blocks() as UI:
        gradio.ChatInterface(manager.chat)
        gradio.Button("End Chat", variant = "stop").click(fn = manager.close_chat)
    UI.launch()
        
    print('Finished!')

if __name__ == "__main__":
    main()

