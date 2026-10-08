###############################################
### AI Playground                           ###
### Agentic AI                              ###
### LangGraph                               ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import gradio
import signal 
from   dotenv                  import load_dotenv
from   typing_extensions       import TypedDict
from   typing                  import Annotated
from   langgraph.graph.message import add_messages
from   langgraph.graph         import StateGraph, START, END
from   langchain_openai        import ChatOpenAI
from   langchain_core.tools    import tool
from   langgraph.prebuilt      import ToolNode, tools_condition

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

class State(TypedDict):
    messages: Annotated[list, add_messages]
    farsi   : str

class ManagerNodes():
    def __init__(self, prompts, agent):
        self.prompts = prompts
        self.agent   = agent
    
    def chatbot(state):
        return {"messages": [self.agent.invoke(state["messages"])]}

    def translator(state):
        last   = state  ["messages"  ][-1].content
        prompt = self.prompts['translator'].format(x = last)
        return {"farsi": self.agent.invoke(prompt).content}

class Manager():
    def __init__(self, params, system_prompt, graph):
        self.params        = params
        self.system_prompt = system_prompt
        self.graph         = graph

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt}] + history + [{"role": "user", "content": message}]
        result   = self.graph.invoke({"messages": messages})
        return f"{result['messages'][-1].content}\n\n*{result['farsi']}*"

    def close_chat(self):
        print("Shutting Down ...")
        os.kill(os.getpid(), signal.SIGINT)

    def visualize_graph(self):
        filename = os.path.join(os.environ.get("MY_WORKDIR"), "graph" + ".png")
        self.graph.get_graph().draw_mermaid_png(output_file_path = filename) 

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
    prompts   ['resume' ]    = rPDF(filename)
    return params, prompts

def main():    
    params, prompts = initialize_run()
    load_dotenv()
    
    system_prompt   = prompts['agent'].format(x = prompts['summary'], y = prompts['resume'])
    tools           = [record_user_details, record_unknown_question]
    agent           = ChatOpenAI(model = params['model'])
    agent           = agent.bind_tools(tools)
    
    managerNodes    = ManagerNodes(prompts, agent)
    builder         = StateGraph(State)
    builder.add_node("chatbot"   , managerNodes.chatbot   )
    builder.add_node("tools"     , ToolNode(tools))
    builder.add_node("translator", managerNodes.translator)
    builder.add_edge             (START       , "chatbot"      )
    builder.add_conditional_edges("chatbot"   , tools_condition, {"tools": "tools", END:"translator"})
    builder.add_edge             ("tools"     , "chatbot"      )
    builder.add_edge             ("translator", END            )
    graph           = builder.compile()
    
    manager         = Manager(params, system_prompt, graph)
    manager.visualize_graph()
    
    with gradio.Blocks() as UI:
        gradio.ChatInterface(manager.chat)
        gradio.Button("End Chat", variant = "stop").click(fn = manager.close_chat)
    UI.launch()
        
    print('Finished!')

if __name__ == "__main__":
    main()

