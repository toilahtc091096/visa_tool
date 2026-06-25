from database.connection import get_connection, init_database
from database.crud.visa_registration import (
    create_visa_registration,
    delete_visa_registration,
    get_visa_registration_by_first_applyid,
    get_visa_registration_by_id,
    get_visa_registration_by_passport,
    list_visa_registrations,
    list_visa_registrations_by_status,
    delete_visa_registrations_by_passport_except_status,
    batch_update_visa_registration_status_and_payload,
    update_visa_registration_status,
    update_visa_registration_status_and_payload,
)
from database.models.visa_registration import VisaRegistration

__all__ = [
    "VisaRegistration",
    "create_visa_registration",
    "delete_visa_registration",
    "get_visa_registration_by_first_applyid",
    "get_connection",
    "get_visa_registration_by_id",
    "get_visa_registration_by_passport",
    "init_database",
    "list_visa_registrations",
    "list_visa_registrations_by_status",
    "delete_visa_registrations_by_passport_except_status",
    "batch_update_visa_registration_status_and_payload",
    "update_visa_registration_status",
    "update_visa_registration_status_and_payload",
]
