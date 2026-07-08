import os
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client
import pytz
import time
import re

def get_lunch_menu(today_str):
    """NEIS_KEY 인증키를 사용하여 속초고 급식을 가져오는 함수"""
    URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    
    # GitHub Secrets에서 인증키를 불러옵니다.
    neis_key = os.environ.get("NEIS_KEY")
    
    if not neis_key:
        print("❌ 에러: 깃허브 Settings에 NEIS_KEY가 등록되지 않았습니다.")
        return None, None

    PARAMS = {
        "KEY": neis_key,
        "Type": "json",
        "pIndex": "1",
        "pSize": "10",
        "ATPT_OFCDC_SC_CODE": "J10",   # 강원특별자치도교육청
        "SD_SCHUL_CODE": "7831023",    # 속초고등학교
        "MLSV_YMD": today_str          # 조회 날짜 (점심 코드를 빼서 장부를 통째로 들고옵니다!)
    }
    
    try:
        response = requests.get(URL, params=PARAMS, timeout=15)
        data = response.json()
        
        if "mealServiceDietInfo" in data:
            # 가져온 식사 데이터 목록 전체를 확인
            meal_entries = data["mealServiceDietInfo"][1]["row"]
            
            # 기본적으로 첫 번째 데이터를 선택하되, 여러 개면 점심(중식) 데이터를 우선 탐색
            row = meal_entries[0]
            for entry in meal_entries:
                if entry.get("MMEAL_SC_NM") == "중식" or entry.get("MMEAL_SC_CODE") == "2":
                    row = entry
                    break
            
            raw_menu = row["DDISH_NM"]
            
            # 알레르기 숫자 및 특수문자 제거
            clean_menu = raw_menu.replace("<br/>", "\n")
            clean_menu = re.sub(r'[0-9\.\*]', '', clean_menu)
            
            menu_list = [line.strip() for line in clean_menu.split("\n") if line.strip()]
            calories = row.get("CAL_INFO", "정보 없음")
            return menu_list, calories
        else:
            print(f"❌ [나이스 응답 에러]: {data}")
            return None, None
            
    except Exception as e:
        print(f"❌ 시스템 통신 치명적 에러: {e}")
        return None, None

def create_story_image(today_str, menu_list, calories):
    """인스타 스토리용 카드 이미지 생성"""
    width, height = 1080, 1920
    image = Image.new("RGB", (width, height), "#F0F4F8")
    draw = ImageDraw.Draw(image)
    
    try:
        font_title = ImageFont.truetype("fonts/NanumGothicBold.ttf", 65)
        font_date = ImageFont.truetype("fonts/NanumGothicBold.ttf", 45)
        font_menu = ImageFont.truetype("fonts/NanumGothicBold.ttf", 52)
        font_cal = ImageFont.truetype("fonts/NanumGothicBold.ttf", 40)
    except Exception:
        font_title = font_date = font_menu = font_cal = ImageFont.load_default()

    draw.rounded_rectangle([100, 200, 980, 1650], radius=40, fill="white", outline="#E2E8F0", width=3)
    
    draw.text((540, 320), "속초고등학교", fill="#1E3A8A", font=font_title, anchor="mm")
    draw.text((540, 420), "오늘의 점심 🍚", fill="#2563EB", font=font_title, anchor="mm")
    
    formatted_date = f"{today_str[0:4]}년 {today_str[4:6]}월 {today_str[6:8]}일"
    draw.text((540, 520), formatted_date, fill="#64748B", font=font_date, anchor="mm")
    
    draw.line([200, 600, 880, 600], fill="#CBD5E1", width=2)
    
    start_y = 680
    for menu in menu_list:
        draw.text((540, start_y), menu, fill="#1E293B", font=font_menu, anchor="mm")
        start_y += 90
        
    draw.line([200, 1400, 880, 1400], fill="#CBD5E1", width=2)
    draw.text((540, 1480), f"총 칼로리: {calories}", fill="#475569", font=font_cal, anchor="mm")
    draw.text((540, 1780), "@sokcho_high_lunch_bot", fill="#94A3B8", font=font_date, anchor="mm")
    
    image.save("lunch_story.jpg", "JPEG", quality=95)
    print("✨ 스토리 이미지 제작 완료")

def upload_to_instagram():
    """인스타그램 스토리 자동 업로드"""
    username = os.environ.get("INSTA_USERNAME")
    password = os.environ.get("INSTA_PASSWORD")
    
    cl = Client()
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

    for attempt in range(1, 4):
        try:
            print(f"🔑 [{attempt}차 시도] 인스타그램 로그인 중...")
            cl.login(username, password)
            print("📸 인스타그램 스토리 업로드 중...")
            cl.album_upload_to_story(["lunch_story.jpg"])
            print("🚀 [성공] 인스타그램 스토리가 무사히 게시되었습니다!")
            return
        except Exception as e:
            print(f"⚠️ [{attempt}차 시도] 실패: {e}")
            if attempt < 3:
                time.sleep(30)

def main():
    tz_kst = pytz.timezone('Asia/Seoul')
    today = datetime.datetime.now(tz_kst)
    today_str = today.strftime("%Y%m%d")
    print(f"📡 현재 시스템 구동 날짜: {today_str}")
    
    menu_list, calories = get_lunch_menu(today_str)
    if menu_list:
        create_story_image(today_str, menu_list, calories)
        upload_to_instagram()
    else:
        print("🛑 급식 데이터를 가져오지 못해 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
