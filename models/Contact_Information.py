from typing import Optional
from sqlmodel import SQLModel


class Name(SQLModel):
    provided: str
    Pan: str
    Aadhar: str
    Tax: str
    flag: bool
    pan_match: bool
    aadhar_match: bool
    tax_match: bool
    remarks: str

class Mobile(SQLModel):
    provided: str
    Pan: str
    Aadhar: str
    Government: str
    flag: bool
    pan_match: bool
    aadhar_match: bool
    government_match: bool
    remarks: str

class Email(SQLModel):
    provided: str
    Pan: str
    Aadhar: str
    Government: str
    flag: bool
    pan_match: bool
    aadhar_match: bool
    government_match: bool
    remarks: str

class Address(SQLModel):
    provided: Optional[str]
    Pan: str
    Aadhar: str
    Government: str
    flag: bool
    pan_match: bool
    aadhar_match: bool
    government_match: bool
    remarks: str

class Index(SQLModel):
    consistency: int
    discrepancy: int
    meter: str
    remarks: str

class contact_info(SQLModel):
    name: Name
    mobile: Mobile
    email: Email
    address: Address
    index: Index