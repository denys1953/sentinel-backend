from pydantic import BaseModel

class Login2FA(BaseModel):
    temp_token: str
    code: str

class Verify2FA(BaseModel):
    code: str
