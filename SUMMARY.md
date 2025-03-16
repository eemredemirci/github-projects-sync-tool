# GitHub Project Sync Tool - Project Summary

## About the Project

GitHub Project Sync Tool is a command-line tool that allows you to manage and synchronize GitHub Projects locally. With this tool, you can download GitHub projects in JSON and YAML formats, edit them locally, and send changes back to GitHub.

## What Has Been Done So Far

### Basic Infrastructure
- Interactive command-line interface (CLI) created
- GitHub API integration completed
- Multi-user support added
- User management (add, delete, set default) completed

### Cache Structure
- Repository cache created
- Project cache created
- Cache management and cleaning mechanisms added
- Cache structure unified (repository and project caches in separate files)

### Data Management
- GitHub project data fetching functionality completed
- JSON and YAML format data storage added
- File system organization completed

### User Interface Improvements
- Colored terminal output added
- Navigation system improved
- Error handling and user feedback improved
- Multilingual support (English and Turkish) added

## To Do

### GitHub-Local Change Detection
- Detect changes in local files
- Compare with changes on GitHub
- Show change summary to the user

### GitHub Upload Operations
- Test sending changes to GitHub
- Error handling
- Confirmation and feedback mechanisms

### Conflict Resolution
- Detect conflicts between local and remote changes
- Create conflict resolution interface
- Add automatic merge options

## Project Directory Structure

```
GitHub-Project-Sync-Tool/
├── app/                    # Main application package
│   ├── services/           # GitHub API and synchronization services
│   ├── utils/              # Helper functions
│   ├── interactive_cli.py  # Interactive command-line interface
│   └── __init__.py
├── data/                   # Data directory (in gitignore)
│   ├── projects/           # Project caches and local projects
│   ├── repositories/       # Repository caches
│   └── users/              # User information
├── .gitignore              # Files to be ignored by Git
├── LICENSE                 # MIT license
├── README.md               # Project description
├── CONTRIBUTING.md         # Contribution guide
├── requirements.txt        # Python dependencies
├── run.py                  # Application startup script
└── SUMMARY.md              # This summary file
```

## Cache Structure

The project uses the following cache structure for efficient operation:

1. **Repository Cache**:
   - Location: `data/repositories/{username}-repos-cache.json`
   - Content: All repositories of the user
   - Renewal: After 1 hour or when the token is changed

2. **Project Cache**:
   - Location: `data/projects/{username}-projects-cache.json`
   - Content: All projects of the user (v1 and v2)
   - Renewal: After 1 hour or when the token is changed

3. **Local Project Files**:
   - Location: `data/projects/{project_id}_{project_name}/`
   - Content: 
     - `project.json`: Latest project in JSON format
     - `project.yaml`: Latest project in YAML format
     - `project_{timestamp}.json`: Dated JSON backups
     - `project_{timestamp}.yaml`: Dated YAML backups

---

# GitHub Project Sync Tool - Proje Özeti

## Proje Hakkında

GitHub Project Sync Tool, GitHub Projects'i yerel olarak yönetmenize ve senkronize etmenize olanak tanıyan bir komut satırı aracıdır. Bu araç sayesinde GitHub projelerinizi JSON ve YAML formatında indirebilir, düzenleyebilir ve değişiklikleri GitHub'a gönderebilirsiniz.

## Şu Ana Kadar Yapılanlar

### Temel Altyapı
- Etkileşimli komut satırı arayüzü (CLI) oluşturuldu
- GitHub API entegrasyonu tamamlandı
- Çoklu kullanıcı desteği eklendi
- Kullanıcı yönetimi (ekleme, silme, varsayılan ayarlama) tamamlandı

### Önbellek (Cache) Yapısı
- Repository önbelleği oluşturuldu
- Proje önbelleği oluşturuldu
- Önbellek yönetimi ve temizleme mekanizmaları eklendi
- Önbellek yapısı tek bir yapıda birleştirildi (repository ve proje önbellekleri ayrı dosyalarda)

### Veri Yönetimi
- GitHub'dan proje verilerini çekme işlevi tamamlandı
- JSON ve YAML formatlarında veri saklama eklendi
- Dosya sistemi organizasyonu tamamlandı

### Kullanıcı Arayüzü İyileştirmeleri
- Renkli terminal çıktısı eklendi
- Navigasyon sistemi geliştirildi
- Hata yönetimi ve kullanıcı geri bildirimleri iyileştirildi
- Çoklu dil desteği (İngilizce ve Türkçe) eklendi

## Yapılacaklar

### GitHub-Lokal Değişiklik Kontrolü
- Yerel dosyalardaki değişiklikleri tespit etme
- GitHub'daki değişikliklerle karşılaştırma
- Değişiklik özetini kullanıcıya gösterme

### GitHub'a Gönderme İşlemleri
- Değişiklikleri GitHub'a gönderme işlemlerinin test edilmesi
- Hata durumlarının yönetimi
- Gönderim onayı ve geri bildirim mekanizmaları

### Çakışma Çözümleme
- Yerel ve uzak değişiklikler arasındaki çakışmaları tespit etme
- Çakışma çözümleme arayüzü oluşturma
- Otomatik birleştirme seçenekleri ekleme

## Proje Dizin Yapısı

```
GitHub-Project-Sync-Tool/
├── app/                    # Ana uygulama paketi
│   ├── services/           # GitHub API ve senkronizasyon servisleri
│   ├── utils/              # Yardımcı fonksiyonlar
│   ├── interactive_cli.py  # İnteraktif komut satırı arayüzü
│   └── __init__.py
├── data/                   # Veri dizini (gitignore'da)
│   ├── projects/           # Proje önbellekleri ve yerel projeler
│   ├── repositories/       # Repository önbellekleri
│   └── users/              # Kullanıcı bilgileri
├── .gitignore              # Git tarafından yok sayılacak dosyalar
├── LICENSE                 # MIT lisansı
├── README.md               # Proje açıklaması
├── CONTRIBUTING.md         # Katkıda bulunma rehberi
├── requirements.txt        # Python bağımlılıkları
├── run.py                  # Uygulamayı başlatma betiği
└── SUMMARY.md              # Bu özet dosyası
```

## Önbellek Yapısı

Proje, verimli çalışmak için aşağıdaki önbellek yapısını kullanır:

1. **Repository Önbelleği**:
   - Konum: `data/repositories/{username}-repos-cache.json`
   - İçerik: Kullanıcının tüm repository'leri
   - Yenilenme: 1 saat sonra veya token değiştiğinde

2. **Proje Önbelleği**:
   - Konum: `data/projects/{username}-projects-cache.json`
   - İçerik: Kullanıcının tüm projeleri (v1 ve v2)
   - Yenilenme: 1 saat sonra veya token değiştiğinde

3. **Yerel Proje Dosyaları**:
   - Konum: `data/projects/{project_id}_{project_name}/`
   - İçerik: 
     - `project.json`: En son JSON formatındaki proje
     - `project.yaml`: En son YAML formatındaki proje
     - `project_{timestamp}.json`: Tarihli JSON yedekleri
     - `project_{timestamp}.yaml`: Tarihli YAML yedekleri 