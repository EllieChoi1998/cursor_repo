from utils.call_llm import safe_generate, client

def determine_context(user_prompt: str, current_context: str):
    context_options = {
        "FIND_MODULE": "Find the module to use based on the user prompt and the current context.",
        "EDIT_PARAMETER": "Edit the parameter of the current context.",
        "RUN_MODULE": "Run the module of the current context."
    }
    context_determination_prompt = f'''
    You are a helpful assistant that determines the context of a user's message.
    You will be given a user prompt and a list of context options.
    You need to determine the context of the user's message from the list of context options.
    User prompt: {user_prompt}
    Current Context: {current_context}
    Context Options: {context_options}
    Determine the context of the user's message from the list of context options.
    Return only the single context name.
    Do not explain or include any other code or json.
    Response:
    '''

    response = safe_generate(context_determination_prompt)
    
    if len(response) > 3:
        return response
    return "FIND_MODULE"

def edit_parameter(user_prompt: str, current_context: str):
    edit_parameter_prompt = f'''
    You are a helpful assistant that edits the parameter of the current context.
    You will be given a user prompt and a list of context options.
    You need to edit the parameter of the current context from the list of context options.
    User prompt: {user_prompt}
    Current Context: {current_context}
    Edit the parameter of the current context from the list of context options.
    Return only JSON format of the edited parameter.
    Do not delete existing parameter key.
    Do not create new parameter key.
    Do not explain or include any other code.
    Edited Parameters:
    '''

    response = safe_generate(edit_parameter_prompt)
    edited_parameter = response.replace("```json", "").replace("```", "")
    try:
        edited_parameter = json.loads(response)
        return edited_parameter
    except Exception as e:
        pass

    try:
        edited_parameter = eval(response)
        return edited_parameter    
    except Exception as e:
        print(f"Error editing parameter: {e}")
        print(f"Response: {edited_parameter}")
        return None

def find_module(user_prompt: str, modules: dict):
    find_module_prompt = f'''
    You are a helpful assistant that finds the module to use based on the user prompt and the current context.
    You will be given a user prompt and a list of modules.
    You need to find the module to use based on the user prompt.
    User prompt: {user_prompt}
    Modules: {modules}
    Find the module to use based on the user prompt.
    Return only the single module name.
    Do not explain or include any other code.
    Response:
    '''

    response = safe_generate(find_module_prompt)
    if len(response) > 3:
        return response
    return None

def find_parameter(user_prompt: str, module_instruction: str):
    find_parameter_prompt = f'''
    You are a helpful assistant that finds the parameter to use based on the user prompt and the module instruction.
    You will be given a user prompt and a module instruction.
    You need to find the parameter to use based on the user prompt.
    User prompt: {user_prompt}
    Module Instruction: {module_instruction}
    Find the parameter to use based on the user prompt.
    Return only JSON format of the parameter.
    Do not explain or include any other code.
    Response:
    '''
    response = safe_generate(edit_parameter_prompt)
    found_parameter = response.replace("```json", "").replace("```", "")
    try:
        found_parameter = json.loads(response)
        return found_parameter
    except Exception as e:
        pass

    try:
        found_parameter = eval(response)
        return found_parameter    
    except Exception as e:
        print(f"Error finding parameter: {e}")
        print(f"Response: {found_parameter}")
        return None

def generate_no_module_found_text(user_prompt: str, modules: dict):
    no_module_found_prompt = f'''
    유저 프롬프트: {user_prompt}
    사용 가능한 모듈: {json.dumps(modules, ensure_ascii=False, indent=2)}

    유저가 선택할 모듈이 없는 프롬프트를 입력하였습니다.
    유저 프롬프트에 대해 친절하게 대답을 하면서도,
    당신이 제공 가능한 모듈들에 대해 설명하여
    올바른 방법으로 이 채팅을 사용할 수 있도록 유저를 가이드하는 프롬프트를 작성하세요.
    Markdown 형식의 프롬프트는 사용하지 말고, 일반 텍스트 형식으로 작성하세요.
    모듈 이름이나 키워드를 제외한 설명은 한국어로 작성하세요.
    '''
    response = safe_generate(no_module_found_prompt)
    return response