import os
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client
import pytz
import time
import re

def get_lunch_menu(today_str):
    """나이스 API 최종 연동 규격에 맞춰 속초고 점심 급식을 완벽하게 긁어오는 함수"""
    URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    
    # [최종 교차 검증 완료] 강원특별자치도교육청(J10) / 속초고등학교 API 전용 코드(7831023)
    PARAMS = {
        "Type": "json",
        "pIndex": "1",
        "pSize": "100",
        "ATPT_OFCDC_SC_CODE": "J10",   # 강원특별자치도교육청 진짜 코드
        "SD_SCHUL_CODE": "7831023",    # 속초고등학교 오픈 API 전용 기관코드
        "MLSV_YMD": today_str,         # 조회 날짜
        "MMEAL_SC_CODE": "2"           # 점심 식사 번호 고정
    }
    
    try:
        response = requests.get(URL, params=PARAMS, timeout=20)
        data = response.json()
        
        if "mealServiceDietInfo" in data:
            row = data["mealServiceDietInfo"][1]["row"][0]
            raw_menu = row["DDISH_NM"]
            
            # 알레르기 유발 숫자 및 특수문자 완벽 제거 정제
            clean_menu = raw_menu.replace("<br/>", "\n")
            clean_menu = re.sub(r'[0-9\.\*]', '', clean_menu)
            
            menu_list = [line.strip() for line in clean_menu.split("\n") if line.strip()]
            calories = row.get("CAL_INFO", "정보 없음")
            return menu_list, calories
        else:
            print(f"⚠️ [나이스 전산망 최종 응답 복사]: {data}")
            return None, None
            
    except Exception as e:
        print(f"❌ 나이스 API 통신 중 치명적 오류 발생: {e}")
        return None, None

def create_story_image(today_str, menu_list, calories):
    """폰트 누락으로 인한 튕김을 완벽 차단한 인스타 스토리용 이미지 생성 함수"""
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
    print("📸 스토리용 급식 이미지 파일 생성 완료")

def upload_to_instagram():
    """인스타그램 보안 우회 및 스토리 업로드 수행 함수"""
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
            print(f"🔐 [{attempt}차 시도] 인스타그램 로그인 프로세스 구동...")
            cl.login(username, password)
            print("📤 인스타그램 스토리 채널 전송 중...")
            cl.album_upload_to_story(["lunch_story.jpg"])
            print("🎉 [최종 성공] 인스타그램 스토리 채널에 오늘 급식이 게시되었습니다!")
            return
        except Exception as e:
            print(f"⚠️ [{attempt}차 시도] 업로드 실패: {e}")
            if attempt < 3:
                time.sleep(30)
            else:
                print("❌ 인스타 Secrets 설정 혹은 비밀번호 변경 여부를 확인해 주세요.")

def main():
    tz_kst = pytz.timezone('Asia/Seoul')
    today = datetime.datetime.now(tz_kst)
    today_str = today.strftime("%Y%m%d")
    print(f"📡 현재 시스템 구동 날짜 및 시간: {today.strftime('%Y-%m-%d %H:%M:%S')} KST")
    
    menu_list, calories = get_lunch_menu(today_str)
    if menu_list:
        create_story_image(today_str, menu_list, calories)
        upload_to_instagram()
    else:
        print("🛑 나이스 전산망 장부 조회 실패로 빌드를 종료합니다.")

if __name__ == "__main__":
    main()
