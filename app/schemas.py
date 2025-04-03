from pydantic import BaseModel, EmailStr, field_validator,Field
from typing import Optional
import re
class Config:
    orm_mode = True  # Это позволяет Pydantic работать с SQLAlchemy моделями
    
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
  
  # Проверка урла   
class LinkRequest(BaseModel):
    original_url: str  
    customAlias: Optional[str] = Field(None, alias="custom_alias")  # 👈 Добавляем alias!

    @field_validator('original_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if len(v) > 2000:
            raise ValueError('URL слишком длинный')
        if not re.match(r"^https?://", v):  
            raise ValueError('Некорректный URL')
        return v.strip()

    @field_validator("customAlias", mode="before")
    @classmethod
    def validate_alias(cls, v) -> Optional[str]:
        print(f"Проверка alias (до обработки): {v}")  

        if v in (None, "", "null"):  # Если пустой — приводим к None
            return None

        if not isinstance(v, str):
            raise ValueError("Alias должен быть строкой.")

        v = v.strip()
        print(f"Проверка alias (после обработки): {v}")  

        if not re.match(r"^[a-zA-Z0-9]{5,15}$", v):
            raise ValueError("Alias должен содержать только буквы и цифры (от 5 до 15 символов).")

        return v
    
class ShortLinkUpdateModel(BaseModel):
    new_url: str = Field(..., max_length=2000)

    @field_validator('new_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not re.match(r"^https?://", v):  # Проверяем, что URL начинается с http:// или https://
            raise ValueError('Некорректный URL')
        return v.strip()
    
class ArchiveFilter(BaseModel):
    short_code: Optional[str] = None  # Фильтр по короткой ссылке (необязательный)