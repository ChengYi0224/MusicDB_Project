# 學習筆記
## flask
### 取得資料
**GET**
這是預設的取得方式，沒有加密

例如使用者在網址輸入`/user/abcd`

任何人可以直接取得`abcd`這個資料

**POST**
這是取得包裝過、formed的資料

**運作邏輯如下**
1. 使用者進入網頁，flask以預設GET方法處理
2. 在方框輸入資訊(例如username) (`input type = "text" name = "usr"`)
3. 使用者按下送出 (`input type="submit"`)
4. 我們redirect回到同個網站
5. flask偵測到POST，使用POST方法，成功取得資料
6. 後端處理資料...

## HTML
剛剛提到了`input`，我們現在來看看input怎麼用
### input
`input` 是網站上用來進行輸入的方塊

有多種`type`可以指定，詳細請參考[網站](https://matthung0807.blogspot.com/2019/08/html-input-value.html)

例如:
```html
<!-- 文字輸入欄位 -->
<input type="text" value="你好">
<!-- 搜尋欄位 -->
<input type="search" value="天氣預報">
<!-- URL輸入欄位 -->
<input type="url" value="https://www.google.com.tw/">
<!-- 密碼輸入欄位 -->
<input type="password" value="12345">
<!-- 提交按鈕 -->
<input type="submit" value="這是提交按鈕">
```
