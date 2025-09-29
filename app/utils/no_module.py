import time
from google import genai
from google.genai.errors import ServerError
import json
import re

token = 'AIzaSyD9YdnbJfXglc3zMD6EjVD_U2cDaGBlEkI'
client = genai.Client(api_key=token)

def safe_generate(prompt, max_retries=3):
    """재시도 로직이 있는 안전한 API 호출"""
    for i in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemma-3-27b-it",
                contents=prompt
            )
            return response.text.strip()
        except ServerError as e:
            if i < max_retries - 1:
                wait_time = (i + 1) * 3
                print(f"⏳ {wait_time}초 후 재시도... ({i+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"❌ API 호출 실패: {e}")
                return None
        except Exception as e:
            print(f"❌ 예상치 못한 에러: {e}")
            return None

# 유저 프롬프트
user_prompt = "A1234567890"  # 테스트용

modules = {
    "lot_start": '''
    Module Name: `lot_start`
    In order to call this module, a current user prompt should include the word `trend`.
    Also, there should be neither tech name (length of 10 characters or more) nor device name (length of exactly 4 characters) and para name (length of between 5 to 8 characters) should be in the current user prompt.
    Otherwise, never call this module. 
    ''',
    "commonality_start": '''
    Module Name: `commonality_start`
    In order to call this module, a current user prompt should include the word `commonality`.
    Also, there should be neither tech name (length of 10 characters or more) nor device name (length of exactly 4 characters) and para name (length of between 5 to 8 characters) should be in the current user prompt.
    Otherwise, never call this module.
    ''',
    "sameness_start": '''
    Module Name: `sameness_start`
    In order to call this module, a current user prompt should include the word `sameness`.
    Also, there should be neither tech name (length of 10 characters or more) nor device name (length of exactly 4 characters) and para name (length of between 5 to 8 characters) should be in the current user prompt.
    '''
}

# 1단계: 모듈 선택
module_selection_prompt = f'''
You are a module selector for a semiconductor data analysis system.

User Prompt: "{user_prompt}"

Available Modules:
{json.dumps(modules, ensure_ascii=False, indent=2)}

Analyze the user prompt and determine which module should be called based on the module descriptions.
Return ONLY ONE of the following module names or "no_module":
- lot_start
- commonality_start
- sameness_start
- no_module (if no module matches)

Return ONLY the module name, nothing else.
'''

selected_module = safe_generate(module_selection_prompt)

if not selected_module:
    print("❌ 모듈 선택 실패 (API 에러)")
    exit()

print(f"✅ 선택된 모듈: {selected_module}")

# 2단계: 모듈별 처리
if selected_module == "no_module":
    no_module_prompt = f'''
    유저 프롬프트: {user_prompt}
    사용 가능한 모듈: {json.dumps(modules, ensure_ascii=False, indent=2)}

    유저가 선택할 모듈이 없는 프롬프트를 입력하였습니다.
    유저 프롬프트에 대해 친절하게 대답을 하면서도,
    당신이 제공 가능한 모듈들에 대해 설명하여
    올바른 방법으로 이 채팅을 사용할 수 있도록 유저를 가이드하는 프롬프트를 작성하세요.
    Markdown 형식의 프롬프트는 사용하지 말고, 일반 텍스트 형식으로 작성하세요.
    모듈 이름이나 키워드를 제외한 설명은 한국어로 작성하세요.
    '''
    
    no_module_response = safe_generate(no_module_prompt)
    if no_module_response:
        print("\n=== 모듈 없을 시 응답 ===")
        print(no_module_response)

elif selected_module == "lot_start":
    print("\n=== LOT START 모듈 실행 ===")
    print("트렌드 분석을 시작합니다...")
    # 여기에 실제 lot_start 로직 추가
    
elif selected_module == "commonality_start":
    print("\n=== COMMONALITY START 모듈 실행 ===")
    print("공통성 분석을 시작합니다...")
    # 여기에 실제 commonality_start 로직 추가
    
elif selected_module == "sameness_start":
    print("\n=== SAMENESS START 모듈 실행 ===")
    print("동일성 분석을 시작합니다...")
    # 여기에 실제 sameness_start 로직 추가
    
else:
    print(f"⚠️ 알 수 없는 모듈: {selected_module}")