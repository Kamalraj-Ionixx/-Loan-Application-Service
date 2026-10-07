from fastapi import HTTPException, status


class DuplicateEmailError(Exception):
    pass
