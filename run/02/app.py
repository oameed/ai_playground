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

    class Manager():

        async def run  (self, query):
            with trace(params['prjdescription']):
                emails = await self.write(query)
                emails = "Cold sales emails:\n\n" + "\n\nEmail:\n\n".join(emails)
                _      = await self.pick(emails)

        async def write(self, query):
            result = await asyncio.gather(Runner.run(agent_02, query),
                                          Runner.run(agent_03, query),
                                          Runner.run(agent_04, query) )
            return [r.final_output for r in result]

        async def pick(self, query):
            result = await Runner.run(agent_01, query)
            return None        

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

    asyncio.run(Manager().run(prompts['task'])) 
    
    print('Finished!')


if __name__ == "__main__":
    main()

