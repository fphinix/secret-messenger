from typing import Optional, Tuple
from google.auth.credentials import Scoped
from gspread.cell import Cell
from gspread_asyncio import AsyncioGspreadWorksheet
from dotenv import load_dotenv

load_dotenv()

import gspread_asyncio
import os
import hashlib


from google.oauth2.service_account import Credentials

class Database:

    def __init__(self, spreadsheet_key: str) -> None:

        def get_creds() -> Scoped:
            env_fields = ["token", "type", "project_id", "private_key_id",
                "private_key", "client_email", "client_email", "auth_uri",
                "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]

            creds = Credentials.from_service_account_info({ cred: os.environ.get(cred) for cred in env_fields })
            scoped = creds.with_scopes([
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ])
            return scoped

        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        self.spreadsheet_key = spreadsheet_key

        self.logged_in_users = {}
        return

    async def _get_worksheet(self, index: int) -> AsyncioGspreadWorksheet:
        """Helper function"""
        agc = await self.agcm.authorize()
        ss = await agc.open_by_key(self.spreadsheet_key)
        return await ss.get_worksheet(index)
    
    async def _find_value_from_column(self, worksheet: AsyncioGspreadWorksheet, column_number: int, value: str) -> Optional[Cell]:
        """Helper function"""
        records = await worksheet.get_all_values()
        for row_idx, row in enumerate(records[1:]): #skip first value
            row_value = row[column_number - 1]
            if row_value  == value:
                return Cell(row_idx+2, column_number, row_value)
        return None

    async def increment_counter(self) -> int:
        worksheet = await self._get_worksheet(1)
        cell = await worksheet.cell(1, 2)
        await worksheet.update_cell(1, 2, int(cell.value) + 1)
        return int(cell.value)
    
    async def is_password_and_nickname_valid(self, nickname: str, password: str, userid: str) -> bool:
        worksheet = await self._get_worksheet(0)
        
        cell = await self._find_value_from_column(worksheet, 1, nickname)
        if cell is None:
            return False
        
        hashed_password = hashlib.sha256(bytes(password + userid, "utf-8"), usedforsecurity=True).hexdigest()
        stored_hashed_password = await worksheet.cell(cell.row, cell.col + 1)

        return hashed_password == stored_hashed_password.value

    async def is_nickname_duplicate(self, nickname: str) -> bool:
        worksheet = await self._get_worksheet(0)
        cell = await self._find_value_from_column(worksheet, 1, nickname)
        return cell is not None

    async def register_nickname(self, nickname: str, password: str, userid: str) -> None:

        worksheet = await self._get_worksheet(0)
        hashed_password = hashlib.sha256(bytes(password + userid, "utf-8"), usedforsecurity=True).hexdigest()

        await worksheet.append_row([nickname, hashed_password])

        return
    
    async def delete_nickname(self, nickname: str, password: str, userid: str) -> bool:
        worksheet = await self._get_worksheet(0)

        if not await self.is_password_and_nickname_valid(nickname, password, userid):
            return False
        
        cell = await self._find_value_from_column(worksheet, 1, nickname)
        await worksheet.delete_row(cell.row)
        await self.logout_user(userid)
        return True
    
    async def change_nickname(self, new_nickname: str, userid: str) -> bool:
        worksheet = await self._get_worksheet(0)
        
        nickname = await self.get_nickname_from_session(userid)
        
        cell = await self._find_value_from_column(worksheet, 1, nickname)
        if cell is None:
            return False

        await worksheet.update_cell(cell.row, cell.col, new_nickname)
        return True

    async def change_password(self, nickname: str, password: str, new_password: str, userid: str):
        worksheet = await self._get_worksheet(0)

        if not await self.is_password_and_nickname_valid(nickname, password, userid):
            return False
        
        hashed_password = hashlib.sha256(bytes(new_password + userid, "utf-8"), usedforsecurity=True).hexdigest()
        cell = await self._find_value_from_column(worksheet, 1, nickname)
        await worksheet.update_cell(cell.row, cell.col + 1, hashed_password)
        return True
    
    async def increment_counter(self) -> int:
        worksheet = await self._get_worksheet(1)
        cell = await worksheet.cell(1, 2)
        await worksheet.update_cell(1, 2, int(cell.value) + 1)
        return int(cell.value)

    async def increment_prompted_question_counter(self) -> int:
        worksheet = await self._get_worksheet(1)
        cell = await worksheet.cell(2, 2)
        await worksheet.update_cell(2, 2, int(cell.value) + 1)
        return int(cell.value)

    async def login_user(self, nickname: str, password: str, userid: str) -> bool:
        is_valid = await self.is_password_and_nickname_valid(nickname, password, userid)
        if is_valid:
            hashed_id = hashlib.sha256(bytes(userid, "utf-8"), usedforsecurity=True).hexdigest()
            self.logged_in_users[hashed_id] = nickname
        return is_valid
    
    async def logout_user(self, userid: str) -> bool:
        hashed_id = hashlib.sha256(bytes(userid, "utf-8"), usedforsecurity=True).hexdigest()
        if hashed_id in self.logged_in_users:
            self.logged_in_users.pop(hashed_id)
            return True
        return False
    
    async def get_nickname_from_session(self, userid: str) -> Optional[str]:
        hashed_id = hashlib.sha256(bytes(userid, "utf-8"), usedforsecurity=True).hexdigest()
        if hashed_id in self.logged_in_users:
            return self.logged_in_users[hashed_id]
        return None
