###############################################
### AI Playground                           ###
### Agentic AI                              ###
### LangChain                               ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import asyncio
import gradio
import signal 
from   dotenv                      import load_dotenv
from   pydantic                    import BaseModel, Field
from   langchain_core.tools        import tool
from   langchain.agents            import create_agent
from   langgraph.checkpoint.memory import MemorySaver
from   langchain.agents.middleware import wrap_tool_call
from   langchain_tavily            import TavilySearch

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

class WebSearchItem(BaseModel):
    reason: str = Field(description = "Your reasoning for why this search is important to the query.")
    query : str = Field(description = "The search term to use for the web search."                   )

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]  = Field(description = "A list of web searches to perform to best answer the query.")

class ReportData(BaseModel):
    short_summary      : str       = Field(description = "A short 2-3 sentence summary of the findings.")
    markdown_report    : str       = Field(description = "The final report"                             )
    follow_up_questions: list[str] = Field(description = "Suggested topics to research further"         )

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
        yield "Planning searches   ..."            #
        plan    = await self.search_plan   (query) #
        yield "Performing Searches ..."            #
        results = await self.search_perform(plan ) #
        yield "Writing report      ..."
        report  = await self.report_write  (query,results)
        yield "Sending email       ..."
        _       = await self.send_email    (report)
        yield report.markdown_report

    async def search(self, item):
        query = f"Search term: {item.query}\nReason for searching: {item.reason}"
        query = {"messages": [{"role": "user", "content": query}]}
        x     = await self.agent_01.ainvoke(query)
        return x['messages'][-1].content

    async def search_plan(self, query):
        query = {"messages": [{"role": "user", "content": f"Query: {query}"}]}
        x     = await self.agent_02.ainvoke(query)
        return x['structured_response']

    async def search_perform(self, plan):
        tasks = [self.search(item) for item in plan.searches]
        x     = await asyncio.gather(*tasks)
        return x

    async def report_write(self, query, results):
        input_message = f"Original query: {query}\nSummarized search results: {results}"
        input_message = {"messages": [{"role": "user", "content": input_message}]}
        x             = await self.agent_03.ainvoke(input_message)
        return x['structured_response']
    
    async def send_email(self, report):
        input_message = {"messages": [{"role": "user", "content": report.markdown_report}]}
        x             = await self.agent_04.ainvoke(input_message)
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
    
    middleware      = [log_tool_calls]

    agent_01        = create_agent(system_prompt   = prompts['agent_01'],
                                   model           = params ['model'   ],
                                   tools           = [TavilySearch()]   ,
                                   middleware      = middleware          )
    
    system_prompt   = prompts['agent_02'].format(x = params['HOW_MANY_SEARCHES'])
    agent_02        = create_agent(system_prompt   = system_prompt  ,
                                   model           = params['model'],
                                   response_format = WebSearchPlan   )

    agent_03        = create_agent(system_prompt   = prompts['agent_03'],
                                   model           = params ['model'   ],
                                   response_format = ReportData          )

    agent_04        = create_agent(system_prompt   = prompts['agent_04'],
                                   model           = params ['model'   ],
                                   tools           = [send_email]       ,
                                   middleware      = middleware          )
    
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

