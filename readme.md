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