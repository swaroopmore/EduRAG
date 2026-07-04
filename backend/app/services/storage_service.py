import os
import uuid
import aiofiles

from fastapi import UploadFile


class StorageService:

    UPLOAD_DIR = "uploads/documents"

    async def save_file(
        self,
        file: UploadFile,
    ):

        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

        extension = os.path.splitext(file.filename)[1]

        filename = f"{uuid.uuid4()}{extension}"

        path = os.path.join(
            self.UPLOAD_DIR,
            filename,
        )

        async with aiofiles.open(
            path,
            "wb",
        ) as out_file:

            content = await file.read()

            await out_file.write(content)

        return {
            "filename": filename,
            "path": path,
            "size": len(content),
            "type": extension.replace(".", ""),
        }