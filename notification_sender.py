from plyer import notification
import schedule
import time
from datetime import datetime

def send_notification():
    notification.notify(
        title='Daily Hatırlatma!',
        message='Bugün için daily göndermeyi unutmayın!',
        app_icon=None,  # e.g. 'C:\\icon.ico'
        timeout=10,  # seconds
    )

def check_time():
    # Eğer saat 10:00 ise ve iş günüyse bildirim gönder
    current_time = datetime.now()
    if current_time.hour == 10 and current_time.minute == 0:
        if current_time.weekday() < 5:  # 0-4 arası Pazartesi-Cuma
            send_notification()

# Her gün saat 10:00'da bildirim gönder
schedule.every().day.at("10:00").do(send_notification)

if __name__ == "__main__":
    print("Bildirim sistemi başlatıldı...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Her dakika kontrol et