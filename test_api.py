import requests
import json
import time

# API 기본 URL
BASE_URL = "http://localhost:8005"

def test_health():
    """헬스 체크 테스트"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ Health check passed!\n")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False

def test_chat_streaming(message, choice="pcm", chatroom_id=1):
    """스트리밍 채팅 API 테스트"""
    print(f"🔍 Testing chat endpoint with message: '{message}'")
    
    url = f"{BASE_URL}/api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "choice": choice,
        "message": message,
        "chatroom_id": chatroom_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Streaming response:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 'data: ' 제거
                        try:
                            data_json = json.loads(data_str)
                            print(f"   {json.dumps(data_json, indent=2, ensure_ascii=False)}")
                        except json.JSONDecodeError:
                            print(f"   Raw data: {data_str}")
            print("✅ Chat test completed!\n")
            return True
        else:
            print(f"❌ Chat test failed: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"❌ Chat test failed: {e}\n")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Starting PCM Chat API Tests...\n")
    
    # 헬스 체크
    if not test_health():
        print("❌ Server is not running. Please start the server first.")
        return
    
    # 다양한 메시지로 테스트
    test_messages = [
        "pcm trend",
        "pcm commonality", 
        "show me PCM data",
        "commonality analysis"
    ]
    
    for message in test_messages:
        test_chat_streaming(message)
        time.sleep(1)  # 요청 간 간격
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main() 