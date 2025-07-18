import twitter_client as tc
import x_api_usage as xusage
import os
import time
import working_wjson as wj

t_client = tc.get_twitter_client()
# Opcional: Agrega tu propia cuenta como authorized para pruebas
t_client.authorized_users.add('StockP_Ai')  # O el username

def safe_monitor_and_respond():
    while True:
        try:
            # Verifica caps antes de cada ciclo
            usage = xusage.check_caps()
            print(f"[USO API X] Lecturas: {usage['read']}/{xusage.READ_CAP} | Posts usuario: {usage['post_user']}/{xusage.POST_CAP_USER} | Posts app: {usage['post_app']}/{xusage.POST_CAP_APP}")
            t_client.monitor_and_respond_mentions()
        except Exception as e:
            print(f"[ADVERTENCIA] {e}")
            print("Deteniendo bot para evitar bloqueo por límites de API.")
            break

def erase_analysis_data():
    # Erase all previous analysis data files
    for fname in [
        'data/data_total_analyze.json',
        'data/uncertity_per_company.json',
        'data/x_tweets.json',
        'data/yf_news.json',
        'data/google_news.json',
        'data/Combined_Prob.json',
    ]:
        wj.save_to_json({}, fname)
    print('[INFO] All previous analysis data erased.')

# Track last erase time
erase_interval = 600  # 10 minutes in seconds
last_erase_time = time.time()

def periodic_erase():
    global last_erase_time
    now = time.time()
    if now - last_erase_time > erase_interval:
        erase_analysis_data()
        last_erase_time = now

if __name__ == "__main__":
    erase_analysis_data()  # Erase all analysis data on startup
    while True:
        periodic_erase()  # Erase every 10 minutes
        safe_monitor_and_respond()
        time.sleep(1)








