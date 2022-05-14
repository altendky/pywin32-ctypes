#
# (C) Copyright 2014 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
""" Interface to credentials management functions. """
from win32ctypes.core import _authentication, _common, _backend
from .pywintypes import pywin32error as _pywin32error

# Bring constants into namespace
from win32ctypes.constants import (  # noqa
    CRED_TYPE_GENERIC,
    CRED_PERSIST_SESSION,
    CRED_PERSIST_LOCAL_MACHINE,
    CRED_PERSIST_ENTERPRISE,
    CRED_ENUMERATE_ALL_CREDENTIALS,
    CRED_PERSIST_ENTERPRISE)


def CredWrite(Credential, Flags=0):
    """ Creates or updates a stored credential.

    Parameters
    ----------
    Credential : dict
        A dictionary corresponding to the PyWin32 ``PyCREDENTIAL``
        structure.
    Flags : int
        ``CRED_PRESERVE_CREDENTIAL_BLOB`` or 0. Default is 0.

    """
    c_creds = _authentication.CREDENTIAL.fromdict(Credential)
    c_pcreds = _authentication.PCREDENTIAL(c_creds)
    with _pywin32error():
        _authentication._CredWrite(c_pcreds, 0)


def CredRead(TargetName, Type, Flags=0):
    """ Retrieves a stored credential.

    Parameters
    ----------
    TargetName : unicode
        The target name to fetch from the keyring.
    Type : int
        One of the CRED_TYPE_* constants.
    Flags : int
        Reserved, always use 0.

    Returns
    -------
    credentials : dict
        ``None`` if the target name was not found or A dictionary
        corresponding to the PyWin32 ``PyCREDENTIAL`` structure.

    """
    if Type != CRED_TYPE_GENERIC:
        raise ValueError("Type != CRED_TYPE_GENERIC not yet supported")

    flag = 0
    with _pywin32error():
        if _backend == 'cffi':
            ppcreds = _authentication.PPCREDENTIAL()
            _authentication._CredRead(TargetName, Type, flag, ppcreds)
            pcreds = _common.dereference(ppcreds)
        else:
            pcreds = _authentication.PCREDENTIAL()
            _authentication._CredRead(
                TargetName, Type, flag, _common.byreference(pcreds))
    try:
        return _authentication.credential2dict(_common.dereference(pcreds))
    finally:
        _authentication._CredFree(pcreds)


def CredDelete(TargetName, Type, Flags=0):
    """ Remove the given target name from the stored credentials.

    Parameters
    ----------
    TargetName : unicode
        The target name to fetch from the keyring.
    Type : int
        One of the CRED_TYPE_* constants.
    Flags : int
        Reserved, always use 0.

    """
    if not Type == CRED_TYPE_GENERIC:
        raise ValueError("Type != CRED_TYPE_GENERIC not yet supported.")
    with _pywin32error():
        _authentication._CredDelete(TargetName, Type, 0)


def CredEnumerate(Filter=None, Flags=0):
    """ Remove the given target name from the stored credentials.

    Parameters
    ----------
    Filter : unicode
        Matches credentials' target names by prefix, can be None.
    Flags : int
        When set to CRED_ENUMERATE_ALL_CREDENTIALS enumerates all of
        the credentials in the user's credential set but in that
        case the Filter parameter should be NULL, an error is
        raised otherwise

    Returns
    -------
    credentials : list
        Returns a sequence of CREDENTIAL dictionaries.

    """
    with _pywin32error():
        if _backend == 'cffi':
            pcount = _common.PDWORD()
            pppcredential = _authentication.PPPCREDENTIAL()
            _authentication._CredEnumerate(
                Filter, Flags, pcount, pppcredential)
            count = pcount[0]
            data = _common.dereference(
                _common.ffi.cast(f"PCREDENTIAL*[{count}]", pppcredential))
            memory = _common.dereference(pppcredential)
        else:
            import ctypes
            count = _authentication.DWORD()
            pcredential = _authentication.PCREDENTIAL()
            ppcredential = ctypes.pointer(pcredential)
            pppcredential = ctypes.pointer(ppcredential)
            _authentication._CredEnumerate(
                Filter, Flags, _common.byreference(count), pppcredential)
            count = count.value
            data = _common.dereference(
                _common.cast(
                    ppcredential,
                    _common.POINTER(_authentication.PCREDENTIAL*count)))
            memory = pcredential
    try:
        result = []
        for i in range(count):
            credential = _common.dereference(data[i])
            result.append(_authentication.credential2dict(credential))
        return result
    finally:
        _authentication._CredFree(memory)
