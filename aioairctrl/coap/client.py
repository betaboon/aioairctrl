import json
import logging
import os
import asyncio

from aioairctrl.coap import aiocoap_monkeypatch  # noqa: F401
from aiocoap import (
    Context,
    GET,
    Message,
    NON,
    POST,
)

from aioairctrl.coap.encryption import EncryptionContext

logger = logging.getLogger(__name__)


class Client:
    STATUS_PATH = "/sys/dev/status"
    CONTROL_PATH = "/sys/dev/control"
    SYNC_PATH = "/sys/dev/sync"

    def __init__(self, host, port=5683):
        self.host = host
        self.port = port
        self._client_context = None
        self._encryption_context = None

    async def _init(self):
        self._client_context = await Context.create_client_context()
        self._encryption_context = EncryptionContext()
        await self._sync()

    @classmethod
    async def create(cls, *args, **kwargs):
        obj = cls(*args, **kwargs)
        await obj._init()
        return obj

    async def shutdown(self) -> None:
        if self._client_context:
            await self._client_context.shutdown()

    async def _sync(self):
        logger.debug("syncing")
        sync_request = os.urandom(4).hex().upper()
        request = Message(
            code=POST,
            mtype=NON,
            uri=f"coap://{self.host}:{self.port}{self.SYNC_PATH}",
            payload=sync_request.encode(),
        )
        response = await self._client_context.request(request).response
        client_key = response.payload.decode()
        logger.debug("synced: %s", client_key)
        self._encryption_context.set_client_key(client_key)

    async def get_status(self):
        logger.debug("retrieving status")
        request = Message(
            code=GET,
            mtype=NON,
            uri=f"coap://{self.host}:{self.port}{self.STATUS_PATH}",
        )
        #request.opt.observe = 0 # no observe here
        response = await self._client_context.request(request).response
        payload_encrypted = response.payload.decode()
        payload = self._encryption_context.decrypt(payload_encrypted)
        logger.debug("status: %s", payload)
        state_reported = json.loads(payload)
        return state_reported["state"]["reported"]

    async def observe_status(self, inital_timeout=180):
        """ observes status
            wont return untill some exception is triggert or Timeout is hit
        """
        def decrypt_status(response):
            payload_encrypted = response.payload.decode()
            payload = self._encryption_context.decrypt(payload_encrypted)
            logger.debug("observation status: %s", payload)
            status = json.loads(payload)
            return status["state"]["reported"]

        logger.info("observing status")
        request = Message(
            code=GET,
            mtype=NON, 
            uri=f"coap://{self.host}:{self.port}{self.STATUS_PATH}",
        )
        request.opt.observe = 0
        requester = self._client_context.request(request)
        ## https://github.com/chrysn/aiocoap/blob/1f03d4ceb969b2b443c288c312d44c3b7c3e2031/aiocoap/cli/client.py#L296
        #observation_is_over = asyncio.get_event_loop().create_future()
        #requester.observation.register_errback(observation_is_over.set_result)
        #requester.observation.register_callback(lambda data, options=options: incoming_observation(options, data))
        # exit_reason = await observation_is_over
        # print("Observation is over: %r"%(exit_reason,), file=sys.stderr)
        try:
            response = await asyncio.wait_for(requester.response, timeout=inital_timeout)
            yield decrypt_status(response)
            timeout = response.opt.max_age #
            timeout += 30 # add some slack to timeout
            iterator =requester.observation.__aiter__()
            while True:
                response = await asyncio.wait_for(iterator.__anext__(), timeout=timeout)
                yield decrypt_status(response)
        except asyncio.TimeoutError as e:
            logger.warning('timeout!')


    async def set_control_value(self, key, value, retry_count=5, resync=True) -> None:
        return await self.set_control_values(
            data={key: value}, retry_count=retry_count, resync=resync
        )

    async def set_control_values(self, data: dict, retry_count=5, resync=True) -> None:
        state_desired = {
            "state": {
                "desired": {
                    "CommandType": "app",
                    "DeviceId": "",
                    "EnduserId": "",
                    **data,
                }
            }
        }
        payload = json.dumps(state_desired)
        logger.debug("REQUEST: %s", payload)
        payload_encrypted = self._encryption_context.encrypt(payload)
        request = Message(
            code=POST,
            mtype=NON,
            uri=f"coap://{self.host}:{self.port}{self.CONTROL_PATH}",
            payload=payload_encrypted.encode(),
        )
        response = await self._client_context.request(request).response
        logger.debug("RESPONSE: %s", response.payload)
        result = json.loads(response.payload)
        if result.get("status") == "success":
            return True
        else:
            if resync:
                logger.debug("set_control_value failed. resyncing...")
                await self._sync()
            if retry_count > 0:
                logger.debug("set_control_value failed. retrying...")
                return await self.set_control_values(data, retry_count - 1, resync)
            logger.error("set_control_value failed: %s", data)
            return False
