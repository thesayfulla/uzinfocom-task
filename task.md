Task: Concurrent Order & Inventory Reservation Service (til erkin)

Kontekst: Mini marketplace uchun buyurtma va ombor boshqaruvchi backend service. til, 
framework, kutubxona — ixtiyoringizda. 
Yagona shart: HTTP API orqali ishlashi va Docker'da ko'tarilishi kerak.

Funktsional talablar: <br>
POST /products — mahsulot yaratish (name, price, stock_quantity) <br>
POST /orders — bir nechta item'li buyurtma, Idempotency-Key header majburiy 
(bir xil key bilan qayta yuborilsa, stock ikkinchi marta kamaymasligi kerak)<br>
GET /orders/{id} — status: pending → confirmed / cancelled <br>
POST /orders/{id}/cancel — reserved stock qaytarilishi kerak <br>

authorization jwt token bolsin.

Fon jarayon: 15 daqiqa ichida to'lanmagan pending buyurtmalar avtomatik bekor qilinishi.


Texnik talablar:

Ma'lumotlar bazasi:
PostgreSQL majburiy va sql query qolda yozilishi shart orm ishlatilmasin.
redis orqali keshlansin va caching strategylarni ham yoritsin

Concurrency correctness: 50 ta parallel so'rov bitta productga (stock=10) yuborilganda,
 aynan 10 tasi muvaffaqiyatli bo'lishi kerak — qolgani 409/422 bilan qaytishi kerak.

Arxitektura: qatlamlarga ajratilgan bo'lishi (example: handler/controller → service → repository) 

Docker: docker-compose.yml bilan bitta buyruqda ko'tarilishi va standart portda (masalan :8080) ishlashi shart

AI ishlatilmasligi kerak va har bir decision imkoni bolsa readme da yoritilsin. 

database schemalar ham yaratilsin dbdiagram.io sayti orqali tablitsalarni architecturasi qoyilsin.

githubda public repoda bolishi va har bir qilingan ishlarni committa aytib otilishi shart commit historyga qaraladi!!!