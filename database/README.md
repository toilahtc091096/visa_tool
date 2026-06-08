# Database Structure

This package stores visa registration data in PostgreSQL.

## Environment variables

- `POSTGRES_HOST` default: `localhost`
- `POSTGRES_PORT` default: `5432`
- `POSTGRES_DB` default: `visa_db`
- `POSTGRES_USER` default: `visa_user`
- `POSTGRES_PASSWORD` default: `123456`

## Initialize schema

```python
from database.connection import init_database

init_database()
```

## Example

```python
from database.connection import init_database
from database.crud.visa_registration import create_visa_registration
from database.models.visa_registration import VisaRegistration

init_database()

record_id = create_visa_registration(
    VisaRegistration(
        first_applyid="2026060800721220240",
        full_name="Nguyen Van A",
        passport_number="P1234567",
        visa_type="L15",
    )
)
print(record_id)
```

`first_applyid` is treated as the unique key. If it already exists, the row is updated instead of inserted again.
