# 音樂資料庫專案說明 (MUSICDB_PROJECT)

大學專題，音樂資料庫查詢程式


## 版本需求
最低Python版本: **Python3.13**

## 安裝教學 (Installation)

1.  **Clone 專案庫**

    先 `cd` 到你要儲存專案的位置，然後執行：
    ```bash
    git clone https://github.com/ChengYi0224/MusicDB_Project.git
    cd MUSICDB_PROJECT
    ```

2.  **建立並啟用虛擬環境 (Virtual Environment)**

    為了避免專案之間的套件版本衝突，強烈建議使用虛擬環境來隔離本專案的依賴套件。

    **a. 建立虛擬環境**
    在專案根目錄 (`MUSICDB_PROJECT/`) 下執行以下指令，建立一個名為 `venv` 的虛擬環境資料夾：
    ```bash
    py -m venv venv
    ```
    
    **b. 啟用虛擬環境**
    啟用指令根據你的作業系統而有所不同：

    * **Windows (CMD / PowerShell):**
        ```bash
        .\venv\Scripts\activate
        ```

    * **macOS / Linux (bash / zsh):**
        ```bash
        source venv/bin/activate
        ```
    成功啟用後，你的終端機前方會出現 `(venv)` 的字樣。

3.  **安裝依賴套件**

    **請先確認你已經啟用虛擬環境**（看到 `(venv)` 字樣）。接著安裝所有必要的套件。
    ```bash
    pip install -r requirements.txt
    ```

---

## 爬蟲使用教學 (Usage)

⚠️ **重要：** 所有指令都必須在專案的**根目錄** (`MusicDB_Project/`) 下執行，而不是在 `scripts` 或 `crawler` 資料夾內。

### 1. 執行爬蟲程式 (Crawler)

此程式用於從指定來源抓取音樂相關資料。
目前爬取兩種資料:songs以及playlist
可以在以下的`main.py`檔案中調整參數

**指令：**
```bash
py -m backend.crawler.main
```

**說明：**
* `py -m`: 使用 `-m` 旗標可以讓 Python 將當前目錄（專案根目錄）視為頂層套件，從而正確找到 `backend.crawler.main` 模組，避免發生 `ModuleNotFoundError`。
* 執行後，爬蟲會開始運作，抓取的結果可能會存儲在指定的檔案或直接寫入資料庫，具體行為取決於程式碼的實現。

---

### 2. 執行資料上傳腳本 (Upload Scripts)

爬取好資料後，你的本地會多出:
- **`downloads`資料夾**: 儲存本地歌曲音訊
- **`crawled_results`資料夾**: 儲存本地的歌曲資訊

#### 上傳資料

分別使用以下指令上傳
> ⚠️ 請確認自己電腦**是否支援IPv6**，上傳過程只支援IPv6，否則將失敗

**指令：**
```bash
py -m backend.scripts.upload_playlists
py -m backend.scripts.upload_songs
```