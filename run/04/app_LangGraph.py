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
from   typing_extensions           import TypedDict
from   typing                      import Annotated
from   langgraph.graph.message     import add_messages
from   langgraph.graph             import StateGraph, START, END
from   langchain_openai            import ChatOpenAI
from   langchain_core.tools        import tool
from   langgraph.prebuilt          import ToolNode, tools_condition
from   langgraph.checkpoint.memory import MemorySaver

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

class State(TypedDict):
    messages: Annotated[list, add_messages]
    farsi   : str

def visualize_graph(agent):
    filename = os.path.join(os.environ.get("MY_WORKDIR"), "graph" + ".png")
    agent.get_graph().draw_mermaid_png(output_file_path = filename) 

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
    
    def node_chatbot(state: State) -> dict:
        return {"messages": [agent.invoke(state["messages"])]}
    
    def node_translator(state: State) -> dict:
        last   = state  ["messages"  ][-1].content
        prompt = prompts['translator'].format(x = last)
        return {"farsi": agent.invoke(prompt).content}
    
    def chat(message, history):
        config = {"configurable": {"thread_id": params['thread_id']}}
        result = graph.invoke({"messages": [{"role": "user", "content": message}]}, config)
        return f"{result['messages'][-1].content}\n\n*{result['farsi']}*"
    
    params, prompts = initialize_run()
    load_dotenv()
    
    tools           = [send_email]
    
    agent           = ChatOpenAI(model = params['model'])
    agent           = agent.bind_tools(tools)
    
    builder         = StateGraph(State)
    builder.add_node("chatbot"   , node_chatbot   )
    builder.add_node("tools"     , ToolNode(tools))
    builder.add_node("translator", node_translator)
    builder.add_edge             (START       , "chatbot"      )
    builder.add_conditional_edges("chatbot"   , tools_condition, {"tools": "tools", END:"translator"})
    builder.add_edge             ("tools"     , "chatbot"      )
    builder.add_edge             ("translator", END            )
    memory          = MemorySaver()
    graph           = builder.compile(checkpointer = memory)
    visualize_graph(agent)
    
    with gradio.Blocks() as UI:
        gradio.ChatInterface(chat)
        gradio.Button("End Chat", variant = "stop").click(fn = close_chat)
    UI.launch()
        
    print('Finished!')

if __name__ == "__main__":
    main()

