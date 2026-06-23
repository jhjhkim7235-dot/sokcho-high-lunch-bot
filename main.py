import os
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client
from pytz import timezone
import time

def get_lunch_menu(today_str):
    """나이스 API에서 급식 정보를 안전하게 가져오는 함수 (오류 방지 대책 적용)"""
    # 속초고등학교 정보 세팅
    URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    PARAMS = {
        "KEY": "YOUR_NEIS_API_KEY", # 만약 개인 API 키가 있다면 입력, 없다면 공공키 사용 가능
        "Type": "json",
        "pIndex": "1",
        "pSize": "100",
        "ATPT_OFCDC_SC_CODE": "K10", # 강원도교육청
        "SD_SCHUL_CODE": "7831023",  # 속초고등학교
        "MLSV_YMD": today_str
    }
    
    try:
        response = requests.get(URL, params=PARAMS, timeout=10)
        data = response.json()
        
        if "mealServiceDietInfo" in data:
            row = data["mealServiceDietInfo"][1]["row"][0]
            # 나이스 특유의 불필요한 글자들(<br/>, 숫자, 특수문자)을 깨끗하게 청소
            raw_menu = row["DDISH_NM"]
            clean_menu = raw_menu.replace("<br/>", "\n")
            # 불필요한 알레르기 숫자 제거 (예: 1.2.3. 등)
            import re
            clean_menu = re.sub(r'[0-9\.\*]', '', clean_menu)
            
            menu_list = [line.strip() for line in clean_menu.split("\n") if line.strip()]
            calories = row["CAL_INFO"]
            return menu_list, calories
        else:
            print(f"[{today_str}] 나이스 서버에 급식 데이터가 아직 등록되지 않았거나 점검 중입니다.")
            return None, None
    except Exception as e:
        print(f"나이스 서버 연결 중 에러 발생: {e}")
        return None, None

def create_story_image(today_str, menu_list, calories):
    """인스타 스토리용 이미지 생성 (1080x1920)"""
    width, height = 1080, 1920
    # 연한 파스텔 블루 배경
    image = Image.new("RGB", (width, height), "#F0F4F8")
    draw = ImageDraw.Draw(image)
    
    # 폰트 로드
    try:
        font_title = ImageFont.truetype("fonts/NanumGothicBold.ttf", 65)
        font_date = ImageFont.truetype("fonts/NanumGothicBold.ttf", 45)
        font_menu = ImageFont.truetype("fonts/NanumGothicBold.ttf", 52)
        font_cal = ImageFont.truetype("fonts/NanumGothicBold.ttf", 40)
    except:
        font_title = font_date = font_menu = font_cal = ImageFont.load_default()

    # 중앙 화이트 카드 그리기
    draw.rounded_rectangle([100, 200, 980, 1650], radius=40, fill="white", outline="#E2E8F0", width=3)
    
    # 타이틀 및 날짜 작성
    draw.text((540, 320), "속초고등학교", fill="#1E3A8A", font=font_title, anchor="mm")
    draw.text((540, 420), "오늘의 급식 🍚", fill="#2563EB", font=font_title, anchor="mm")
    
    formatted_date = f"{today_str[0:4]}년 {today_str[4:6]}월 {today_str[6:8]}일"
    draw.text((540, 520), formatted_date, fill="#64748B", font=font_date, anchor="mm")
    
    # 구분선
    draw.line([200, 600, 880, 600], fill="#CBD5E1", width=2)
    
    # 메뉴 리스트 작성 (중앙 정렬)
    start_y = 680
    for menu in menu_list:
        draw.text((540, start_y), menu, fill="#1E293B", font=font_menu, anchor="mm")
        start_y += 90
        
    # 구분선 2
    draw.line([200, 1400, 880, 1400], fill="#CBD5E1", width=2)
    draw.text((540, 1480), f"총 칼로리: {calories}", fill="#475569", font=font_cal, anchor="mm")
    
    # 워터마크
    draw.text((540, 1780), "@sokcho_high_lunch_bot", fill="#94A3B8", font=font_date, anchor="mm")
    
    image.save("lunch_story.jpg", "JPEG", quality=95)
    print("스토리 이미지 생성 완료 (lunch_story.jpg)")

def upload_to_instagram():
    """인스타그램 업로드 (해외 IP 차단 우회 및 재시도 로직 추가)"""
    username = os.environ.get("INSTA_USERNAME")
    password = os.environ.get("INSTA_PASSWORD")
    
    cl = Client()
    
    # 보안 차단 방지를 위해 랜덤한 기기 값 설정
    cl.set_device_settings({
        "app_version": "269.0.0.18.230",
        "android_version": "29",
        "android_release": "10",
        "dpi": "480dpi",
        "resolution": "1080x2280",
        "manufacturer": "Samsung",
        "model": "SM-G977N",
        "cpu": "exynos9820"
    })

    # 로그인 및 업로드 실패 시 최대 3번까지 시간 간격을 두고 재시도합니다.
    for attempt in range(1, 4):
        try:
            print(f"[{attempt}차 시도] 인스타그램 로그인 중...")
            cl.login(username, password)
            
            print("인스타그램 스토리 업로드 중...")
            cl.album_upload_to_story(["lunch_story.jpg"])
            print("🎉 인스타그램 스토리 업로드 성공 완료!")
            return # 성공하면 함수 종료
            
        except Exception as e:
            print(f"[{attempt}차 시도] 에러 발생: {e}")
            if attempt < 3:
                print("보안 걸쇠 회피를 위해 30초 대기 후 재시도합니다...")
                time.sleep(30)
            else:
                print("⚠️ 3회 재시도 모두 실패했습니다. 인스타 계정 설정을 확인해 주세요.")

def main():
    tz_kst = timezone('Asia/Seoul')
    today = datetime.datetime.now(tz_kst)
    today_str = today.strftime("%Y%m%d")
    print(f"조회 실행 날짜: {today_str}")
    
    menu_list, calories = get_lunch_menu(today_str)
    if menu_list:
        create_story_image(today_str, menu_list, calories)
        upload_to_instagram()
    else:
        print("조건이 맞지 않아 스토리를 올리지 않고 종료합니다.")

if __name__ == "__main__":
    main()
