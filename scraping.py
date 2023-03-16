import os
import json
from selenium import webdriver
from dotenv import load_dotenv
load_dotenv()
# 環境変数を参照
USERS = os.getenv('USERS')
usersJson = json.loads(USERS)
driver = webdriver.Chrome()
cnt = 0
driver.get('https://www.fureai-net.city.kawasaki.jp/user/view/user/homeIndex.html')
# ログイン画面
elem = driver.find_element_by_xpath('//*[@id="login"]/img')
elem.click()
for key, value in usersJson.items():
    if cnt != 0:
        # ログイン画面
        elem = driver.find_element_by_xpath('//*[@id="login"]/img')
        elem.click()
    texts = driver.find_element_by_id("userid")
    texts.send_keys(value['id'])
    texts = driver.find_element_by_id("passwd")
    texts.send_keys(value['pass'])
    # ログイン
    elem = driver.find_element_by_xpath('//*[@id="doLogin"]')
    elem.click()
    # 新規抽選を申し込む
    elem = driver.find_element_by_xpath('//*[@id="goLotSerach"]/img')
    elem.click()
    # TODO
    # ログアウト
    elem = driver.find_element_by_xpath('//*[@id="doLogout"]')
    elem.click()
    cnt += 1
