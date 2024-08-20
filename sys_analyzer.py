import psutil
import threading
import time
import platform
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Global değişkenler
cpu_percent = 0
virtual_memory_percent = 0
cpu_freq = 0
used_memory_mb = 0
total_memory_mb = 0
bytes_sent = 0
bytes_recv = 0
load_avg = 0
cpu_temp = 0
battery_percent = 0
disk_partitions_info = {}
system_info = {
    "platform": platform.system(),
    "platform_version": platform.version(),
    "platform_release": platform.release(),
    "machine": platform.machine(),
    "processor": platform.processor(),
    "cpu_cores": psutil.cpu_count(logical=True),
    "memory": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB",
}

# Thread-safe işlemler için kilit
lock = threading.Lock()

# Veri toplama fonksiyonları
def update_cpu_percent():
    global cpu_percent
    while True:
        with lock:
            cpu_percent = psutil.cpu_percent(interval=1)
        time.sleep(1)

def update_virtual_memory():
    global virtual_memory_percent, used_memory_mb, total_memory_mb
    while True:
        with lock:
            virtual_memory = psutil.virtual_memory()
            virtual_memory_percent = virtual_memory.percent
            used_memory_mb = virtual_memory.used / (1024 * 1024)
            total_memory_mb = virtual_memory.total / (1024 * 1024)
        time.sleep(1)

def update_cpu_freq():
    global cpu_freq
    while True:
        with lock:
            cpu_freq = psutil.cpu_freq().current
        time.sleep(1)

def update_network_io():
    global bytes_sent, bytes_recv
    while True:
        with lock:
            net_io = psutil.net_io_counters()
            bytes_sent = (net_io.bytes_sent * 8) / (1024 * 1024)  # Mbps cinsinden
            bytes_recv = (net_io.bytes_recv * 8) / (1024 * 1024)  # Mbps cinsinden
        time.sleep(1)

def update_disk_usage():
    global disk_partitions_info
    while True:
        with lock:
            partitions = psutil.disk_partitions()
            disk_partitions_info = {p.device: psutil.disk_usage(p.mountpoint) for p in partitions}
        time.sleep(1)

def update_load_avg():
    global load_avg
    while True:
        with lock:
            load_avg = psutil.getloadavg()[0]
        time.sleep(1)

def update_cpu_temp():
    global cpu_temp
    while True:
        with lock:
            try:
                cpu_temp = psutil.sensors_temperatures()['coretemp'][0].current
            except (KeyError, IndexError):
                cpu_temp = 0  # Bazı sistemlerde sıcaklık bilgisi bulunamayabilir
        time.sleep(1)

def update_battery():
    global battery_percent
    while True:
        with lock:
            try:
                battery_percent = psutil.sensors_battery().percent
            except AttributeError:
                battery_percent = 0  # Bataryası olmayan sistemlerde bu bilgi bulunamayabilir
        time.sleep(1)

# Veri toplama işlemleri için thread'leri başlat
t1 = threading.Thread(target=update_cpu_percent)
t2 = threading.Thread(target=update_virtual_memory)
t3 = threading.Thread(target=update_cpu_freq)
t4 = threading.Thread(target=update_network_io)
t5 = threading.Thread(target=update_disk_usage)
t6 = threading.Thread(target=update_load_avg)
t7 = threading.Thread(target=update_cpu_temp)
t8 = threading.Thread(target=update_battery)

t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t6.start()
t7.start()
t8.start()

# Grafik güncelleme fonksiyonu
def animate(i):
    with lock:
        # Pasta grafiği için veri
        cpu_data = [cpu_percent, 100 - cpu_percent]
        memory_data = [virtual_memory_percent, 100 - virtual_memory_percent]
        battery_data = [battery_percent, 100 - battery_percent]

        # Önceki grafikleri temizle
        plt.clf()

        plt.suptitle('System Analyzer Tool', fontsize=16)

        # CPU kullanımı pasta grafiği
        plt.subplot(3, 3, 1)
        plt.pie(cpu_data, labels=['Kullanılan', 'Boş'], autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff'])
        plt.title('CPU Kullanımı')

        # Bellek kullanımı pasta grafiği
        plt.subplot(3, 3, 2)
        plt.pie(memory_data, labels=['Kullanılan', 'Boş'], autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff'])
        plt.title('Bellek Kullanımı')

        # Disk kullanımı pasta grafiği
        plt.subplot(3, 3, 3)
        disk_labels = []
        disk_sizes = []
        for device, usage in disk_partitions_info.items():
            used = usage.used / (1024 * 1024)
            free = usage.free / (1024 * 1024)
            disk_labels.append(f"{device} - Kullanılan")
            disk_labels.append(f"{device} - Boş")
            disk_sizes.append(used)
            disk_sizes.append(free)
        plt.pie(disk_sizes, labels=disk_labels, autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff'])
        plt.title('Disk Kullanımı')

        # Ağ IO bilgisi
        plt.subplot(3, 3, 4)
        plt.axis('off')
        net_text = f"Ağ IO:\nGönderilen: {bytes_sent:.2f} Mbps\nAlınan: {bytes_recv:.2f} Mbps"
        plt.text(0.5, 0.5, net_text, ha='center', va='center', fontsize=12, wrap=True)

        # Sistem yük ortalaması
        plt.subplot(3, 3, 5)
        plt.axis('off')
        load_text = f"Sistem Yük Ortalaması (1 dk): {load_avg:.2f}"
        plt.text(0.5, 0.5, load_text, ha='center', va='center', fontsize=12, wrap=True)

        # CPU sıcaklığı
        plt.subplot(3, 3, 6)
        plt.axis('off')
        temp_text = f"CPU Sıcaklığı: {cpu_temp:.2f} °C"
        plt.text(0.5, 0.5, temp_text, ha='center', va='center', fontsize=12, wrap=True)

        # Batarya durumu
        plt.subplot(3, 3, 7)
        plt.pie(battery_data, labels=['Kullanılan', 'Boş'], autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff'])
        plt.title('Batarya Durumu')

        # Sistem bilgileri
        plt.subplot(3, 3, 8)
        plt.axis('off')
        sys_info_text = (
            f"Sistem: {system_info['platform']}\n"
            f"Sürüm: {system_info['platform_version']}\n"
            f"Yayın: {system_info['platform_release']}\n"
            f"Makine: {system_info['machine']}\n"
            f"İşlemci: {system_info['processor']}\n"
            f"CPU Çekirdekleri: {system_info['cpu_cores']}\n"
            f"Toplam Bellek: {system_info['memory']}"
        )
        plt.text(0.5, 0.5, sys_info_text, ha='center', va='center', fontsize=12, wrap=True)

        # Sayısal bilgiler
        plt.subplot(3, 3, 9)
        plt.axis('off')
        text = (
            f"CPU Frekansı: {cpu_freq:.2f} MHz\n"
            f"Kullanılan Bellek: {used_memory_mb:.2f} MB / {total_memory_mb:.2f} MB"
        )
        plt.text(0.5, 0.5, text, ha='center', va='center', fontsize=12, wrap=True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# Grafik oluşturma
fig = plt.figure(figsize=(12, 8))
ani = FuncAnimation(fig, animate, interval=1000)
plt.show()

# Ana program sona erdiğinde thread'lerin sonlanmasını sağla
t1.join()
t2.join()
t3.join()
t4.join()
t5.join()
t6.join()
t7.join()
t8.join()