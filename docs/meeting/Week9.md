# 會議內容
1. 加入GitHub!!!
2. 討論開發順序
3. 專案資料夾介紹
4. Flask基本常識

## #1 GitHub 儲存庫連結
https://github.com/ChengYi0224/MusicDB_Project

## #2 開發順序
前期有以下內容
- **資料庫**
    - SQL資料庫表格schema
- **App首頁**
    - 歌曲搜尋
    - 歌曲播放

## #3 專案資料夾
先介紹幾個重要的
- `backend`: 存放一切後端程式
    - `app\`
        - `route\`: 網頁路由
        - `utils\`: 放一些helper function
    - `config\`: 放伺服器設定檔
    - `main.py`: **主程式入口!!!**

## #4 Flask與python基本知識
### 1. 如何import套件
在 Python 裡，一個「**套件（package）**」可以理解成是一堆功能的集合，方便你重複利用別人寫好的程式碼，不用自己從頭寫。
這些套件會被組織成很多「**模組（module）**」，也就是 `.py` 檔案。
```python
from flask import Flask
```
這句的意思是：
- `flask` 是一個外部套件（我們安裝在`venv`）

- `Flask` 是這個套件裡的一個「類別（class）」或「物件（object）」

- 這句話的意思是：「**從 flask 這個套件中，匯入 Flask 這個類別**」

### 2. 什麼是route
- app/home
- app/user/klps0224

**Flask程式寫法**
```python
@app.route('/home')
    def home():
        return render_template('index.html') #這是使用html的寫法
@app.route('/user/<name>')
    def search(name):
        return f"This is {name}'s profile" #直接輸出格式化字串的寫法
```

### 3. 模組化我們的功能
Flask有一個功能叫做「**藍圖(Blueprint)**」，我們可以把各個不同的功能**放到不同的藍圖**

範例:把`app/profile`和`app/player`放在不同的藍圖
```python
from flask import Flask

app = Flask(__name__)

player_bp = Blueprint('player', __name__, url_prefix='/player')
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@player_bp.route('/')
def player_home():
    return "這是播放模組的首頁"

@profile_bp.route('/')
def profile_home():
    return "這是個人檔案模組的首頁"

# 註冊藍圖到主應用
app.register_blueprint(player_bp)
app.register_blueprint(profile_bp)
```

## 其他：虛擬環境&執行程式
請參見根目錄的`README.md`