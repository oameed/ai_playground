###############################################
### AI Playground                           ###
### Agentic AI                              ###
### OpenAI Agents SDK                       ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import asyncio
from   dotenv                      import load_dotenv
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

def wFILE(string, filename):
    with open(filename, "a", encoding = "utf-8") as fobj:
        fobj.write(string + "\n")

@tool
def send_email(email: str) -> str:
    '''
    Send out an email with the given subject and body to all sales prospects
    Args:
        email: Both the subject and the body of the email are concatenated in this variable
    '''
    filename = os.path.join(os.environ.get("MY_WORKDIR"), "output" + ".txt")
    wFILE(email, filename)
    return "OK"

@wrap_tool_call
async def log_tool_calls(request, handler):
    call = request.tool_call
    print(f"[middleware] calling {call['name']} with {call['args']}")
    return await handler(request)


class Manager():
    def __init__(self, params, agent_01, agent_02, agent_03, agent_04):
        self.params   = params
        self.agent_01 = agent_01
        self.agent_02 = agent_02
        self.agent_03 = agent_03
        self.agent_04 = agent_04

    async def orchestrate(self, query):
        message = {"messages": [{"role": "user", "content": query}]}
        emails  = await self.write(message)
        emails  = "Cold sales emails:\n\n" + "\n\nEmail:\n\n".join(emails)
        message = {"messages": [{"role": "user", "content": emails}]}
        _       = await self.pick(message)

    async def write(self, query):
        result = await asyncio.gather(self.agent_02.ainvoke(query),
                                      self.agent_03.ainvoke(query),
                                      self.agent_04.ainvoke(query) )
        return [x['messages'][-1].content for x in result]

    async def pick(self, query):
        result = await self.agent_01.ainvoke(query)
        return None
        

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
    
    agent_01        = create_agent(system_prompt = prompts['agent_01'],
                                   model         = params ['model'   ],
                                   tools         = tools              ,
                                   middleware    = middleware          )

    agent_02        = create_agent(system_prompt = prompts['agent_02'],
                                   model         = params ['model'   ] )
    
    agent_03        = create_agent(system_prompt = prompts['agent_03'],
                                   model         = params ['model'   ] )

    agent_04        = create_agent(system_prompt = prompts['agent_04'],
                                   model         = params ['model'   ] )

    manager         = Manager(params   = params  ,
                              agent_01 = agent_01,
                              agent_02 = agent_02,
                              agent_03 = agent_03,
                              agent_04 = agent_04 )

    asyncio.run(manager.orchestrate(prompts['task'])) 
    
    print('Finished!')

if __name__ == "__main__":
    main()

