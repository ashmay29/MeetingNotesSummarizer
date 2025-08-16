from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

class MeetingIn(BaseModel):
    title: Optional[str] = None
    transcriptText: str
    instructions: Optional[str] = None

class MeetingOut(BaseModel):
    id: str = Field(alias="_id")
    title: Optional[str] = None
    transcriptText: str
    instructions: Optional[str] = None
    summary: Optional[str] = None
    recipients: List[str] = []
    createdAt: datetime
    updatedAt: datetime

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    instructions: Optional[str] = None

class EmailRequest(BaseModel):
    to: List[EmailStr]
    subject: Optional[str] = None
