#!/usr/bin/env python3
import requests
import json

# 백엔드 서버 URL
BASE_URL = "http://localhost:8000"

def test_inline_initial():
    """INLINE initial 요청 테스트"""
    
    # 1. 채팅방 생성
    print("1. 채팅방 생성...")
    create_response = requests.post(f"{BASE_URL}/chatrooms")
    if create_response.status_code == 200:
        chatroom_data = create_response.json()
        chatroom_id = chatroom_data['id']
        print(f"✅ 채팅방 생성 성공: {chatroom_id}")
    else:
        print(f"❌ 채팅방 생성 실패: {create_response.status_code}")
        return
    
    # 2. INLINE initial 메시지 전송
    print("\n2. INLINE initial 메시지 전송...")
    chat_data = {
        "choice": "inline",
        "message": "initial trend 보여줘",
        "chatroom_id": chatroom_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json=chat_data, stream=True)
        
        if response.status_code == 200:
            print("✅ 요청 성공, 응답 스트림 읽는 중...")
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # "data: " 제거
                        try:
                            data = json.loads(data_str)
                            
                            # 진행 메시지 출력
                            if 'progress_message' in data:
                                print(f"📝 진행: {data['progress_message']}")
                            
                            # 최종 응답 확인
                            elif 'response' in data:
                                response_data = data['response']
                                print(f"\n🎯 최종 응답:")
                                print(f"   - result: {response_data.get('result')}")
                                print(f"   - criteria: {response_data.get('criteria')}")
                                print(f"   - real_data 타입: {type(response_data.get('real_data'))}")
                                print(f"   - success_message: {response_data.get('success_message')}")
                                
                                # real_data가 JSON 문자열인지 확인
                                real_data = response_data.get('real_data')
                                if isinstance(real_data, str):
                                    try:
                                        parsed_data = json.loads(real_data)
                                        print(f"   - real_data 파싱됨: {len(parsed_data)}개 레코드")
                                        print(f"   - 첫 번째 레코드: {parsed_data[0] if parsed_data else 'None'}")
                                    except:
                                        print(f"   - real_data JSON 파싱 실패")
                                else:
                                    print(f"   - real_data가 문자열이 아님")
                                
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON 파싱 오류: {e}")
                            print(f"   원본 데이터: {data_str[:200]}...")
                            
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print(f"응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 요청 중 오류: {e}")

if __name__ == "__main__":
    test_inline_initial()
