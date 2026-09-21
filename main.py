import os
import sys
import requests

def get_env_variable(var_name: str) -> str:
    val = os.getenv(var_name)
    if not val:
        print(f"錯誤：缺少環境變數 {var_name}")
        sys.exit(1)
    return val

def fetch_weather_data(api_key: str, location_name: str = "臺北市"):
    """
    串接氣象署 F-C0032-001 (一般天氣預報-今明36小時天氣預報)
    取得當天最高溫度 (MaxT) 與最高降雨機率 (PoP)
    """
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": api_key,
        "locationName": location_name
    }
    
    resp = requests.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"氣象 API 請求失敗，HTTP {resp.status_code}: {resp.text}")
        
    data = resp.json()
    if not data.get("success") == "true":
        raise Exception(f"氣象 API 回傳錯誤：{data.get('message')}")
        
    records = data["records"]["location"][0]["weatherElement"]
    
    max_pop = 0
    max_temp = -99.0

    for element in records:
        if element["elementName"] == "PoP":
            for time_slot in element["time"]:
                pop_val = int(time_slot["parameter"]["parameterName"])
                if pop_val > max_pop:
                    max_pop = pop_val
        elif element["elementName"] == "MaxT":
            for time_slot in element["time"]:
                temp_val = float(time_slot["parameter"]["parameterName"])
                if temp_val > max_temp:
                    max_temp = temp_val

    return max_temp, max_pop

def fetch_aqi_data(api_key: str, sitename: str = "中山"):
    """
    串接環境部空氣品質指標 (AQI) API (aqx_p_432)
    """
    url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
    params = {
        "api_key": api_key,
        "limit": 1000,
        "sort": "ImportDate desc",
        "format": "JSON"
    }
    
    resp = requests.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"環境部 AQI API 請求失敗，HTTP {resp.status_code}: {resp.text}")
        
    records = resp.json().get("records", [])
    for rec in records:
        if rec.get("sitename") == sitename:
            aqi_val = rec.get("aqi")
            return int(aqi_val) if aqi_val and aqi_val.isdigit() else 0
            
    if records and records[0].get("aqi", "").isdigit():
        return int(records[0]["aqi"])
    return 0

def generate_commute_alert(location: str, max_temp: float, max_pop: int, aqi: int) -> str:
    suggestions = []

    if max_pop >= 60:
        suggestions.append("☔ 降雨機率偏高（≥ 60%），出門請記得攜帶雨傘。")
    if max_temp >= 33.0:
        suggestions.append("☀️ 氣溫偏高（≥ 33°C），外出注意防曬並多補充水分。")
    if aqi >= 100:
        suggestions.append("😷 空氣品質不佳（AQI ≥ 100），建議配戴口罩防護。")

    if not suggestions:
        advice_text = "🌿 今日各項指標良好，適合外出通勤！"
    else:
        advice_text = "\n".join(suggestions)

    message = (
        f"🚲 *【智慧通勤風險通知】*\n"
        f"📍 地點：{location}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🌡️ 最高氣溫：`{max_temp} °C`\n"
        f"🌧️ 最高降雨機率：`{max_pop} %`\n"
        f"💨 空氣品質 AQI：`{aqi}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"*💡 通勤建議：*\n{advice_text}"
    )
    return message

def send_telegram_message(bot_token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    resp = requests.post(url, json=payload, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"Telegram 發送失敗，HTTP {resp.status_code}: {resp.text}")
    print("訊息已成功發送至 Telegram。")

def main():
    cwa_api_key = get_env_variable("CWA_API_KEY")
    moenv_api_key = get_env_variable("MOENV_API_KEY")
    tg_bot_token = get_env_variable("TG_BOT_TOKEN")
    tg_chat_id = get_env_variable("TG_CHAT_ID")
    target_location = os.getenv("TARGET_LOCATION", "臺北市")
    target_aqi_site = os.getenv("TARGET_AQI_SITE", "中山")

    print(f"正在取得 {target_location} 的天氣與 AQI 數據...")
    max_temp, max_pop = fetch_weather_data(cwa_api_key, target_location)
    aqi = fetch_aqi_data(moenv_api_key, target_aqi_site)

    alert_msg = generate_commute_alert(target_location, max_temp, max_pop, aqi)
    print("準備發送通知內容：\n", alert_msg)
    
    send_telegram_message(tg_bot_token, tg_chat_id, alert_msg)

if __name__ == "__main__":
    main()
