import asyncio
import functools

import aiocoap
from aiocoap import error
from aiocoap.numbers.constants import EXCHANGE_LIFETIME


def _deduplicate_message(self, message):
    key = (message.remote, message.mid)
    self.log.debug("MP: New unique message received")
    self.loop.call_later(EXCHANGE_LIFETIME, functools.partial(self._recent_messages.pop, key))
    self._recent_messages[key] = None
    return False


aiocoap.messagemanager.MessageManager._deduplicate_message = _deduplicate_message


def __del__(self):
    if self._future.done():
        try:
            # Fetch the result so any errors show up at least in the
            # finalizer output
            self._future.result()
        except (error.ObservationCancelled, error.NotObservable):
            # This is the case at the end of an observation cancelled
            # by the server.
            pass
        except error.LibraryShutdown:
            pass
        except asyncio.CancelledError:
            pass


aiocoap.protocol.ClientObservation._Iterator.__del__ = __del__
