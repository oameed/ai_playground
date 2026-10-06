###############################################
### AI Playground                           ###
### Agentic AI                              ###
### LangChain                               ###
### by: OAMEED NOAKOASTEEN                  ###
############################################### 

import os
import gradio
import signal 
from   dotenv                  import load_dotenv
from   langchain_openai        import ChatOpenAI
from   langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from   langchain_core.tools    import tool
from   pydantic                import BaseModel, Field

import pdb

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
    params, prompts   = initialize_run()
    load_dotenv()
    
    agent             = ChatOpenAI(model = params['model'])
    
    messages          = [SystemMessage(prompts['agent']),
                         HumanMessage (prompts['task'] ) ]
    
    pdb.set_trace()
    
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

