import math
import gspread
import time
import datetime

# import requests
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By

# from pydrive.auth import GoogleAuth
# from pydrive.drive import GoogleDrive
from googleapiclient.discovery import build

# ServiceAccountCredentials：Googleの各サービスへアクセスできるservice変数を生成します。
from oauth2client.service_account import ServiceAccountCredentials
from selenium.webdriver.chrome.options import Options  # オプションを使うために必要
from apiclient.http import MediaFileUpload
from selenium.webdriver.common.alert import Alert

today = datetime.date.today()
dayAfter2Month = today + relativedelta(months=1)
dayAfterMonthYyyyMm = dayAfter2Month.strftime("%Y%m")  # yyyymm
# スプレッドシート操作の準備
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "auto-lottery-987e274706c6.json", scope
)
gc = gspread.authorize(credentials)
drive_service = build("drive", "v3", credentials=credentials)
playTime = {"0900": "2", "1200": "3", "1400": "4", "1600": "5", "1830": "6"}
print(f'playTime:{playTime["1830"]}')


def applicationKawasaki():
    """ふれあいネット抽選自動化モジュール
    スプレッドシートの抽選情報を取得し、抽選を入れる。
    抽選申込後、一覧のスクショを撮り、GoogleDriveにアップロードする。
    スクショを処理結果確認用グループラインへ送信する。
    """

    # IDPASSシート
    SPREADSHEET_KEY_IDPASS = "1B736lqLfQXfU6HXVdSgp9Yb7wLREu6nGjzhSxgLvTgA"
    SPREADSHEET_KEY_LOTTERY_DETAIL_KAWASAKI = (
        "1S7ZlxFiftXQg87FMXxd3dhRD9o6SWFzAVj7DRHPSjik"
    )
    worksheetIdPass = gc.open_by_key(SPREADSHEET_KEY_IDPASS).worksheet("ユーザー")
    # 日付可変（抽選_yyyymm + 1ヵ月後）
    worksheetLottoryDetailYokohama = gc.open_by_key(
        SPREADSHEET_KEY_LOTTERY_DETAIL_KAWASAKI
    ).worksheet(f"抽選_{dayAfterMonthYyyyMm}")
    # usersData = worksheetIdPass.get_all_records(
    #     empty2zero=False, head=1, default_blank=""
    # )
    # lottoryData = worksheetLottoryDetailYokohama.get_all_records(
    #     empty2zero=False, head=1, default_blank=""
    # )
    usersData = worksheetIdPass.get_all_records(numericise_ignore=["all"])
    lottoryData = worksheetLottoryDetailYokohama.get_all_records(
        numericise_ignore=["all"]
    )

    # スクショ保存用のディレクトリ作成
    SHARE_FOLDER_ID = "1hckWWf_S64gB7oQ8MUaYM9QKjzNVPdwY"
    dirInfos = {}

    # ドライブのフォルダ名取得
    response = (
        drive_service.files()
        .list(
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            q=f"parents in '{SHARE_FOLDER_ID}' and trashed = false",
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )

    for file in response.get("files", []):
        print(f"Found file: {file.get('name')} ({file.get('id')})")
        dirInfos[f"{file.get('name')}"] = [f"{file.get('id')}"]

    # ドライブに当月フォルダない場合は作成
    dir = ""
    dirId = ""
    if f"{dayAfterMonthYyyyMm}_川崎" not in dirInfos.keys():
        file_metadata = {
            "name": f"{dayAfterMonthYyyyMm}_川崎",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [SHARE_FOLDER_ID],
        }
        dir = drive_service.files().create(body=file_metadata, fields="id").execute()
        # fieldに指定したidをfileから取得できる
        dirId = dir.get("id")
    else:
        dirId = dirInfos[f"{dayAfterMonthYyyyMm}_川崎"][0]

    # ユニークなnameのリストを作成（抽選データ保有ユーザーのみ）
    targetUsers = {}

    for data in lottoryData:
        if data["name"] not in targetUsers:
            idPass = {}
            tmp = [user for user in usersData if user["name"] == data["name"]]
            print(f"tmp:{tmp}")
            idPass["id"] = tmp[0]["id"]
            idPass["pass"] = tmp[0]["pass"]
            idPass["security_no"] = tmp[0]["security_no"]
            targetUsers[data["name"]] = idPass
    print(f"targetUsers:{targetUsers}")

    option = Options()  # オプションを用意
    option.add_argument("--incognito")  # シークレットモードの設定を付与
    driver = webdriver.Chrome(options=option)
    driver.get("https://www.fureai-net.city.kawasaki.jp/user/view/user/homeIndex.html")

    firstFlg = True  # 初回ログイン画面へ遷移するフラグ
    for key, value in targetUsers.items():
        if firstFlg:
            # ログイン画面
            driver.find_element(By.XPATH, '//*[@id="login"]/img').click()
            firstFlg = False
        driver.find_element(By.ID, "userid").send_keys(value["id"])
        driver.find_element(By.ID, "passwd").send_keys(value["pass"])
        if value["security_no"] != "-":
            driver.find_element(By.ID, "securityno").send_keys(value["security_no"])
        # ログイン
        driver.find_element(By.XPATH, '//*[@id="doLogin"]').click()
        # 「新規抽選を申し込む」
        driver.find_element(By.XPATH, '//*[@id="goLotSerach"]/img').click()
        # 「テニスコート」
        driver.find_element(
            By.XPATH,
            "/html/body/div/table/tbody/tr/td[2]/table[1]/tbody/tr[2]/td/div/table[2]/tbody/tr[2]/td/input[2]",
        ).click()
        # 「中原区」
        driver.find_element(
            By.XPATH,
            "/html/body/div/table/tbody/tr/td[2]/table[1]/tbody/tr[2]/td/div/span[2]/table/tbody/tr[2]/td/input[4]",
        ).click()
        # 「対象館一覧を表示」
        driver.find_element(By.ID, "doSearch").click()
        userInfos = list(filter(lambda user: user["name"] == key, lottoryData))
        for userInfo in userInfos:
            print(f"lottoryData:{lottoryData}")
            print(f"userInfo:{userInfo}")
            # 「施設決定」
            driver.find_element(
                By.XPATH,
                f'/html/body/div/table/tbody/tr/td[2]/table[1]/tbody/tr[2]/td/div/table[2]/tbody/tr[{str(int(userInfo["court_no"])+1)}]/td[3]/div/input',
            ).click()
            # 日付選択
            driver.execute_script(
                f"javascript:selectCalendarDate({str(userInfo['date'])[0:4]},{str(int(str(userInfo['date'])[4:6]))},{str(userInfo['date'])[6:8]});return false;"
            )
            # 時間選択
            driver.find_element(
                By.XPATH,
                f"/html/body/div/form[2]/div/table/tbody/tr/td[2]/table[1]/tbody/tr[2]/td/div/table[2]/tbody/tr[6]/td[{playTime[str(userInfo['time'])]}]/div/div/div/input",
            ).click()
            # 「申込みを確定する」
            driver.find_element(By.XPATH, "//*[@id='doDateTimeSet']").click()
            # 「利用目的」
            driver.find_element(
                By.XPATH,
                "/html/body/div/form[2]/div/table/tbody/tr/td[2]/table[1]/tbody/tr[2]/td/div/table[2]/tbody/tr[5]/td[2]/select/optgroup/option",
            ).click()
            # 「目的の詳細」
            driver.find_element(By.ID, "eventname").clear()
            driver.find_element(By.ID, "eventname").send_keys("テニス")
            # 「グループ名」
            driver.find_element(By.ID, "gname").clear()
            driver.find_element(By.ID, "gname").send_keys("武蔵小杉テニスサークル")
            # 「利用人数（予定）」
            driver.find_element(By.ID, "applycnt").clear()
            driver.find_element(By.ID, "applycnt").send_keys("8")
            # 「抽選内容を確認する」
            driver.find_element(By.ID, "doConfirm").click()
            # 「抽選を申込む」
            driver.find_element(By.ID, "doOnceFix").click()
            # ポップアップ「OK」
            Alert(driver).accept()
            # 「別の日時を申込む」
            driver.find_element(By.ID, "doDateSearch").click()
            # 「施設を選びなおす」
            driver.find_element(By.ID, "goLotIgcdList").click()
        # 「マイページ」
        driver.find_element(
            By.XPATH, "/html/body/div/form[1]/table[1]/tbody/tr/td[3]/a/img"
        ).click()
        # 「 抽選の申し込み状況の一覧へ」
        driver.find_element(
            By.XPATH,
            "/html/body/div/table/tbody/tr/td[2]/form/div/div/table/tbody/tr[2]/td/div/table[2]/tbody/tr/td/a",
        ).click()
        # 申込件数を取得
        lotCnt = driver.find_element(
            By.XPATH,
            '//*[@id="lotCnt"]',
        ).text
        # 申込件数を5で割る
        lotCnt = int(lotCnt) / 5
        # 小数点切り上げ（ページング数）
        lotCnt = math.ceil(lotCnt)
        # ページング数分ループしてスクショ
        for i in range(lotCnt):
            if i != 0:
                # 1ページ目以外はページングリンクをクリック
                driver.find_element(
                    By.XPATH,
                    f"/html/body/div/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/div/div[1]/table/tbody/tr/td/table/tbody/tr/td[1]/span[{i+3}]/a",
                ).click()
            # スクショ
            driver.save_screenshot(
                # f"{key}_{i}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.png"
                f"{key}_{i}.png"
            )
            # GoogleDriveへアップロード
            uploadFileToGoogleDrive(
                drive_service,
                # f"{key}_{i}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.png",
                # f"./{key}_{i}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.png",
                f"{key}_{i}.png",
                f"./{key}_{i}.png",
                "image/png",
                dirId,
            )
        # ログアウト
        driver.find_element(By.ID, "doLogout").click()
        # ログイン画面
        driver.find_element(By.XPATH, '//*[@id="login"]/img').click()


def uploadFileToGoogleDrive(service, fileName, local_path, mimetype, folder_id):
    """GoogleDriveアップロードモジュール
    filename:アップロード先でのファイル名
    local_path:アップロードするファイルのローカルのパス
    mimetype:http通信の規格(csv→text/csv 参照:https://qiita.com/AkihiroTakamura/items/b93fbe511465f52bffaa)
    """

    # "parents": ["****"]この部分はGoogle Driveに作成したフォルダのURLの後ろ側の文字列に置き換えてください。
    file_metadata = {"name": fileName, "mimeType": mimetype, "parents": [folder_id]}
    media = MediaFileUpload(
        local_path, mimetype=mimetype, chunksize=1024 * 1024, resumable=True
    )
    # media = MediaFileUpload(local_path, mimetype=mimetype,resumable=True ) #csvなどの場合はこちらでも可(チャンクサイズは不要)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    # print(f"{fileName}のアップロード完了！")


applicationKawasaki()
