# Daniel Padnos Wellness Center

## Start Proyect

Run the following commands

> pip install -r requirements.txt
> python manage.py makemigrations
> python manage.py migrate
> python manage.py runserver

it should work !

---

## Patient Endpoints `/api/v1/patient/`

All endpoints require JWT authentication: `Authorization: Bearer <token>`

### Create patient
```
POST /api/v1/patient/
```
```json
{
    "name": "Juan Pérez",
    "age": 20,
    "state": true,
    "phone": "12345678",
    "gender": "hombre",
    "grade": "5to",
    "address": "Ciudad de Guatemala",
    "tutor": "María Pérez",
    "managersPhoneNumber": "87654321",
    "place": "CDO"
}
```
Required fields: `name`, `age`, `state`

Valid values for `place`: `CDO`, `SEMILLERO`, `EXTERNAL`

### List / Search patients
```
GET /api/v1/patient/
GET /api/v1/patient/list/?search=nombre
```

### Get / Update / Delete patient
```
GET    /api/v1/patient/<id>/
PUT    /api/v1/patient/<id>/
PATCH  /api/v1/patient/<id>/
DELETE /api/v1/patient/<id>/
```

> **Nota:** El campo `id` es de solo lectura. Cualquier valor enviado en el body para `id` será ignorado.

Valid values for `gender`: `MASCULINO`, `FEMENINO`, `OTRO`

---

## Appointment Endpoints `/api/v1/appointment/`

All endpoints require JWT authentication: `Authorization: Bearer <token>`

### Create appointment
```
POST /api/v1/appointment/
```
```json
{
    "patient": 1,
    "doctor": 1,
    "hour": "10:00:00",
    "date": "2026-08-15",
    "status": "PENDING",
    "place": "CDO",
    "notes": "Primera consulta"
}
```
Valid values for `status`: `PENDING`, `DONE`, `CANCELLED`

Valid values for `place`: `CDO`, `SEMILLERO`, `OTHER`

Supports future and past (retroactive) dates.

### List appointments
```
GET /api/v1/appointment/
```
Supports the following query params:

| Param | Description | Example |
|---|---|---|
| `patient` | Filter by patient id | `?patient=6` |
| `doctor` | Filter by doctor id | `?doctor=1` |
| `place` | Filter by place | `?place=CDO` |
| `date_from` | Filter from date (inclusive) | `?date_from=2026-06-01` |
| `date_to` | Filter to date (inclusive) | `?date_to=2026-06-30` |
| `order` | Sort by date: `asc` or `desc` (default) | `?order=asc` |

Params can be combined:
```
GET /api/v1/appointment/?patient=6&place=CDO&order=asc&date_from=2026-06-01&date_to=2026-12-31
```

Returns paginated results (10 per page). Each appointment includes `attendanceStatus`:
- `PENDING` → `PENDIENTE`
- `DONE` → `CUMPLIDA`
- `CANCELLED` → `NO CUMPLIDA`

```json
{
    "count": 4,
    "next": "http://127.0.0.1:8000/api/v1/appointment/?page=2",
    "previous": null,
    "results": [
        {
            "id": 3,
            "date": "2026-07-10",
            "status": "PENDING",
            "attendanceStatus": "PENDIENTE",
            ...
        }
    ]
}
```

### Get / Update appointment
```
GET   /api/v1/appointment/<id>/
PUT   /api/v1/appointment/<id>/
PATCH /api/v1/appointment/<id>/
```

### Pending appointments
```
GET /api/v1/appointment/pending/
```
Returns all appointments with status `PENDING` and future date, ordered ascending.