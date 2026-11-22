---
name: dikey-animasyon
description: Dikey (9:16, 1080x1920) seslendirmeli animasyon videosu üretir. Shorts, Reels ve TikTok için. Satış danışmanı skeçleri, müşteri komedisi, satış ipuçları ve mobil oyun tanıtım videoları. Konu verilince senaryoyu yazar, ElevenLabs ile Türkçe seslendirir, karakterli animasyonu ve kelime kelime altyazıyı oluşturur, MP4 teslim eder. Tetikleyiciler: animasyon videosu, shorts yap, reels yap, tiktok videosu, satış danışmanı videosu, oyun tanıtım videosu, dikey video.
---

# Dikey Animasyon Videosu

Tek komutla şu zinciri çalıştırır: **konu → senaryo JSON → ElevenLabs Türkçe ses → animasyon (Playwright) → MP4 (ffmpeg)**.

Bu skill'in kullandıkları:
- `scripts/uret.py` (ana komut)
- `scripts/sahne.html` (çizim ve animasyon motoru)
- `scripts/kaydet.js` (kare kare kayıt)

Ortamda gereken araçlar: python3, node + playwright (Chromium), ffmpeg. `api.elevenlabs.io` proxy üzerinden bağlı olmalı (anahtar gerekmez).

## İş akışı

1. **Konuyu netleştir.** Video tipi şunlardan biri: satış skeci, satış ipucu ya da oyun tanıtımı. Oyun tanıtımı içinse kullanıcıdan **dikey ekran görüntüleri** ve **uygulama ikonu** iste. Yoksa ikon yerine emoji kullan.
2. **Senaryoyu yaz.** Senaryo bir JSON dosyası olur (format aşağıda). Kullanıcı tersini söylemedikçe sor-bekle yapma, direkt yaz. Senaryoyu çıktı klasörüne kaydet.
3. **Önizle (karakter harcamaz):**
   `python3 scripts/uret.py senaryo.json CIKTI --sessiz --onizleme`
   Her sahneden bir PNG çıkar. Kareleri `ffmpeg -pattern_type glob -i 'CIKTI/kare_*.png' -vf "scale=360:640,tile=4x2" sheet.png` ile tek resimde birleştir. Read ile bak; taşma ya da üst üste binme varsa düzelt.
4. **Tam videoyu üret:**
   `python3 scripts/uret.py senaryo.json CIKTI`
   30 saniyelik video yaklaşık 1 dakikada çıkar. Sesler `CIKTI/.ses/` klasöründe önbelleğe alınır. Aynı cümleyi tekrar üretmek karakter harcamaz.
5. **Teslim et.** Çıkan `.mp4` ve `_kapak.jpg` dosyalarını SendUserFile ile gönder. `youtube-video-paketi` skill'i varsa başlık, açıklama ve etiket önerisini de ekle.

**ElevenLabs kotası:** Ücretsiz plan ayda 10.000 karakter. Yalnızca `soz` alanları sayılır. 30 saniyelik bir video yaklaşık 350–450 karakter tutar. Toplam karakteri `python3 -c` ile say ve kullanıcıya söyle. Kota bilgisi için `curl -s https://api.elevenlabs.io/v1/user/subscription -H "xi-api-key: proxy"` (`character_count` / `character_limit`).

API hata verirse o satır otomatik olarak sessiz geçer ve süresi tahmin edilir. Bu durumu kullanıcıya bildir. Kütüphane sesleri (ör. Türk aksanlı "Emrullah") ücretsiz planda API'den **çalışmaz**. Yalnızca aşağıdaki hazır sesler kullanılabilir.

## Senaryo formatı

```json
{
  "baslik": "Dosya adi icin",
  "kanal": "@kanaladi",
  "renk": "#e63946",
  "vurgu": "#FFD93D",
  "anlatici_ses": "liam",
  "ses_ayar": {"hiz": 1.0, "stability": 0.4, "style": 0.35},
  "muzik": "opsiyonel/muzik.mp3", "muzik_ses": 0.12,
  "karakterler": {
    "danisman": {"tip": "danisman", "ad": "Danışman Kemal"},
    "musteri":  {"tip": "musteri", "ad": "Müşteri", "ses": "liam"}
  },
  "sahneler": [ ... ]
}
```

Alanların anlamı:
- `renk`: düz ve patlama arka planlarının rengi.
- `vurgu`: altyazıda o an söylenen kelimenin rengi, ayrıca buton ve ilerleme çubuğu rengi.
- `anlatici_ses`: karakter dışı sahneleri (başlık, liste, oyun, kapanış) seslendiren ses.
- `ses_ayar.hiz`: konuşma hızı, 0.7 ile 1.2 arası.

### Karakterler
`tip` alanı hazır bir kalıbı seçer. Kalıbın her alanı tek tek değiştirilebilir.

| tip | görünüm | varsayılan ses |
|---|---|---|
| `danisman` | lacivert takım, kırmızı kravat, yana taranmış saç | chris |
| `musteri` | yeşil kapüşonlu | liam |
| `musteri_kadin` | uzun saç, turuncu tişört | jessica |
| `patron` | kel, bıyıklı, siyah takım | brian |
| `stajyer` | kıvırcık saç, gözlük, sarı tişört | will |
| `oyuncu` | mor kapüşonlu, gözlük | liam |

Değiştirilebilir alanlar:
- `ad`
- `ses`
- `ten`, `sac_renk`, `giysi_renk`, `pantolon`, `kravat`: renkler (hex)
- `sac`: `kisa`, `yana`, `uzun`, `kivircik` veya `kel`
- `giysi`: `takim`, `kapusonlu` veya `tisort` (tişört için `yazi` alanı göğse yazı yazar)
- `gozluk`, `biyik`: true/false

Sesler (hepsi Türkçe konuşabilir, aksan hafif yabancı):
- **Erkek:** chris, liam, will, brian, eric, adam, charlie, george, callum, roger, daniel, bill, harry
- **Kadın:** jessica, sarah, laura, bella, matilda, alice, lily
- **Nötr:** river

### Sahne tipleri
Her sahnede `soz` alanı seslendirilecek metindir. Sahne süresi sese göre otomatik ayarlanır. `sure` ile alt sınır verilebilir.

- **`baslik`** (giriş kancası): Alanları `yazi` (büyük başlık), `emoji` ve `alt`. Arka plan dönen ışınlardır. Bu sahnede altyazı çıkmaz, yazı kelime kelime gelir.
- **`dialog`**: Alanları şunlar:
  - `sahnede`: sahnedeki karakterler, en fazla 3 kişi (ör. `["danisman","musteri"]`).
  - `konusan`: konuşan karakter.
  - `duygu`: konuşanın yüz ifadesi.
  - `duygular`: diğer karakterlerin ifadesi, `{"musteri":"uzgun"}` gibi.
  - `emoji`: konuşanın başının üstünde patlar.
  - `efekt`: `zoom` konuşana yaklaşır, `sallan` ekranı sarsar.
  - `arkaplan`: `ofis`, `galeri`, `magaza`, `duz` veya `patlama`. Galeri için `tabela` metni ve `araba_renk` verilebilir.
  - `yazi`: üstte sabit başlık (opsiyonel).
  - Konuşan karakterin ağzı sese göre oynar, söylenen kelime altyazıda sarı yanar. Bir önceki sahnede olmayan karakter yandan kayarak girer.
- **Duygular:** `normal`, `mutlu`, `sasirmis`, `kizgin`, `supheli`, `uzgun`, `sinsi`.
- **`liste`**: Alanları `yazi` (başlık) ve `maddeler` (en fazla 5, her biri kısa). Her madde, anlatıcı onun ilk kelimesini söylediği anda kart olarak kayar gelir. Bunun için maddelerin ilk kelimesi `soz` içinde aynen geçmeli.
- **`oyun`**: Alanları şunlar:
  - `gorseller`: ekran görüntüleri, senaryo dosyasına göre göreli yol. Dikey olanlar en iyi sonucu verir.
  - `yazi`: üst başlık.
  - `etiket`: köşede sallanan rozet, ör. "ÜCRETSİZ".
  - Görseller telefon çerçevesinde yavaş zoom ile değişir.
  - Video klip desteklenmez. Klip varsa `ffmpeg -ss 3 -i klip.mp4 -frames:v 1 ss.png` ile kare çıkar.
- **`kapanis`**: Alanları şunlar:
  - `gorsel`: uygulama ikonu. Yoksa `emoji` kullanılır.
  - `yazi`, `alt`.
  - `buton`: varsayılan "TAKİP ET".
  - Sahnede ding sesi ve el işareti vardır.

Ses efektleri otomatik eklenir: sahne geçişinde whoosh, emoji, rozet ve liste maddelerinde pop, kapanışta ding. `muzik` verilirse arkada kısık çalar ve sonda kısılarak biter. Müziği kullanıcı vermeli; telifsiz olduğundan emin olsun.

## Senaryo yazma kuralları

- **İlk 2 saniye kanca.** `baslik` sahnesi merak uyandırmalı ya da tanıdık bir durumu yakalamalı. Örnekler: "Satış danışmanına asla bunu söyleme", "Bu oyunu bırakamazsın".
- **Toplam 20–40 saniye, 6–9 sahne.** Her `soz` 1–2 kısa cümle olsun. Uzun cümleler altyazıyı ve ritmi bozar.
- **Konuşma dili kullan.** Rakamları yazıyla yaz: "beş dakika". TTS rakamı bazen İngilizce okur. Kısaltma kullanma.
- **Satış skeçleri:** tanıdık durum → müşteri itirazı → danışmanın abartılı ya da zekice cevabı (`sinsi` + `zoom`) → müşteri tepkisi (`sasirmis` + `sallan`) → punchline. İstenirse sonuna "şaka bir yana" + `liste` ile gerçek bir ipucu ekle. Videoya değer katan kısım bu ipucudur. En sonda yorum isteyen bir `kapanis` olsun.
  Konu fikirleri:
  - "sadece bakıyorum" diyen müşteri
  - "eşime bir sorayım"
  - "internette daha ucuz"
  - indirim pazarlığı
  - ay sonu kotası
  - patron ve stajyer
  - ilk gün çaylak danışman
  - itiraz karşılama teknikleri
  - kapanış cümleleri
- **Oyun tanıtımı:** kanca (meydan okuma ya da soru) → `oyun` sahneleri (mekanik, ödül, zorluk) → oyuncu karakterin komik tepkisi → `kapanis` (ikon + "İndir").
- **Telif:** Gerçek marka, ünlü ya da başka bir oyunun karakterini kullanma. Karakterler bu motorun kendi çizimleridir.
- **Dikkat edilecekler:**
  - Bütün yazılar otomatik büyük harfe çevrilir (Türkçe İ/ı kurallarına uygun).
  - Alt kısımdaki ~300 piksel Shorts arayüzünün altında kalır. Önemli içerik orada yer almaz.

## Hazır örnekler
- `ornekler/satis-danismani.json`: "Sadece bakıyorum" skeci + 3 kural listesi, yaklaşık 32 saniye, ~380 karakter.
- `ornekler/oyun-tanitim.json`: oyun tanıtım şablonu. `ss1.png`, `ss2.png` ve `ikon.png` dosyalarını kullanıcının görselleriyle değiştir.
