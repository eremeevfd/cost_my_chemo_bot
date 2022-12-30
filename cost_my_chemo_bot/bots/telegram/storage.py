"""
This module has mongo storage for finite-state machine
    based on `motor <https://github.com/mongodb/motor>`_ driver
"""

import asyncio
import json
import typing
from typing import AnyStr, Dict, List, Optional, Tuple, Union

import aiohttp

try:
    from google.cloud import firestore
except ModuleNotFoundError as e:
    import warnings

    warnings.warn("Install motor with `pip install google-cloud-firestore`")
    raise e

from aiogram.dispatcher.storage import BaseStorage
from gcloud.aio.storage import Bucket, Storage
from aiogram.contrib.fsm_storage.files import JSONStorage

# from aiogram.contrib.fsm_storage.mongo import MongoStorage

STATE = "aiogram_state"
DATA = "aiogram_data"
BUCKET = "aiogram_bucket"
COLLECTIONS = (STATE, DATA, BUCKET)


class FirestoreStorage(BaseStorage):
    """
    Firestore-based storage for FSM.

    Usage:

    .. code-block:: python3

        storage = FirestoreStorage(host='localhost', port=27017, db_name='aiogram_fsm')
        dp = Dispatcher(bot, storage=storage)

    And need to close Mongo client connections when shutdown

    .. code-block:: python3

        await dp.storage.close()
        await dp.storage.wait_closed()
    """

    def __init__(self):
        self._db: Optional[firestore.Client] = firestore.AsyncClient()

    async def close(self):
        if self._db:
            self._db.close()

    async def wait_closed(self):
        return True

    async def set_state(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        state: Optional[AnyStr] = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db

        if state is None:
            docs = (
                db.collection(STATE)
                .where("user", "==", user)
                .where("chat", "==", chat)
                .stream()
            )
            async for doc in docs:
                doc.reference.delete()
        else:
            await db.collection(STATE).document(str(user)).set(
                {"chat": chat, "user": user, "state": self.resolve_state(state)}
            )

    async def get_state(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[str] = None,
    ) -> Optional[str]:
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db

        result = await (
            db.collection(STATE)
            .where("chat", "==", chat)
            .where("user", "==", user)
            .get()
        )
        return (
            result[0].to_dict().get("state") if result else self.resolve_state(default)
        )

    async def set_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        data: Dict = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db
        if not data:
            docs: list[firestore.DocumentSnapshot] = (
                db.collection(STATE)
                .where("chat", "==", chat)
                .where("user", "==", user)
                .stream()
            )
            async for doc in docs:
                doc.reference.delete()
        else:
            await db.collection(DATA).document(str(user)).set(
                {"chat": chat, "user": user, "data": data}
            )

    async def get_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[dict] = None,
    ) -> Dict:
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db
        result: list[firestore.DocumentSnapshot] = await (
            db.collection(DATA)
            .where("chat", "==", chat)
            .where("user", "==", user)
            .get()
        )

        return result[0].get("data") if result else default or {}

    async def update_data(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        data: Dict = None,
        **kwargs,
    ):
        if data is None:
            data = {}
        temp_data = await self.get_data(chat=chat, user=user, default={})
        temp_data.update(data, **kwargs)
        await self.set_data(chat=chat, user=user, data=temp_data)

    def has_bucket(self):
        return True

    async def get_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        default: Optional[dict] = None,
    ) -> Dict:
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db
        result = await (
            db.collection(BUCKET)
            .where("chat", "==", chat)
            .where("user", "==", user)
            .get()
        )
        return result.to_dict().get("bucket") if result else default or {}

    async def set_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        bucket: Dict = None,
    ):
        chat, user = self.check_address(chat=chat, user=user)
        db = self._db

        await db.collection(BUCKET).where("chat", "==", chat).where(
            "user", "==", user
        ).set({"bucket": bucket})

    async def update_bucket(
        self,
        *,
        chat: Union[str, int, None] = None,
        user: Union[str, int, None] = None,
        bucket: Dict = None,
        **kwargs,
    ):
        if bucket is None:
            bucket = {}
        temp_bucket = await self.get_bucket(chat=chat, user=user)
        temp_bucket.update(bucket, **kwargs)
        await self.set_bucket(chat=chat, user=user, bucket=temp_bucket)

    async def delete_collection(
        self, coll_ref: firestore.AsyncCollectionReference, batch_size: int
    ):
        docs = coll_ref.limit(batch_size).stream()
        deleted = 0

        async for doc in docs:
            print(f"Deleting doc {doc.id} => {doc.to_dict()}")
            await doc.reference.delete()
            deleted = deleted + 1

        if deleted >= batch_size:
            return await self.delete_collection(coll_ref, batch_size)

    async def reset_all(self, full=True):
        """
        Reset states in DB

        :param full: clean DB or clean only states
        :return:
        """
        db = self._db

        await self.delete_collection(db.collection(STATE), batch_size=10)

        if full:
            await self.delete_collection(db.collection(DATA), batch_size=10)
            await self.delete_collection(db.collection(BUCKET), batch_size=10)

    async def get_states_list(self) -> List[Tuple[int, int]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        db = self._db
        items = db.collection(STATE).stream()
        return [(int(item.get("chat")), int(item.get("user"))) async for item in items]


class GcloudStorage(BaseStorage):
    """
    In-memory based states storage.

    This type of storage is not recommended for usage in bots, because you will lost all states after restarting.
    """

    async def wait_closed(self):
        while self.session is not None and not self.session.closed:
            await self.session.close()
            await asyncio.sleep(0.1)

    async def close(self):
        await self.storage.close()
        await self.session.close()

    def __init__(self, bucket_name: str = "cost-my-chemo-bot-storage"):
        self.session: aiohttp.ClientSession | None = None
        self.storage: Storage | None = None
        self.bucket: Bucket | None = None
        self.bucket_name = bucket_name

    async def get_storage(self) -> Storage:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

        if self.storage is None:
            self.storage = Storage()

        if self.bucket is None:
            self.bucket = self.storage.get_bucket(bucket_name=self.bucket_name)
        return self.storage

    async def resolve_address(self, chat, user):
        chat_id, user_id = map(str, self.check_address(chat=chat, user=user))

        storage = await self.get_storage()

        if not await self.bucket.blob_exists(blob_name=f"{chat_id}/{user_id}.json"):
            await storage.upload(
                self.bucket.name,
                f"{chat_id}/{user_id}.json",
                json.dumps({"state": None, "data": {}, "bucket": {}}),
            )

        return chat_id, user_id

    async def download_state(
        self, *, chat: str | int | None = None, user: str | int | None = None
    ) -> dict:
        await self.get_storage()
        user_blob = await self.bucket.get_blob(blob_name=f"{chat}/{user}.json")
        blob_content = await user_blob.download()
        return json.loads(blob_content)

    async def upload_state(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        data: dict,
    ):
        await self.get_storage()
        user_blob = await self.bucket.get_blob(blob_name=f"{chat}/{user}.json")
        await user_blob.upload(json.dumps(data))

    async def get_state(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        default: str | None = None,
    ) -> str | None:
        chat, user = await self.resolve_address(chat=chat, user=user)
        data = await self.download_state(chat=chat, user=user)
        return data.get("state", self.resolve_state(default))

    async def get_data(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        default: str | None = None,
    ) -> dict:
        chat, user = await self.resolve_address(chat=chat, user=user)
        data = await self.download_state(chat=chat, user=user)
        return data.get("data", self.resolve_state(default))

    async def update_data(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        data: dict = None,
        **kwargs,
    ):
        if data is None:
            data = {}
        chat, user = await self.resolve_address(chat=chat, user=user)
        old_data = await self.download_state(chat=chat, user=user)
        old_data["data"].update(data, **kwargs)
        await self.upload_state(chat=chat, user=user, data=old_data)

    async def set_state(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        state: typing.AnyStr = None,
    ):
        chat, user = await self.resolve_address(chat=chat, user=user)
        data = await self.download_state(chat=chat, user=user)
        data["state"] = self.resolve_state(state)
        await self.upload_state(chat=chat, user=user, data=data)

    async def set_data(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        data: dict = None,
    ):
        chat, user = await self.resolve_address(chat=chat, user=user)
        old_data = await self.download_state(chat=chat, user=user)
        old_data["data"] = data
        await self.upload_state(chat=chat, user=user, data=old_data)
        await self._cleanup(chat, user)

    async def reset_state(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        with_data: typing.Optional[bool] = True,
    ):
        await self.set_state(chat=chat, user=user, state=None)
        if with_data:
            await self.set_data(chat=chat, user=user, data={})
        await self._cleanup(chat, user)

    def has_bucket(self):
        return True

    async def get_bucket(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        default: dict | None = None,
    ) -> dict:
        chat, user = await self.resolve_address(chat=chat, user=user)
        data = await self.download_state(chat=chat, user=user)
        return data.get("bucket", self.resolve_state(default))

    async def set_bucket(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        bucket: dict = None,
    ):
        chat, user = await self.resolve_address(chat=chat, user=user)
        data = await self.download_state(chat=chat, user=user)
        data["bucket"] = bucket
        await self.upload_state(chat=chat, user=user, data=data)
        await self._cleanup(chat, user)

    async def update_bucket(
        self,
        *,
        chat: str | int | None = None,
        user: str | int | None = None,
        bucket: dict = None,
        **kwargs,
    ):
        if bucket is None:
            bucket = {}
        chat, user = await self.resolve_address(chat=chat, user=user)
        data = await self.download_state(chat=chat, user=user)
        data.get["bucket"].update(bucket, **kwargs)
        await self.upload_state(chat=chat, user=user, data=data)

    async def _cleanup(self, chat, user):
        storage = await self.get_storage()
        chat, user = await self.resolve_address(chat=chat, user=user)
        data = await self.download_state(chat=chat, user=user)
        if data == {"state": None, "data": {}, "bucket": {}}:
            await self.storage.delete(
                bucket_name=self.bucket.name, blob_name=f"{chat}/{user}.json"
            )


if __name__ == "__main__":
    storage = GcloudStorage()
    # print(asyncio.run(storage.get_states_list()))
    # print(asyncio.run(storage.reset_all()))
    print(asyncio.run(storage.get_state(chat=130909778, user=130909778)))
    storage.close()