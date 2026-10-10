###############################################
### AI Playground                           ###
### Agentic AI                              ###
### OpenAI Agents SDK                       ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import asyncio
import gradio
import signal
from   dotenv import load_dotenv
from   agents import Agent, Runner, trace, function_tool, ModelSettings

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

@function_tool
def send_email(email: str) -> str:
    '''
    Send out an email with the given subject and body to all sales prospects
    Args:
        email: Both the subject and the body of the email are concatenated in this variable
    '''
    filename = os.path.join(os.environ.get("MY_WORKDIR"), "output" + ".txt")
    wFILE(email, filename)
    return "OK"

class Manager():
    def __init__(self, params, agent_01, agent_02, agent_03, agent_04):
        self.params   = params
        self.agent_01 = agent_01
        self.agent_02 = agent_02
        self.agent_03 = agent_03
        self.agent_04 = agent_04

    async def chat_run(self,query):
        async for status_update in self.orchestrate(query):
            yield status_update
    
    def chat_close(self):
        print("Shutting Down ...")
        os.kill(os.getpid(), signal.SIGINT)

    async def orchestrate(self, query):
        with trace(self.params['prjdescription']):
            yield "Writing emails   ..."
            emails = await self.write(query)
            yield "Picking emails   ..."
            emails = "Cold sales emails:\n\n" + "\n\nEmail:\n\n".join(emails)
            email  = await self.pick(emails)
            yield email

    async def write(self, query):
        result = await asyncio.gather(Runner.run(self.agent_02, query),
                                      Runner.run(self.agent_03, query),
                                      Runner.run(self.agent_04, query) )
        return [r.final_output for r in result]

    async def pick(self, query):
        result = await Runner.run(self.agent_01, query)
        return result.final_output

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
    
    agent_01        = Agent(instructions   = prompts['agent_01']                    ,
                            model          = params ['model'   ]                    ,  
                            model_settings = ModelSettings(tool_choice = "required"),
                            name           = "Sales Picker"                         ,
                            tools          = [send_email]                            )

    agent_02        = Agent(instructions   = prompts['agent_02']                    ,
                            model          = params ['model'   ]                    ,
                            name           = "Professional Sales Agent"              )

    agent_03        = Agent(instructions   = prompts['agent_03']                    ,
                            model          = params ['model'   ]                    ,
                            name           = "Humorous Sales Agent"                  )

    agent_04        = Agent(instructions   = prompts['agent_04']                    ,
                            model          = params ['model'   ]                    ,
                            name           = "Executive Sales Agent"                 )

    manager         = Manager(params   = params  ,
                              agent_01 = agent_01,
                              agent_02 = agent_02,
                              agent_03 = agent_03,
                              agent_04 = agent_04 )

    with gradio.Blocks() as UI:
        textbox_query = gradio.Textbox (label = "What topic would you like to research?")
        button_run    = gradio.Button  ("Run"     , variant = "primary")
        button_end    = gradio.Button  ("End Chat", variant = "stop"   )
        report        = gradio.Markdown(label = "Report")

        button_run.click(manager.chat_run, inputs = textbox_query, outputs = report)
        button_end.click(fn = manager.chat_close)
    UI.launch()
    
    print('Finished!')


if __name__ == "__main__":
    main()

