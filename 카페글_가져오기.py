"""
네이버 카페 글 가져오기 (다음글 반복 읽기)
- 셀레니움으로 네이버 로그인 (pyperclip 방식)
- 카페 글 내용 스크래핑
- '기말시험 후기' 게시판의 다음글을 반복적으로 읽기
"""

import os
import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ── 네이버 계정 정보 ──
NAVER_ID = "compu21"
NAVER_PW = "nipdms55"

# ── 네이버 로그인 URL ──
LOGIN_URL = "https://nid.naver.com/nidlogin.login"

# ── 카페 글 URL (시작점) ──
CAFE_ARTICLE_URL = (
    "https://cafe.naver.com/f-e/cafes/30428231/articles/11217"
    "?boardtype=L&menuid=137&referrerAllArticles=false"
)

# ── 최대 읽을 글 수 (9999 = 사실상 무제한, 다음글이 없을 때 자동 종료) ──
MAX_ARTICLES = 9999

# ── 결과 저장 경로 ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "카페글_결과.txt")
DEBUG_HTML_FILE = os.path.join(BASE_DIR, "temp_cafe_page.html")


def create_driver():
    """크롬 드라이버 생성"""
    chrome_options = Options()
    # 자동화 탐지 우회 옵션
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    # 로그 레벨 설정
    chrome_options.add_argument("--log-level=3")
    # User-Agent 설정
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Safari/537.36"
    )
    # 창 크기 설정
    chrome_options.add_argument("--window-size=1280,900")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # navigator.webdriver 속성 제거 (봇 탐지 우회)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    return driver


def pyperclip_input(element, text):
    """
    pyperclip을 이용한 입력 방식
    - 직접 타이핑 대신 클립보드 복사 → 붙여넣기로 입력
    - 네이버 봇 탐지(키 입력 패턴 분석) 우회용
    """
    element.click()
    time.sleep(0.3)
    element.clear()
    time.sleep(0.2)

    # pyperclip으로 클립보드에 복사
    pyperclip.copy(text)
    time.sleep(0.2)

    # Ctrl+V로 붙여넣기
    element.send_keys(Keys.CONTROL, "v")
    time.sleep(0.5)


def naver_login(driver):
    """네이버 로그인 수행"""
    print("🔐 네이버 로그인 페이지 접속 중...")
    driver.get(LOGIN_URL)
    time.sleep(3)

    wait = WebDriverWait(driver, 10)

    # ── 1) 아이디 입력 (id="id") ──
    print("📝 아이디 입력 중...")
    id_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#id")))
    pyperclip_input(id_input, NAVER_ID)
    time.sleep(1)

    # ── 2) 비밀번호 입력 (id="pw") ──
    print("🔑 비밀번호 입력 중...")
    pw_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#pw")))
    pyperclip_input(pw_input, NAVER_PW)
    time.sleep(1)

    # ── 3) 로그인 버튼 클릭 (id="log.login") ──
    print("🖱️ 로그인 버튼 클릭...")
    login_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#log\\.login"))
    )
    login_btn.click()
    print("⏳ 로그인 처리 대기 중...")
    time.sleep(5)

    # ── 4) 로그인 결과 확인 ──
    current_url = driver.current_url
    print(f"📍 현재 URL: {current_url}")

    # '새로운 기기 등록' 등의 추가 인증 페이지가 뜰 수 있음
    if "nid.naver.com" in current_url:
        print("⚠️  추가 인증이 필요할 수 있습니다. 수동으로 처리해주세요.")
        print("   (60초 대기 중... 인증 완료 후 자동으로 진행됩니다)")
        for i in range(60):
            time.sleep(1)
            if "nidlogin" not in driver.current_url:
                break

    # 로그인 성공 여부 확인
    if "nidlogin" not in driver.current_url:
        print("✅ 네이버 로그인 성공!")
        return True
    else:
        print("❌ 로그인 실패 또는 추가 인증 필요")
        return False


def read_cafe_article(driver, url):
    """
    네이버 카페 글 내용 읽기
    - 네이버 카페는 iframe(#cafe_main) 안에 본문이 렌더링됨
    - iframe으로 전환 후 본문 추출
    """
    print(f"\n📖 카페 글 접속 중...")
    print(f"   URL: {url}")
    driver.get(url)

    # 페이지 로딩 대기
    print("⏳ 페이지 로딩 대기 중 (5초)...")
    time.sleep(5)

    wait = WebDriverWait(driver, 15)

    result = {
        "title": "",
        "author": "",
        "date": "",
        "content": "",
        "comments": [],
        "url": url,
    }

    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # iframe(cafe_main)으로 전환
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("🔄 iframe(cafe_main)으로 전환 중...")
        iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#cafe_main"))
        )
        driver.switch_to.frame(iframe)
        print("✅ iframe 전환 완료!")
        time.sleep(3)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 글 제목 찾기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        title_selectors = [
            "h3.title_text",
            ".article_header .title_text",
            ".tit_area .title_text",
            ".ArticleTitle .title_text",
            ".se_title .se_textarea",
            "h3[class*='title']",
        ]
        for sel in title_selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if text and len(text) > 0:
                    result["title"] = text
                    print(f"📌 제목: {result['title']}")
                    break
            except Exception:
                continue

        if not result["title"]:
            try:
                title_tag = driver.title
                if title_tag:
                    result["title"] = title_tag.replace(" : 네이버 카페", "").strip()
                    print(f"📌 제목 (title 태그): {result['title']}")
            except Exception:
                print("⚠️  제목을 찾을 수 없습니다.")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 작성자 찾기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        author_selectors = [
            ".nickname .text",
            ".profile_info .nickname",
            ".WriterInfo .nickname",
            ".article_writer .nick",
            ".nick_box .nickname",
            "[class*='nickname'] .text",
            ".se_author",
        ]
        for sel in author_selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if text and len(text) > 0:
                    result["author"] = text
                    print(f"👤 작성자: {result['author']}")
                    break
            except Exception:
                continue

        if not result["author"]:
            print("⚠️  작성자를 찾을 수 없습니다.")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 작성 날짜 찾기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        date_selectors = [
            ".article_info .date",
            ".WriterInfo .date",
            ".profile_info .date",
            ".se_publishDate",
            "span.date",
        ]
        for sel in date_selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if text and len(text) > 3:
                    result["date"] = text
                    print(f"📅 작성일: {result['date']}")
                    break
            except Exception:
                continue

        if not result["date"]:
            print("⚠️  작성일을 찾을 수 없습니다.")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 본문 내용 찾기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        content_selectors = [
            ".se-main-container",
            ".article_viewer",
            "#body",
            ".ContentRenderer",
            ".content_area",
            ".ArticleContentBox",
            ".post_article",
        ]
        for sel in content_selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if text and len(text) > 10:
                    result["content"] = text
                    print(f"\n📄 본문 ({len(text)}자)")
                    break
            except Exception:
                continue

        if not result["content"]:
            print("⚠️  특정 셀렉터로 본문을 찾지 못함. body 텍스트를 추출합니다.")
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                result["content"] = body_text
                print(f"📄 iframe body 텍스트 ({len(body_text)}자)")
            except Exception:
                print("❌ 페이지 텍스트도 추출할 수 없습니다.")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 댓글 찾기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        comment_selectors = [
            ".comment_box .text_comment",
            ".comment_area .comment_box",
            ".CommentItem",
            "[class*='comment_text']",
        ]
        for sel in comment_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    text = el.text.strip()
                    if text:
                        result["comments"].append(text)
                if result["comments"]:
                    break
            except Exception:
                continue

        if result["comments"]:
            print(f"💬 댓글 {len(result['comments'])}개")

        # iframe에서 빠져나오기
        driver.switch_to.default_content()

    except Exception as e:
        print(f"❌ 글 읽기 중 오류: {e}")
        import traceback
        traceback.print_exc()
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

    return result


def find_next_article_url(driver):
    """
    현재 글 페이지의 iframe 안에서 '다음글' 링크를 찾아 URL을 반환
    - 네이버 카페 글 하단에 '다음글' 링크가 있음
    - 같은 게시판(기말시험 후기)의 다음글만 대상
    - 반환값: 다음글 URL (없으면 None)
    """
    try:
        wait = WebDriverWait(driver, 10)

        # iframe으로 전환
        iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#cafe_main"))
        )
        driver.switch_to.frame(iframe)
        time.sleep(2)

        next_url = None

        # ── 방법 1: 다음글 링크 찾기 (다양한 셀렉터) ──
        next_selectors = [
            # 네이버 카페 일반적인 다음글 영역
            ".ArticleNextArticle a",
            ".prev_next .next a",
            ".board_action .next a",
            ".Knext a",
            # '다음글' 텍스트를 포함하는 링크
            "a[class*='next']",
            "a[class*='Next']",
        ]

        for sel in next_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    href = el.get_attribute("href")
                    text = el.text.strip()
                    if href and ("articles" in href or "ArticleRead" in href):
                        next_url = href
                        print(f"🔗 다음글 발견: {text} → {href}")
                        break
                if next_url:
                    break
            except Exception:
                continue

        # ── 방법 2: XPath로 '다음글' 텍스트 주변 링크 찾기 ──
        if not next_url:
            try:
                # "다음글" 텍스트가 포함된 요소 근처의 <a> 태그
                next_elements = driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(),'다음글')]/ancestor::*[self::div or self::li or self::tr]//a[@href]"
                )
                for el in next_elements:
                    href = el.get_attribute("href")
                    text = el.text.strip()
                    if href and text and len(text) > 1:
                        # 절대 URL로 변환
                        if href.startswith("/"):
                            href = "https://cafe.naver.com" + href
                        next_url = href
                        print(f"🔗 다음글 발견 (XPath): {text}")
                        break
            except Exception:
                pass

        # ── 방법 3: '다음글' 라벨이 있는 행에서 링크 추출 ──
        if not next_url:
            try:
                # 글 하단 네비게이션에서 다음글 찾기
                all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
                for link in all_links:
                    href = link.get_attribute("href") or ""
                    # 같은 카페의 다른 글 링크인지 확인
                    if "cafes/30428231/articles/" in href:
                        # 현재 글 URL과 다른지 확인
                        parent_text = ""
                        try:
                            parent = link.find_element(By.XPATH, "./..")
                            parent_text = parent.text.strip()
                        except Exception:
                            pass

                        if "다음글" in parent_text or "다음 글" in parent_text:
                            next_url = href
                            link_text = link.text.strip()
                            print(f"🔗 다음글 발견 (부모요소): {link_text}")
                            break
            except Exception:
                pass

        # iframe에서 빠져나오기
        driver.switch_to.default_content()

        return next_url

    except Exception as e:
        print(f"⚠️  다음글 찾기 중 오류: {e}")
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return None



def save_result_append(result, article_num, is_first=False):
    """
    결과를 텍스트 파일에 추가(append) 저장
    - is_first=True: 파일을 새로 생성 (첫 번째 글)
    - is_first=False: 기존 파일에 이어서 저장
    """
    mode = "w" if is_first else "a"
    with open(OUTPUT_FILE, mode, encoding="utf-8") as f:
        if not is_first:
            f.write("\n\n")

        f.write(f"{'━' * 70}\n")
        f.write(f"📌 [{article_num}번째 글]\n")
        f.write(f"{'━' * 70}\n")
        f.write(f"제목: {result['title']}\n")
        f.write(f"작성자: {result['author']}\n")
        f.write(f"작성일: {result['date']}\n")
        f.write(f"URL: {result['url']}\n")
        f.write("=" * 60 + "\n")
        f.write(f"\n{result['content']}\n")
        f.write("\n" + "=" * 60 + "\n")
        if result["comments"]:
            f.write(f"\n댓글 ({len(result['comments'])}개):\n")
            f.write("-" * 40 + "\n")
            for idx, comment in enumerate(result["comments"], 1):
                f.write(f"[{idx}] {comment}\n")

    print(f"💾 [{article_num}번째 글] 저장 완료")


import re


def get_resume_info():
    """
    기존 결과 파일에서 마지막 글 번호와 URL을 읽어와 이어서 읽기 지원
    반환: (last_article_num, last_url) 또는 (0, None)
    """
    if not os.path.exists(OUTPUT_FILE):
        return 0, None

    last_num = 0
    last_url = None

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # [N번째 글] 패턴에서 가장 마지막 번호 추출
        nums = re.findall(r"\[(\d+)번째 글\]", content)
        if nums:
            last_num = int(nums[-1])

        # 마지막 URL: 줄 찾기
        urls = re.findall(r"URL: (.+)", content)
        if urls:
            last_url = urls[-1].strip()

        if last_num > 0:
            print(f"📂 기존 파일 발견: {last_num}개의 글이 저장되어 있습니다.")
            print(f"   마지막 글 URL: {last_url}")

    except Exception as e:
        print(f"⚠️  기존 파일 읽기 오류: {e}")

    return last_num, last_url


def main():
    """메인 실행 - 다음글 반복 읽기 (이어서 읽기 지원)"""
    driver = None
    try:
        # 0. 이어서 읽기 확인
        last_num, last_url = get_resume_info()

        resume_mode = False
        if last_num > 0 and last_url:
            print(f"\n❓ 이어서 읽을까요?")
            print(f"   [1] 이어서 읽기 ({last_num}번째 글 다음부터)")
            print(f"   [2] 처음부터 다시 읽기")
            choice = input("   선택 (1/2): ").strip()
            if choice == "1":
                resume_mode = True
                print(f"\n➡️  {last_num}번째 글 다음부터 이어서 읽습니다.")
            else:
                print(f"\n🔄 처음부터 다시 읽습니다.")

        # 1. 드라이버 생성
        driver = create_driver()
        print("🚀 크롬 브라우저 실행 완료")

        # 2. 네이버 로그인
        login_success = naver_login(driver)

        if login_success:
            print("\n✅ 로그인 완료! 카페 글 가져오기를 시작합니다...")

            if resume_mode:
                # 이어서 읽기: 마지막 글 페이지로 이동 → 다음글 URL 가져오기
                print(f"\n📖 마지막 글 페이지로 이동하여 다음글 URL을 가져옵니다...")
                driver.get(last_url)
                time.sleep(5)
                next_url = find_next_article_url(driver)

                if next_url:
                    current_url = next_url
                    article_count = last_num
                    print(f"✅ 다음글 발견! {article_count + 1}번째 글부터 시작합니다.")
                else:
                    print("🏁 마지막 글 이후 다음글이 없습니다. 수집 완료!")
                    input("아무 키나 누르면 종료합니다...")
                    return
            else:
                # 처음부터 읽기
                current_url = CAFE_ARTICLE_URL
                article_count = 0

            visited_urls = set()  # 중복 방문 방지

            while current_url and article_count < MAX_ARTICLES:
                # 중복 체크
                if current_url in visited_urls:
                    print(f"\n⚠️  이미 방문한 글입니다. 중단합니다.")
                    break
                visited_urls.add(current_url)

                article_count += 1
                print(f"\n{'=' * 70}")
                print(f"📖 [{article_count}번째 글] 읽기 시작")
                print(f"{'=' * 70}")

                # 3. 카페 글 읽기
                article = read_cafe_article(driver, current_url)

                # 4. 결과 저장 (이어서 읽기면 항상 append)
                is_first = (article_count == 1 and not resume_mode)
                save_result_append(article, article_count, is_first)

                if article["title"]:
                    print(f"   제목: {article['title']}")
                    print(f"   본문: {len(article['content'])}자 / 댓글: {len(article['comments'])}개")
                else:
                    print("   ⚠️ 글 내용을 가져오지 못했습니다.")

                # 5. 다음글 URL 찾기
                print(f"\n🔍 다음글 찾는 중...")
                next_url = find_next_article_url(driver)

                if next_url:
                    print(f"➡️  다음글로 이동합니다...")
                    current_url = next_url
                    # 네이버 봇 탐지 방지를 위해 잠시 대기
                    time.sleep(3)
                else:
                    print(f"\n🏁 다음글이 없습니다. 수집을 종료합니다.")
                    break

            # ── 최종 결과 요약 ──
            print(f"\n{'=' * 70}")
            print(f"🎉 수집 완료!")
            print(f"   총 {article_count}개의 글이 저장되어 있습니다.")
            print(f"   저장 파일: {OUTPUT_FILE}")
            print(f"{'=' * 70}")

            print("\n⏳ 브라우저를 확인하세요. 아무 키나 누르면 종료합니다.")
            input()
        else:
            print("\n⚠️  로그인에 실패했습니다. 계정 정보를 확인해주세요.")
            input("아무 키나 누르면 종료합니다...")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        input("아무 키나 누르면 종료합니다...")

    finally:
        if driver:
            driver.quit()
            print("🔒 브라우저 종료 완료")


if __name__ == "__main__":
    main()

