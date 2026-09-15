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
from   dotenv   import load_dotenv
from   agents   import Agent, Runner, trace, function_tool, ModelSettings, WebSearchTool
from   pydantic import BaseModel, Field

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

class WebSearchItem(BaseModel):
    reason  : str = Field(description = "Your reasoning for why this search is important to the query.")
    query   : str = Field(description = "The search term to use for the web search."                   )

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]  = Field(description = "A list of web searches to perform to best answer the query.")

class ReportData(BaseModel):
    short_summary      : str       = Field(description = "A short 2-3 sentence summary of the findings.")
    markdown_report    : str       = Field(description = "The final report"                             )
    follow_up_questions: list[str] = Field(description = "Suggested topics to research further"         )

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

    class Manager():

        async def run(self, query):
            with trace(params['prjdescription']):
                yield "Starting research ..."
                plan    = await self.search_plan   (query)
                yield "Searches planned  ..."
                results = await self.search_perform(plan )
                yield "Writing report    ..."
                report  = await self.report_write  (query,results)
                yield "Sending email     ..."
                _       = await self.send_email    (report)
                yield report.markdown_report

        async def search(self, item):
            input_message = f"Search term: {item.query}\nReason for searching: {item.reason}"
            x             = await Runner.run(agent_01, input_message)
            return x.final_output

        async def search_plan(self, query):
            x = await Runner.run(agent_02, f"Query: {query}")
            return x.final_output

        async def search_perform(self, plan):
            tasks = [self.search(item) for item in plan.searches]
            x     = await asyncio.gather(*tasks)
            return x

        async def report_write(self, query, results):
            input_message = f"Original query: {query}\nSummarized search results: {results}"
            x             = await Runner.run(agent_03, input_message)
            return x.final_output
    
        async def send_email(self, report):
            x = await Runner.run(agent_04, report.markdown_report)
            return None

    async def run(query):
        async for status_update in Manager().run(query):
            yield status_update

    params, prompts   = initialize_run()
    load_dotenv()
    
    agent_01          = Agent(instructions   = prompts['agent_01']                    ,
                              model          = params ['model'   ]                    ,  
                              model_settings = ModelSettings(tool_choice = "required"),
                              name           = "Searcher"                             ,
                              tools          = [WebSearchTool()]                       )

    instructions      = prompts['agent_02'].format(x = params['HOW_MANY_SEARCHES'])
    agent_02          = Agent(instructions   = instructions    ,
                              model          = params ['model'],
                              name           = "Planner"       ,
                              output_type    = WebSearchPlan    )
    
    agent_03          = Agent(instructions   = prompts['agent_03'],
                              model          = params ['model'   ],
                              name           = "Writer"           ,
                              output_type    = ReportData          )
    
    agent_04          = Agent(instructions   = prompts['agent_04']                    ,
                              model          = params ['model'   ]                    ,  
                              model_settings = ModelSettings(tool_choice = "required"),
                              name           = "Email"                                ,
                              tools          = [send_email]                            )
    
    with gradio.Blocks() as UI:
        textbox_query = gradio.Textbox (label = "What topic would you like to research?")
        button_run    = gradio.Button  ("Run"     , variant = "primary")
        button_end    = gradio.Button  ("End Chat", variant = "stop"   )
        report        = gradio.Markdown(label = "Report")

        button_run.click    (run, inputs = textbox_query, outputs = report)
        textbox_query.submit(run, inputs = textbox_query, outputs = report)
        button_end.click(fn = close_chat)
    UI.launch()
        
    print('Finished!')

if __name__ == "__main__":
    main()

