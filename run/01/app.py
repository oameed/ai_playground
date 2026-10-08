###############################################
### AI Playground                           ###
### Agentic AI                              ###
### OpenAI Agents SDK                       ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import gradio
import signal
from   dotenv import load_dotenv
from   agents import Agent, Runner, trace, function_tool, ModelSettings, SQLiteSession

def rJSON(filename):
    import json
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

@function_tool
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

@function_tool
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

class Manager():
    def __init__(self, params, agent, session):
        self.params  = params
        self.agent   = agent
        self.session = session

    async def chat_run(self, message, history):
        async for status_update in self.orchestrate(message):
            yield status_update

    def chat_close(self):
        print("Shutting Down ...")
        os.kill(os.getpid(), signal.SIGINT)

    async def orchestrate(self, query):
        with trace(self.params['prjdescription']):
            result = await Runner.run(self.agent, query, session = self.session)    
            yield result.final_output

def initialize_run():
    import shutil
    params   = rJSON("config"  + ".json")
    prompts  = rYAML("prompts" + ".yaml")
    workdir  = os.path.join("..", "..", "workspace", params['prjname'])
    shutil.rmtree(workdir, ignore_errors = True)
    os.makedirs  (workdir, exist_ok      = True)
    os.environ["MY_WORKDIR"] = workdir
    filename = os.path.join(workdir, "resume" + ".pdf")
    dFILE(params['url'], filename)
    prompts['resume' ] = rPDF(filename)
    return params, prompts

def main():    
    params, prompts = initialize_run()
    session         = SQLiteSession("12346")
    load_dotenv()
    
    instructions    = prompts['agent_01'].format(x = prompts['summary'], y = prompts['resume'])
    tools           = [record_user_details, record_unknown_question]
    
    agent_01        = Agent(instructions = instructions   ,
                            model        = params['model'],
                            name         = "twin"         ,
                            tools        = tools           )
    
    manager = Manager(params  = params  ,
                      agent   = agent_01,
                      session = session  )
    
    with gradio.Blocks() as UI:
        gradio.ChatInterface(manager.chat_run)
        gradio.Button("End Chat", variant = "stop").click(fn = manager.chat_close)
    UI.launch()
    
    print('Finished!')

if __name__ == "__main__":
    main()

