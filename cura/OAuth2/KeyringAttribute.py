# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Type, TYPE_CHECKING

import keyring
from keyring.backend import KeyringBackend
from keyring.errors import NoKeyringError, PasswordSetError

from UM.Logger import Logger

if TYPE_CHECKING:
    from cura.OAuth2.Models import BaseModel


class KeyringAttribute:
    """
    Descriptor for attributes that need to be stored in the keyring. With Fallback behaviour to the preference cfg file
    """
    def __get__(self, instance: Type["BaseModel"], owner: type) -> str:
        if self._store_secure:
            try:
                return keyring.get_password("cura", self._keyring_name)
            except NoKeyringError:
                self._store_secure = False
                Logger.logException("w", "No keyring backend present")
                return getattr(instance, self._name)
        else:
            return getattr(instance, self._name)

    def __set__(self, instance: Type["BaseModel"], value: str):
        if self._store_secure:
            setattr(instance, self._name, None)
            try:
                keyring.set_password("cura", self._keyring_name, value)
            except PasswordSetError:
                self._store_secure = False
                setattr(instance, self._name, value)
                Logger.logException("w", "Keyring access denied")
            except NoKeyringError:
                self._store_secure = False
                setattr(instance, self._name, value)
                Logger.logException("w", "No keyring backend present")
            except BaseException as e:
                # A BaseException can occur in Windows when the keyring attempts to write a token longer than 1024
                # characters in the Windows Credentials Manager.
                self._store_secure = False
                setattr(instance, self._name, value)
                Logger.log("w", "Keyring failed: {}".format(e))
        else:
            setattr(instance, self._name, value)

    def __set_name__(self, owner: type, name: str):
        self._name = "_{}".format(name)
        self._keyring_name = name
        self._store_secure = False
        try:
            self._store_secure = KeyringBackend.viable
        except NoKeyringError:
            Logger.logException("w", "Could not use keyring")
        setattr(owner, self._name, None)
