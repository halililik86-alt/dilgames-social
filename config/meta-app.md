# Meta uygulaması: DilGame Social Studio

App ID: `1674033130957286` · Mod: **Geliştirme** (yalnızca hesap sahibi kullandığı için uygulama incelemesi gerekmez)

## Amaç (dar tutulur)
Yalnızca **kendi** Instagram işletme hesabımıza Reels yayınlamak ve **kendi** gönderilerimizin istatistiklerini okumak. Mesajlaşma, yorum yönetimi, reklam ve başka hesaplara erişim kapsam dışıdır.

## Kullanım durumu
- **Instagram API → API setup with Facebook login** (video doğrudan yüklenir; herkese açık barındırma gerekmez)
- Facebook Login for Business yapılandırması: **DilGame Instagram Publishing** (`2087998005153480`)

## İzinler
| İzin | Neden |
|---|---|
| `instagram_basic` | Hesap kimliği ve medya listesi |
| `instagram_content_publish` | Reels yayınlama |
| `instagram_manage_insights` | Haftalık rapor (izlenme, erişim, kayıt, paylaşım) |
| `pages_show_list`, `pages_read_engagement` | Bağlı Facebook Sayfasını ve sayfa anahtarını bulmak |
| `business_management` | Sayfa/hesap işletme portföyündeyse erişim |

Eklenmeyecekler: `instagram_manage_messages`, `instagram_manage_comments`, `ads_*`, `instagram_manage_engagement`.

## Anahtar
- Graph API Explorer → kullanıcı anahtarı (yukarıdaki izinlerle) → **Access Token Tool → Extend** → `me/accounts?fields=name,instagram_business_account,access_token`
- Uzun ömürlü kullanıcı anahtarından alınan **sayfa anahtarı süresizdir** → GitHub secret `IG_ACCESS_TOKEN`
- `instagram_business_account.id` → GitHub secret `IG_USER_ID`
- Anahtarlar yalnızca GitHub Secrets'ta durur; sohbete, koda ya da Claude ajanlarına verilmez.
