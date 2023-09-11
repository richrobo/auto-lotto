import re
import sys
import time
import requests
from datetime import datetime, timedelta

from requests import post, Response
from playwright.sync_api import Playwright, sync_playwright

RUN_FILE_NAME = sys.argv[0]

# 동행복권 아이디와 패스워드를 설정
USER_ID = sys.argv[1]
USER_PW = sys.argv[2]

# TELEGRAM 설정
TELEGRAM_BOT_TOKEN = sys.argv[3]
TELEGRAM_CHAT_ID = sys.argv[4]
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# 구매 개수를 설정
COUNT = sys.argv[5]


def __get_now() -> datetime:
    now_utc = datetime.utcnow()
    korea_timezone = timedelta(hours=9)
    now_korea = now_utc + korea_timezone
    return now_korea



def send_telegram_message(message: str) -> None:
    korea_time_str = __get_now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"> {korea_time_str} *로또 자동 구매 봇 알림* \n{message}",
    }
    response = requests.post(TELEGRAM_API_URL, data=payload)
    if response.status_code != 200:
        print("Failed to send message to Telegram:", response.text)


def run(playwright: Playwright) -> None:
    # hook_slack(f"{COUNT}개 자동 복권 구매 시작합니다!")
    try:
        browser = playwright.chromium.launch(headless=True)  # chrome 브라우저를 실행
        context = browser.new_context()

        page = context.new_page()
        page.goto("https://dhlottery.co.kr/user.do?method=login")
        page.click('[placeholder="아이디"]')
        page.fill('[placeholder="아이디"]', USER_ID)
        page.press('[placeholder="아이디"]', "Tab")
        page.fill('[placeholder="비밀번호"]', USER_PW)
        page.press('[placeholder="비밀번호"]', "Tab")

        # Press Enter
        # with page.expect_navigation(url="https://ol.dhlottery.co.kr/olotto/game/game645.do"):
        with page.expect_navigation():
            page.press('form[name="jform"] >> text=로그인', "Enter")
        time.sleep(4)

        # 로그인 이후 기본 정보 체크 & 예치금 알림
        page.goto("https://dhlottery.co.kr/common.do?method=main")
        money_info = page.query_selector("ul.information").inner_text()
        money_info: str = money_info.split("\n")
        user_name = money_info[0]
        money_info: int = int(money_info[2].replace(",", "").replace("원", ""))
        send_telegram_message(f"로그인 사용자: {user_name}, 예치금: {money_info}")

        # 예치금 잔액 부족 미리 exception
        if 1000 * int(COUNT) > money_info:
            raise Exception(
                "예치금이 부족합니다! \n충전해주세요: https://dhlottery.co.kr/payment.do?method=payment"
            )

        # End of Selenium
        context.close()
        browser.close()
    except Exception as exc:
        send_telegram_message(exc)
        context.close()
        browser.close()
        raise exc


with sync_playwright() as playwright:
    run(playwright)
