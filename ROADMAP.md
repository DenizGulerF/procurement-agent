# ProcureAI — Geliştirme Yol Haritası

Bu belge, projeyi gerçek bir fabrika/ERP kullanımına doğru adım adım geliştirmek için önerilen yol haritasını içerir.

---

## ✅ Tamamlananlar

- FastAPI + PostgreSQL + Docker altyapısı
- Domain modelleri (User, Product, Warehouse, Inventory, ProcurementRequest, AuditLog)
- Rol tabanlı yetkilendirme (EMPLOYEE / WAREHOUSE / PROCUREMENT / MANAGER)
- OpenAI-uyumlu LLM agent (tool calling loop)
- 7 agent tool: get_user, search_product, get_product, check_stock, find_product_locations, create_procurement_request, get_procurement_request
- İnsan onayı zorunluluğu (PENDING_PROCUREMENT → APPROVED/REJECTED)
- Audit loglama
- 31 pytest testi

---

## 📋 Yapılacaklar (Önerilen Sıra)

### 1. Yeni ürün ekleme — `create_product`

**Motivasyon:** Şu an veritabanında kayıtlı olmayan bir ürün için procurement açılamıyor. Gerçek kullanımda yeni malzemeler sürekli ekleniyor.

**Yapılacaklar:**
- [x] `product_service.create_product(sku, name, unit, description)` servisi
- [x] `create_product` agent tool'u
- [x] `POST /products` API endpoint'i
- [x] Test: yeni ürün oluşturma → procurement açma akışı

**Beklenen davranış:**
```
"Siemens S7-1200 PLC lazım, hiç almamıştık"
→ search_product → bulunamadı
→ create_product(sku="SIEM-S7-1200", name="Siemens S7-1200 PLC", unit="piece")
→ create_procurement_request(...)
→ PENDING_PROCUREMENT
```

---

### 2. Procurement talebi iptal etme — `cancel_procurement_request`

**Motivasyon:** Yanlış açılan veya ihtiyaç kalmayan talepleri geri çekebilmek gerekiyor.

**Yapılacaklar:**
- [x] `CANCELLED` status'u `ProcurementStatus` enum'una ekle
- [x] `cancel_procurement_request` servisi (sadece talep sahibi veya MANAGER iptal edebilir)
- [x] `cancel_procurement_request` agent tool'u
- [x] `POST /procurement/requests/{id}/cancel` API endpoint'i
- [x] Test: EMPLOYEE kendi talebini iptal edebilir, başkasınınkini edemez

**Beklenen davranış:**
```
"1 numaralı talebimi iptal et"
→ get_procurement_request(1)
→ cancel_procurement_request(request_id=1, user_id=1)
→ CANCELLED
```

---

### 3. Stok güncelleme — `update_stock`

**Motivasyon:** Şu an stok sadece seed data ile geliyor. Gerçekte mal gelince veya kullanılınca stok değişmesi lazım.

**Yapılacaklar:**
- [ ] `inventory_service.update_stock(product_id, warehouse_location_id, quantity_delta)` servisi
- [ ] `POST /inventory/{product_id}/receive` endpoint'i (mal kabul)
- [ ] WAREHOUSE rolü bu işlemi yapabilmeli
- [ ] Her stok değişikliği audit log'a yazılmalı
- [ ] Test: mal kabul → stok artışı → audit kaydı

---

### 4. Reorder Point — Otomatik stok uyarısı

**Motivasyon:** Stok kritik seviyenin altına düştüğünde sistem kendiliğinden uyarı versin veya procurement önersin.

**Yapılacaklar:**
- [ ] `Product` modeline `min_stock` alanı ekle
- [ ] `GET /inventory/low-stock` endpoint'i (min_stock altındaki ürünler)
- [ ] `check_reorder_points()` servis fonksiyonu
- [ ] Agent tool: `find_low_stock_items`
- [ ] Cron-friendly endpoint veya startup task

---

### 5. Tedarikçi yönetimi — `Supplier`

**Motivasyon:** Agent "bu ürün için en hızlı tedarikçi kim?" sorusunu cevaplayabilsin.

**Yapılacaklar:**
- [ ] `Supplier` modeli: id, name, contact_email, lead_time_days
- [ ] `ProductSupplier` ilişki tablosu: product_id, supplier_id, unit_price
- [ ] `GET /suppliers`, `GET /products/{id}/suppliers` endpoint'leri
- [ ] `find_product_suppliers` agent tool'u
- [ ] Test: ürün için tedarikçi listesi, en hızlı tedarikçi sorgulama

---

### 6. Raporlama endpoint'leri

**Motivasyon:** Yöneticilerin sistemin genel durumunu görebilmesi için.

**Yapılacaklar:**
- [ ] `GET /reports/top-requested` — en çok talep edilen ürünler (son 30 gün)
- [ ] `GET /reports/pending-summary` — bekleyen taleplerin özeti
- [ ] `GET /reports/low-stock` — kritik stok altındaki ürünler
- [ ] Bu endpoint'leri wrap eden agent tool'ları
- [ ] Örnek: "Bu ay en çok ne talep edildi?" sorusu cevaplanabilir

---

## Notlar

- Her özellik kendi branch'inde geliştirilebilir
- Her adımın sonunda testler çalıştırılmalı (`pytest`)
- Yeni tool eklendikçe README güncellenmeli
- Business logic her zaman servis katmanında kalmalı — LLM'e bırakılmamalı
