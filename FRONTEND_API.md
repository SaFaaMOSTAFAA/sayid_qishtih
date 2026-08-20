# Frontend Agent Report — السيد قشطة Dashboard API

Backend P0 is implemented. Use this contract to build the dashboard SPA.

## Base URL & locale

All routes are language-prefixed via Django `i18n_patterns`:

| Environment | Example base |
|-------------|--------------|
| Local | `http://localhost:8000/en` or `http://localhost:8000/ar` |
| Production | `https://<host>/en` or `https://<host>/ar` |

Swagger: `{base}/api/docs/`  
Schema: `{base}/api/schema/`

Send media/multipart for image uploads (`Content-Type: multipart/form-data`).

---

## Auth (staff dashboard)

Staff users must have `is_staff=True` in Django.

| Method | Path | Auth | Body / notes |
|--------|------|------|--------------|
| `POST` | `/api/auth/login/` | Public | `{ "username", "password" }` → `{ "access", "refresh" }` |
| `POST` | `/api/auth/refresh/` | Public | `{ "refresh" }` → `{ "access" }` |
| `GET` | `/api/auth/me/` | Bearer | Current user summary |
| `POST` | `/api/auth/register/` | Public | Exists; **do not use for dashboard** — create staff via Django admin |

### Headers

```http
Authorization: Bearer <access_token>
Accept-Language: ar   # or en
```

### Permission rules (important)

| Resource | Public | Staff JWT |
|----------|--------|-----------|
| Products / Categories / Offers **GET** | Yes | Yes (staff see hidden products & inactive offers) |
| Products / Categories / Offers **POST/PUT/PATCH/DELETE** | No (403) | Yes |
| Dashboard stats | No | Yes (`IsAdminUser`) |
| Contact **POST** | Yes (site form) | Yes |
| Contact **GET / DELETE** | No | Yes |

---

## 1. Dashboard stats

`GET /products/dashboard/stats/`  
**Auth:** staff only

### Response `200`

```json
{
  "total_products": 12,
  "available_products": 9,
  "unavailable_products": 3,
  "current_offers": 2
}
```

| Field | Meaning |
|-------|---------|
| `total_products` | All products |
| `available_products` | `is_available=true` |
| `unavailable_products` | Out of stock / `is_available=false` |
| `current_offers` | `is_active=true` and within optional date window (or open-ended) |

---

## 2. Categories

Base: `/products/categories/`

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/products/categories/` | Public |
| `GET` | `/products/categories/{id}/` | Public |
| `POST` | `/products/categories/` | Staff |
| `PUT` / `PATCH` | `/products/categories/{id}/` | Staff |
| `DELETE` | `/products/categories/{id}/` | Staff |

### Fields

```json
{
  "id": 1,
  "name": "Dairy",
  "name_ar": "ألبان",
  "display_order": 0
}
```

- List is ordered by `display_order`, then `id`.
- To reorder: `PATCH` each category with the new `display_order`.

### Create example

```json
{
  "name": "Cheese",
  "name_ar": "جبن",
  "display_order": 1
}
```

---

## 3. Products

Base: `/products/products/`

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/products/products/` | Public (only `is_visible=true`) |
| `GET` | `/products/products/{id}/` | Public (visible only unless staff) |
| `POST` | `/products/products/` | Staff |
| `PUT` / `PATCH` | `/products/products/{id}/` | Staff |
| `DELETE` | `/products/products/{id}/` | Staff |

### Fields

```json
{
  "id": 1,
  "name": "Eshta",
  "name_ar": "قشطة",
  "description": "...",
  "description_ar": "...",
  "price": "25.00",
  "image": "/media/products/....jpg",
  "category": 1,
  "quantity": 10,
  "is_visible": true,
  "is_available": true,
  "display_order": 0,
  "created_at": "2026-07-25T20:00:00Z"
}
```

| Field | Notes |
|-------|-------|
| `is_visible` | Hide/show on storefront |
| `is_available` | `false` = Out of Stock |
| `quantity` | When set to `0`, backend forces `is_available=false` |
| `display_order` | Lower first |
| `image` | File upload; nullable |

### Query params (staff + public)

| Param | Example | Notes |
|-------|---------|-------|
| `category` / `category_id` | `?category=1` | Filter by category id |
| `category_name` | `?category_name=Dairy` | Exact name (case-insensitive) |
| `is_available` | `?is_available=true` | Filter stock status |
| `is_visible` | `?is_visible=false` | **Staff only** |

### Dashboard UI actions mapping

| UI action | API |
|-----------|-----|
| Add product | `POST` multipart/JSON |
| Edit product | `PUT` / `PATCH` |
| Delete product | `DELETE` |
| Hide / show | `PATCH { "is_visible": false \| true }` |
| Mark out of stock | `PATCH { "is_available": false }` or `{ "quantity": 0 }` |
| Restock | `PATCH { "quantity": 5, "is_available": true }` |

---

## 4. Offers (banners / ads)

Base: `/products/offers/`

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/products/offers/` | Public → only currently active offers |
| `GET` | `/products/offers/{id}/` | Public (if currently active) / Staff (any) |
| `POST` | `/products/offers/` | Staff |
| `PUT` / `PATCH` | `/products/offers/{id}/` | Staff |
| `DELETE` | `/products/offers/{id}/` | Staff |

### Fields

```json
{
  "id": 1,
  "title": "Ramadan Offer",
  "title_ar": "عرض رمضان",
  "description": "20% off",
  "description_ar": "خصم 20٪",
  "image": "/media/offers/....jpg",
  "is_active": true,
  "start_date": "2026-07-01",
  "end_date": "2026-07-31",
  "is_currently_active": true,
  "created_at": "2026-07-25T20:00:00Z"
}
```

| Field | Notes |
|-------|-------|
| `is_active` | Manual on/off |
| `start_date` / `end_date` | Optional (`YYYY-MM-DD`); omit or `null` for open-ended |
| `is_currently_active` | Read-only: active flag **and** inside date window |
| `image` | Banner image |

### Staff query

`GET /products/offers/?is_active=true` — filter by flag (staff only).

### Activate / deactivate

```http
PATCH /products/offers/{id}/
{ "is_active": false }
```

---

## 5. Contact messages

Base: `/api/contact-us/`

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/api/contact-us/` | Public (website form) |
| `GET` | `/api/contact-us/` | Staff |
| `GET` | `/api/contact-us/{id}/` | Staff |
| `DELETE` | `/api/contact-us/{id}/` | Staff |

`PUT` / `PATCH` are **not** allowed.

### Fields

```json
{
  "id": 1,
  "name": "Ahmed",
  "name_ar": null,
  "phone_number": "01000000000",
  "message": "Hello",
  "message_ar": null,
  "created_at": "2026-07-25T20:00:00Z"
}
```

Sender data available today: **name**, **phone_number**, **message** (+ optional Arabic fields). No email field.

### Public submit example

```json
{
  "name": "Ahmed",
  "phone_number": "01000000000",
  "message": "I want to order eshta"
}
```

---

## Suggested dashboard screens

1. **Home** — call `GET /products/dashboard/stats/` and show 4 counters.
2. **Products** — list/create/edit/delete; toggles for `is_visible` & `is_available`; quantity + order.
3. **Categories** — CRUD + reorder via `display_order`.
4. **Offers** — CRUD + `is_active` toggle; date pickers for start/end; image upload.
5. **Contact** — list table (name, phone, message, date) + delete.

---

## Image upload note

For `product.image` and `offer.image`, use `FormData`:

```js
const form = new FormData();
form.append("name", "Eshta");
form.append("price", "25.00");
form.append("description", "...");
form.append("category", "1");
form.append("quantity", "10");
form.append("is_visible", "true");
form.append("is_available", "true");
form.append("display_order", "0");
form.append("image", fileInput.files[0]);

await fetch(`${base}/products/products/`, {
  method: "POST",
  headers: { Authorization: `Bearer ${access}` },
  body: form,
});
```

Do **not** set `Content-Type` manually when using `FormData` (browser sets boundary).

---

## Error shapes

DRF standard:

- `400` — `{ "field_name": ["error..."] }` or `{ "detail": "..." }` / `{ "non_field_errors": [...] }`
- `401` — missing/invalid token
- `403` — authenticated but not staff
- `404` — not found

Offer date validation: if both dates set, `end_date` must be ≥ `start_date`.

---

## Checklist for FE agent

- [ ] Login with JWT; store `access` / `refresh`; attach Bearer on dashboard calls
- [ ] Dashboard home uses stats endpoint
- [ ] Products support hide/show, stock, quantity, display order, image
- [ ] Categories support display order
- [ ] Offers CRUD + activate/deactivate + optional dates + banner image
- [ ] Contact inbox: list + delete (no edit)
- [ ] Public storefront can reuse GET products/categories/offers without auth
- [ ] Prefer `/ar` prefix for Arabic UI
- [ ] Use Swagger at `/en/api/docs/` while integrating
