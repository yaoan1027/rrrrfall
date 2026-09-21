# smart-commute-alert

智慧通勤風險通知系統，利用 GitHub Actions 定時執行 Python 腳本，串接中央氣象署 (CWA) 與環境部 (MOENV) 資料，依通勤門檻透過 Telegram Bot 推送預警。

## 功能規格
- 取得地點最高溫度、最高降雨機率與 AQI。
- 降雨機率 ≥ 60% 提醒帶傘。
- 最高溫 ≥ 33°C 提醒防曬補水。
- AQI ≥ 100 提醒配戴口罩。
- 指標皆正常時顯示適合外出。
- GitHub Actions 平日上午 07:00 (台灣時間) 自動推播，支援手動觸發。
