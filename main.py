import os
import requests
import datetime
from pytz import timezone
from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client

# ==========================================
# 1. 설정 및 상수 정의
# ==========================================
NEIS_API_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"
OFFICE_CODE = "K10" 
SCHOOL_CODE = "7480070"
FONT_PATH = "NanumGothicBold.ttf"
OUTPUT_IMAGE = "lunch_story.png"

# ==========================================
# 2. 나이스 API로부터 급식 정보 가져오기
# ==========================================
def get_lunch_menu(target_date_str):
    params = {
        "Type": "json",
        "pIndex": 1,
        "pSize": 10,
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "MLSV_YMD": target_date_str
    }
    try:
        response = requests.get(NEIS_API_URL, params=params)
        data = response.json()
        if "mealServiceDietInfo" in data:
            meal_info = data["mealServiceDietInfo"][1]["row"][0]
            menu_raw = meal_info["DDISH_NM"]
            import re
            clean_menu = re.sub(r'\([0-9\.]+\)', '', menu_raw)
            menu_list = [item.strip() for item in clean_menu.split("<br/>") if item.strip()]
            calories = meal_info.get("CAL_INFO", "정보 없음")
            return menu_list, calories
        else:
            print("해당 날짜에는 급식 정보가 존재하지 않습니다.")
            return None, None
    except Exception as e:
        print(f"나이스 API 호출 중 오류 발생: {e}")
        return None, None

# ==========================================
# 3. 인스타그램 스토리용 이미지 생성 (1080x1920)
# ==========================================
def create_story_image(date_str, menu_list, calories):
    width, height = 1080, 1920
    image = Image.new("RGB", (width, height), color="#F0F4F8")
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype(FONT_PATH, 65)
        date_font = ImageFont.truetype(FONT_PATH, 45)
        menu_font = ImageFont.truetype(FONT_PATH, 50)
        info_font = ImageFont.truetype(FONT_PATH, 40)
    except IOError:
        title_font = ImageFont.load_default()
        date_font = ImageFont.load_default()
        menu_font = ImageFont.load_default()
        info_font = ImageFont.load_default()

    draw.rounded_rectangle([80, 150, 1000, 1770], radius=40, fill="#FFFFFF", outline="#E2E8F0", width=4)
    draw.text((540, 260), "속초고등학교", fill="#1E3A8A", font=title_font, anchor="mm")
    draw.text((540, 350), "오늘의 급식 🍚", fill="#2563EB", font=title_font, anchor="mm")
    
    formatted_date = f"{date_str[0:4]}년 {date_str[4:6]}월 {date_str[6:8]}일"
    draw.text((540, 460), formatted_date, fill="#64748B", font=date_font, anchor="mm")
    draw.line([180, 530, 900, 530], fill="#CBD5E1", width=3)
    
    start_y = 620
    line_spacing = 80
    if menu_list:
        for i, item in enumerate(menu_list):
            y_pos = start_y + (i * line_spacing)
            draw.text((540, y_pos), item, fill="#1E293B", font=menu_font, anchor="mm")
        draw.line([180, 1450, 900, 1450], fill="#CBD5E1", width=3)
        draw.text((540, 1530), f"총 칼로리: {calories}", fill="#475569", font=info_font, anchor="mm")
    else:
        draw.text((540, 960), "오늘은 급식이 없습니다. 🏖️", fill="#94A3B8", font=menu_font, anchor="mm")
        
    draw.text((540, 1680), "@sokcho_high_lunch_bot", fill="#94A3B8", font=info_font, anchor="mm")
    image.save(OUTPUT_IMAGE)
    print("스토리 이미지 생성 완료!")

# ==========================================
# 4. 인스타그램 로그인 및 스토리 업로드
# ==========================================
def upload_to_instagram():
    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")
    if not username or not password:
        print("인스타그램 계정 정보 환경변수가 설정되지 않았습니다.")
        return False
    cl = Client()
    try:
        print("인스타그램 로그인 시도 중...")
        cl.login(username, password)
        print("로그인 성공!")
        print("스토리 업로드 중...")
        cl.album_upload_to_story([OUTPUT_IMAGE])
        print("인스타그램 스토리 업로드 완료!")
        return True
    except Exception as e:
        print(f"인스타그램 업로드 실패: {e}")
        return False

def main():
    # 깃허브가 언제 작동하든 무조건 오늘(6월 22일 월요일) 날짜 급식을 강제로 긁어오도록 변경
    today_str = "20260622"
    print(f"강제 조회 날짜: {today_str}")
    
    menu_list, calories = get_lunch_menu(today_str)
    if menu_list:
        create_story_image(today_str, menu_list, calories)
        upload_to_instagram()
    else:
        print("오늘 급식이 없어 스토리를 올리지 않고 종료합니다.")

if __name__ == "__main__":
    main()
