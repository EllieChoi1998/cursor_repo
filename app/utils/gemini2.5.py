token = 'AIzaSyD9YdnbJfXglc3zMD6EjVD_U2cDaGBlEkI'
from google import genai
import json

client = genai.Client(api_key=token)
# user_prompt = "닭볶음탕을 해먹고 싶어. 근데 일단은 레시피를 찾아서 재료를 목록으로 만들어줘."
user_prompt = "안녕."
modules = {
    "search_receipe": "레시피를 검색합니다. 검색 할 키워드를 사용자 요청에서 추출합니다.",
    "list_ingredients": "레시피의 재료 목록을 작성합니다.",
    "shop_ingredients": "필요한 재료를 쇼핑합니다. 쇼핑 할 재료를 재료 목록에서 추출합니다."
}

receipe = '''
닭도리탕은 형태상 조림에 가까운 한국의 요리이다. 토막 낸 닭고기를 고추장, 고춧가루, 간장, 파, 마늘 등의 양념으로 볶거나 약간의 국물을 남기고 졸여 만든다. 부재료로는 주로 큼직하게 썬 감자, 양파, 당근 등이 같이 들어간다.
'''

# 1단계: 모듈 선택
pipeline_instructions = f'''
당신은 한국 요리 전문가입니다.

사용자 요청: "{user_prompt}"


사용 가능한 모듈:
- search_receipe: 레시피를 검색합니다
- list_ingredients: 레시피의 재료 목록을 작성합니다
- shop_ingredients: 필요한 재료를 쇼핑합니다

사용자 요청을 분석해서 어떤 모듈을 실행해야 하는지 판단하세요.
여러개의 모듈이 연속적으로 호출해야한다면, 순서대로 작성하세요.
리스트 형식으로 작성하세요. 
만약 선택할 모듈이 한개도 존재하지 않는다면, 빈 리스트를 작성하세요.

'''


response = client.models.generate_content(
    model="gemini-2.5-flash", 
    contents=pipeline_instructions
)

selected_module = response.text.strip()
print(f"선택된 모듈:\n{selected_module}\n========")

if len(eval(selected_module)) == 0:
    no_module_prompt = f'''
    유저 프롬프트 : {user_prompt}
    사용 가능한 모듈 : {json.dumps(modules, ensure_ascii=False, indent=2)}

    유저가 선택할 모듈이 없는 프롬프트를 입력 하였습니다.
    유저 프롬프트에 대해 친절하게 대답을 하면서도,
    당신이 제공 가능한 모듈들에 대해 설명하여
    올바른 방법이로 이 채팅을 사용 할 수 있도록 유저를 가이드하는 프롬프트를 작성하세요.
    Markdown 형식의 프롬프트는 사용하지 말고, 일반 텍스트 형식으로 작성하세요.
    '''
    no_module_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=no_module_prompt
    )
    print("\n=== 모듈 없을 시 프롬프트 ===")
    print(no_module_response.text)
    exit()
# 2단계: 모듈 실행
if selected_module == "list_ingredients":
    ingredient_prompt = f'''
    다음 레시피의 재료를 정리해주세요:
    {receipe}
    
    형식:
    - 재료명 (수량)
    '''
    
    result = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=ingredient_prompt
    )
    print("\n=== 재료 목록 ===")
    print(result.text)

elif selected_module == "search_receipe":
    print("레시피 검색 모듈 (크롤링 봇 필요)")
    
elif selected_module == "shop_ingredients":
    print("재료 쇼핑 모듈 (크롤링 봇 필요)")