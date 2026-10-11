###############################################
### AI Playground                           ###
### Agentic AI                              ###
### OpenAI Agents SDK                       ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import asyncio
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
    def __init__(self, params, agent):
        self.params = params
        self.agent  = agent

    async def orchestrate(self,query):
        with trace(self.params['prjdescription']):
            _ = await Runner.run(self.agent, query)

    def visualize_graph(self):
        from agents.extensions.visualization import draw_graph
        filename = os.path.join(os.environ.get("MY_WORKDIR"),"graph")
        draw_graph(self.agent, filename = filename)

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
    
    agent_02        = Agent(instructions   = prompts['agent_02']       ,
                            model          = params ['model'   ]       ,
                            name           = "Professional Sales Agent" )

    agent_03        = Agent(instructions   = prompts['agent_03']       ,
                            model          = params ['model'   ]       ,
                            name           = "Humorous Sales Agent"     )

    agent_04        = Agent(instructions   = prompts['agent_04']       ,
                            model          = params ['model'   ]       ,
                            name           = "Executive Sales Agent"    )

    agent_02_tool   = agent_02.as_tool(tool_description = prompts['tool_description'],
                                       tool_name        = "sales_email_writer_1"      )

    agent_03_tool   = agent_03.as_tool(tool_description = prompts['tool_description'],
                                       tool_name        = "sales_email_writer_2"      )

    agent_04_tool   = agent_04.as_tool(tool_description = prompts['tool_description'],
                                       tool_name        = "sales_email_writer_3"      )

    tools           = [send_email, agent_02_tool, agent_03_tool, agent_04_tool]

    agent_01        = Agent(instructions   = prompts['agent_01_OBL']                ,
                            model          = params ['model'   ]                    ,  
                            model_settings = ModelSettings(tool_choice = "required"),
                            name           = "Sales Manager"                        ,
                            tools          = tools                                   )

    manager         = Manager(params = params, agent = agent_01)
    manager.visualize_graph()
    
    asyncio.run(manager.orchestrate(prompts['task_OBL'])) 
        
    print('Finished!')


if __name__ == "__main__":
    main()

