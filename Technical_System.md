# GitHub Proje Senkronizasyon Aracı - Teknik Sistem Dokümantasyonu

Bu doküman, GitHub Proje Senkronizasyon Aracının teknik mimarisini, temel bileşenlerini ve bunların birbirleriyle nasıl etkileşime girdiğini açıklamaktadır.

## Genel Mimari

GitHub Proje Senkronizasyon Aracı, GitHub Projeleri v2 ile yerel dosya sistemi arasında çift yönlü senkronizasyon sağlayan bir araçtır. Araç, şu temel modüllerden oluşur:

1. **ChangeTracker**: Yerel değişiklikleri izler
2. **ChangeReviewer**: Değişiklikleri gözden geçirme ve onaylama süreci sağlar
3. **OperationList**: Onaylanan değişikliklerin GitHub'a gönderilmesi için operasyon listesi oluşturur
4. **GitHubSynchronizer**: Operasyonları GitHub API'sine iletir

## ChangeTracker

### Amaç
ChangeTracker, yerel dosya sistemindeki değişiklikleri izleyerek GitHub ile senkronize edilmesi gereken değişiklikleri tespit eder.

### Çözdüğü Sorunlar
- Yerel dosya sistemindeki değişikliklerin otomatik tespiti
- GitHub'dan indirilen verilerin orijinal durumunun korunması
- Değişiklik tiplerinin (ekleme, güncelleme, silme) doğru şekilde kategorize edilmesi
- Milestone ve Issue/PR öğelerinin yapılandırılmış bir hiyerarşide yönetilmesi

### Çalışma Prensibi
1. **Orijinal Durum Yakalama**: GitHub'dan indirilen veriler, referans olarak kaydedilir
2. **Mevcut Durum Tarama**: Yerel dosya sistemi periyodik olarak taranır
3. **Değişiklik Tespiti**: Orijinal durum ile mevcut durum arasındaki farklar tespit edilir
4. **Parmak İzi Karşılaştırma**: Her öğe için benzersiz bir parmak izi (fingerprint) oluşturulur ve bu değerler karşılaştırılır
5. **Spesifik Alan Değişiklikleri**: Değişen alanların detaylı listesi çıkarılır

```python
def detect_changes(self) -> Dict:
    """Orijinal durum ile mevcut durum arasındaki farkları tespit eder"""
    # Değişiklikler: eklenen, güncellenen, silinen öğeler
    changes = {"created": [], "updated": [], "deleted": []}
    
    # 1. Eklenen öğeleri tespit et (şimdi var, önce yoktu)
    # 2. Güncellenen öğeleri tespit et (her ikisinde de var ama içerik farklı)
    # 3. Silinen öğeleri tespit et (önce vardı, şimdi yok)
    
    return changes
```

## ChangeReviewer

### Amaç
ChangeReviewer, tespit edilen değişikliklerin kullanıcı tarafından gözden geçirilmesini ve onaylanmasını sağlar.

### Çözdüğü Sorunlar
- İstenmeyen veya yanlışlıkla yapılan değişikliklerin GitHub'a yansıtılmasını engelleme
- Değişikliklerin görselleştirilmesi ve kolay anlaşılması
- Değişiklikleri tek tek veya toplu olarak onaylama imkanı
- Değişiklik operasyonlarının onay sonrası yönetimi

### Çalışma Prensibi
1. **Değişiklik Listeleme**: ChangeTracker'dan gelen değişiklikler kategorize edilir
2. **Detay Görüntüleme**: Her değişikliğin ayrıntıları (eski/yeni değerler) gösterilir
3. **Onay Mekanizması**: Kullanıcı değişiklikleri onaylayabilir veya reddedebilir
4. **Operasyon Listesi Oluşturma**: Onaylanan değişiklikler için GitHub operasyonları oluşturulur

```python
def approve_change(self, change_type: str, index: int) -> bool:
    """Belirli bir değişikliği onaylar"""
    # 1. Değişikliği bul
    # 2. Onay listesine ekle
    # 3. Operasyon listesini güncelle
```

## OperationList

### Amaç
OperationList, onaylanan değişiklikleri GitHub API'sine gönderilecek operasyonlara dönüştürür ve bu operasyonların durumunu takip eder.

### Çözdüğü Sorunlar
- GitHub API operasyonlarının organizasyonu ve sıralanması
- Operasyon durumlarının (beklemede, tamamlandı, başarısız) takibi
- Başarısız operasyonların yeniden denenmesi
- Operasyon günlüğünün tutulması

### Çalışma Prensibi
1. **Operasyon Dönüşümü**: Değişiklikler, GitHub API'sine uygun operasyonlara çevrilir
2. **Durum Takibi**: Her operasyonun durumu izlenir
3. **Hata Yönetimi**: Başarısız operasyonlar için hata raporları oluşturulur
4. **Senkronizasyon Geçmişi**: Tamamlanan operasyonlar senkronizasyon geçmişine kaydedilir

```python
def add_operation(self, change_type: str, item_type: str, data: Dict) -> str:
    """Operasyon listesine yeni bir operasyon ekler"""
    # 1. Operasyon tipini belirle (create, update, delete)
    # 2. Öğe tipini belirle (issue, milestone)
    # 3. Operasyon verilerini hazırla
    # 4. Operasyonu listeye ekle ve ID döndür
```

## GitHubSynchronizer

### Amaç
GitHubSynchronizer, onaylanan değişiklikleri GitHub API'sine iletir ve senkronizasyon sürecini yönetir.

### Çözdüğü Sorunlar
- GitHub GraphQL ve REST API ile iletişim
- API hız sınırlarının yönetimi
- İndirilen ve gönderilen verilerin doğruluğunun sağlanması
- Senkronizasyon hatalarının yönetimi ve geri bildirim

### Çalışma Prensibi
1. **API İletişimi**: GitHub GraphQL ve REST API'leri ile iletişim kurulur
2. **Operasyon İşleme**: Operasyon listesindeki işlemler sırayla gerçekleştirilir
3. **Sonuç Doğrulama**: Her operasyonun sonucu doğrulanır
4. **Durum Güncellemesi**: Operasyon durumları güncellenir

```python
def execute_operation(self, operation: Dict) -> bool:
    """Bir operasyonu GitHub API'sine gönderir"""
    # 1. Operasyon tipine göre API çağrısı hazırla
    # 2. API çağrısını gerçekleştir
    # 3. Sonucu kontrol et
    # 4. Operasyon durumunu güncelle
```

## Veri Akışı

1. **GitHub → Yerel**: İndirme süreci
   - GitHub API'sinden proje verileri alınır
   - Veriler, yapılandırılmış bir dosya hiyerarşisine dönüştürülür
   - Orijinal durum kaydedilir

2. **Yerel → GitHub**: Yükleme süreci
   - Yerel değişiklikler ChangeTracker ile tespit edilir
   - Değişiklikler ChangeReviewer ile onaylanır
   - Onaylanan değişiklikler için OperationList operasyonlar oluşturur
   - GitHubSynchronizer operasyonları GitHub'a iletir

## Dosya Yapısı

```
proje/
  ├── project.json            # Ana proje verisi
  ├── project.yaml            # YAML formatında proje verisi
  ├── milestones/             # Milestone klasörü
  │   ├── milestone_adı/      # Her milestone için bir klasör
  │   │   ├── milestone.json  # Milestone bilgileri
  │   │   ├── issue_1.json    # Bu milestone'a ait issue
  │   │   ├── issue_2.json    # Bu milestone'a ait başka bir issue
  │   │   └── issue_3_parent/ # Parent issue'lar için klasör
  │   │       └── issue_4.json # Child issue'lar bu klasörde
  │   └── no_milestone/       # Milestone olmayan issue'lar burada
  ├── .cache/                 # Önbellek klasörü
  │   └── original_state.json # Orijinal durum verisi
  ├── .pending/               # Bekleyen operasyonlar klasörü
  ├── logs/                   # Günlük dosyaları klasörü
  └── sync_history/           # Senkronizasyon geçmişi klasörü
```

## Başlıca Zorluklar ve Çözümleri

### 1. Öğe Eşleştirme
**Zorluk**: GitHub'daki öğeler ile yerel dosyalar arasında tutarlı eşleştirme sağlamak
**Çözüm**: Her öğe için benzersiz ID'ler ve normalleştirilmiş başlıklar

### 2. Değişiklik Tespiti
**Zorluk**: Gerçek değişiklikleri doğru şekilde tespit etmek
**Çözüm**: Özelleştirilmiş parmak izi algoritması ve alan bazlı karşılaştırma

### 3. Hata Toleransı
**Zorluk**: Senkronizasyon sırasında oluşan hataları yönetmek
**Çözüm**: Operasyon durumu izleme ve yeniden deneme mekanizmaları

### 4. Kullanıcı Deneyimi
**Zorluk**: Karmaşık bir süreci kullanıcı dostu hale getirmek
**Çözüm**: Aşamalı onay süreci ve detaylı geribildirim mekanizmaları

## Sonuç

Bu teknik mimari, GitHub Projeleri ile yerel dosya sistemi arasında güvenilir, hızlı ve kullanıcı dostu bir senkronizasyon sağlar. Modüler yapısı sayesinde sistemin farklı bileşenleri bağımsız olarak geliştirilebilir ve test edilebilir. 