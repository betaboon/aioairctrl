import asyncio

import aiocoap
from aiocoap import error


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
