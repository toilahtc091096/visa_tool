from database.connection import get_connection, init_database
from database.crud.visa_registration import (
    create_visa_registration,
    delete_visa_registration,
    get_visa_registration_by_first_applyid,
    get_visa_registration_by_id,
    get_visa_registration_by_passport,
    list_existing_visa_registration_application_codes,
    list_visa_registrations,
    list_visa_registrations_by_status,
    delete_visa_registrations_by_passport_except_status,
    batch_update_visa_registration_status_and_payload,
    update_visa_registration_status,
    update_visa_registration_status_and_payload,
)
from database.crud.approval_print_job import (
    get_approval_print_job_by_han_code,
    list_approval_print_jobs,
    update_approval_print_job_by_han_code,
    update_approval_print_job_status_by_codes,
    update_approval_print_job_status_by_ids,
    upsert_approval_print_job_processing,
)
from database.models.visa_registration import VisaRegistration
from database.models.approval_print_job import ApprovalPrintJob

__all__ = [
    "VisaRegistration",
    "ApprovalPrintJob",
    "create_visa_registration",
    "delete_visa_registration",
    "get_visa_registration_by_first_applyid",
    "get_connection",
    "get_visa_registration_by_id",
    "get_visa_registration_by_passport",
    "list_existing_visa_registration_application_codes",
    "init_database",
    "list_visa_registrations",
    "list_visa_registrations_by_status",
    "delete_visa_registrations_by_passport_except_status",
    "batch_update_visa_registration_status_and_payload",
    "update_visa_registration_status",
    "update_visa_registration_status_and_payload",
    "get_approval_print_job_by_han_code",
    "list_approval_print_jobs",
    "update_approval_print_job_by_han_code",
    "update_approval_print_job_status_by_codes",
    "update_approval_print_job_status_by_ids",
    "upsert_approval_print_job_processing",
]
