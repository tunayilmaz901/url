import os
import random
import requests
import time
from itertools import cycle
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from user_agent import generate_user_agent
from requests.adapters import HTTPAdapter

load_dotenv()
AYARLAR = {
    "VANITY_KOD": os.getenv("VANITY_URL"),
    "SUNUCU_ID": os.getenv("GUILD_ID"),
    "YETKI_TOKEN": os.getenv("TOKEN")
}

class VanityAvcisi:
    def __init__(self):
        self.hedef_vanity = AYARLAR["VANITY_KOD"]
        self.sunucu_id = AYARLAR["SUNUCU_ID"]
        self.yetki_token = AYARLAR["YETKI_TOKEN"]
        
        self.oturum = requests.Session()
        self.oturum.headers.update({
            "authorization": self.yetki_token,
            "user-agent": generate_user_agent()
        })
        self.oturum.mount("https://", HTTPAdapter(max_retries=2))
        
        self.veri_yuku = {"code": self.hedef_vanity}
        self.proxy_dongusu = cycle(self._proxyleri_al())
        self.guncel_proxy = next(self.proxy_dongusu)
        
    def _proxyleri_al(self):
        proxy_listesi = set()
        
        try:
            cevap = self._istek_yap("https://sslproxies.org/", "get", {})
            if isinstance(cevap, requests.Response):
                soup = BeautifulSoup(cevap.text, "lxml")
                tablo = soup.find("table", class_="table table-striped table-bordered")
                for satir in tablo.find_all("tr"):
                    hucreler = satir.find_all("td")
                    if len(hucreler) > 1:
                        proxy_listesi.add(f"{hucreler[0].text}:{hucreler[1].text}")
        except Exception as hata:
            print(f"{self._zaman_damgasi()} sslproxies'den proxy alınamadı: {hata}")
        
        try:
            cevap = self._istek_yap(
                "https://www.proxy-list.download/api/v1/get?type=https",
                "get",
                {}
            )
            if isinstance(cevap, str):
                for proxy in cevap.split("\n"):
                    if proxy.strip():
                        proxy_listesi.add(proxy.strip())
        except Exception as hata:
            print(f"{self._zaman_damgasi()} proxy-list'den proxy alınamadı: {hata}")
        
        proxyler = list(proxy_listesi)
        random.shuffle(proxyler)
        proxyler.append("son")
        return proxyler

    def _zaman_damgasi(self):
        return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

    def _istek_yap(self, adres, metod, proxyler):
        try:
            if metod == "get":
                return self.oturum.get(adres, timeout=5, proxies=proxyler, headers={"user-agent": generate_user_agent()})
            elif metod == "patch":
                return self.oturum.patch(adres, timeout=5, proxies=proxyler, headers=self.oturum.headers, json=self.veri_yuku)
        except requests.exceptions.Timeout:
            return f"Zaman aşımı - {self.guncel_proxy}"
        except requests.exceptions.ProxyError:
            return f"Proxy hatası - {self.guncel_proxy}"
        except requests.exceptions.SSLError:
            return f"SSL hatası - {self.guncel_proxy}"

    def vanity_degistir(self):
        adres = f"https://discord.com/api/v9/guilds/{self.sunucu_id}/vanity-url"
        cevap = self._istek_yap(adres, "patch", {"https": self.guncel_proxy})
        try:
            if isinstance(cevap, requests.Response):
                if cevap.status_code == 200:
                    print(f"{self._zaman_damgasi()} VANITY ALINDI: discord.gg/{self.hedef_vanity} başarıyla alındı!")
                    os._exit(1)
                else:
                    print(f"{self._zaman_damgasi()} discord.gg/{self.hedef_vanity} alınamadı! Durum Kodu: {cevap.status_code}")
            else:
                print(f"{self._zaman_damgasi()} Vanity değiştirme hatası: {cevap}")
        except Exception as hata:
            print(f"{self._zaman_damgasi()} Vanity değiştirme hatası: {hata}")

    def vanity_kontrol(self):
        adres = f"https://discord.com/api/v9/invites/{self.hedef_vanity}?with_counts=true&with_expiration=true"
        cevap = self._istek_yap(adres, "get", {"https": self.guncel_proxy})
        try:
            if isinstance(cevap, requests.Response):
                if cevap.status_code == 404:
                    print(f"{self._zaman_damgasi()} Proxy uygun, değiştirme deneniyor: {self.guncel_proxy}")
                    self.vanity_degistir()
                elif cevap.status_code == 200:
                    print(f"{self._zaman_damgasi()} Proxy çalışıyor: {self.guncel_proxy}, ancak URL hâlâ alınmış, 30 saniye bekleniyor")
                    time.sleep(30)
                    self.vanity_kontrol()
                elif cevap.status_code == 429:
                    print(f"{self._zaman_damgasi()} Proxy fazla istek yaptı: {self.guncel_proxy}")
                else:
                    print(f"{self._zaman_damgasi()} Durum kodu: {cevap.status_code} - Proxy: {self.guncel_proxy} - URL hâlâ alınmış")
            else:
                print(f"{self._zaman_damgasi()} Vanity kontrol hatası: {cevap}")
        except Exception as hata:
            print(f"{self._zaman_damgasi()} Vanity kontrol hatası: {hata}")

    def basla(self):
        while self.guncel_proxy != "son":
            self.vanity_kontrol()
            self.guncel_proxy = next(self.proxy_dongusu)
        VanityAvcisi().basla()

VanityAvcisi().basla()
