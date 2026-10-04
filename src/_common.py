# ---------------------------------------------------------------------------
# Shared runtime for TS4 Unofficial Fixes (prepended to every fix at build time)
# ---------------------------------------------------------------------------
import hashlib
import os
import sys
import time
import traceback
import types

_MODS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_PATH = os.path.join(_MODS_DIR, 'ts4_unofficial_fixes.log')

# One registry shared by every fix script, whatever the load order.
_REGISTRY = sys.modules.get('ts4_unofficial_fixes_registry')
if _REGISTRY is None:
    _REGISTRY = types.ModuleType('ts4_unofficial_fixes_registry')
    _REGISTRY.fixes = {}
    _REGISTRY.commands_registered = False
    sys.modules['ts4_unofficial_fixes_registry'] = _REGISTRY


def _log(message):
    try:
        with open(_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write('[{}] [{}] {}\n'.format(time.strftime('%Y-%m-%d %H:%M:%S'), FIX_ID, message))
    except Exception:
        pass


def _fingerprint(func):
    code = func.__code__
    digest = hashlib.sha1()
    digest.update(code.co_code)
    digest.update(repr(code.co_names).encode())
    digest.update(repr(code.co_varnames).encode())
    return digest.hexdigest()[:16]


class _FixState:
    def __init__(self):
        self.status = 'not loaded'
        self.counters = {}

    def count(self, key, amount=1):
        self.counters[key] = self.counters.get(key, 0) + amount


STATE = _FixState()
_REGISTRY.fixes[FIX_ID] = STATE


def _replace(owner, attr, new_func, expected_fingerprint):
    """Swap owner.attr for new_func, but only if the original is exactly the code we fixed.

    If EA patched the function (or another mod already replaced it), the fingerprint no
    longer matches and the fix stays out of the way.
    """
    original = owner.__dict__.get(attr)
    original_func = getattr(original, '__func__', original)
    if original_func is None or not hasattr(original_func, '__code__'):
        raise RuntimeError('{}.{} not found'.format(owner.__name__, attr))
    found = _fingerprint(original_func)
    if found != expected_fingerprint and not getattr(sys, '_ts4_unofficial_fixes_test', False):
        raise _Mismatch('{}.{} has changed (expected {}, found {}): fix disabled'.format(
            owner.__name__, attr, expected_fingerprint, found))
    new_func.__wrapped__ = original_func
    setattr(owner, attr, new_func)
    return original_func


class _Mismatch(Exception):
    pass


def _register_status_command():
    if _REGISTRY.commands_registered:
        return
    import sims4.commands

    @sims4.commands.Command('ufix.status', command_type=sims4.commands.CommandType.Live)
    def ufix_status(_connection=None):
        output = sims4.commands.CheatOutput(_connection)
        for fix_id in sorted(_REGISTRY.fixes):
            state = _REGISTRY.fixes[fix_id]
            counters = ', '.join('{}={}'.format(k, v) for k, v in sorted(state.counters.items()))
            output('{}: {}{}'.format(fix_id, state.status, ' (' + counters + ')' if counters else ''))

    _REGISTRY.commands_registered = True


def _run(install):
    try:
        install()
        STATE.status = 'active'
        _log('active')
    except _Mismatch as exc:
        STATE.status = 'disabled (game code changed)'
        _log(str(exc))
    except Exception:
        STATE.status = 'error'
        _log('failed to install:\n' + traceback.format_exc())
    try:
        _register_status_command()
    except Exception:
        _log('could not register ufix.status:\n' + traceback.format_exc())

# ---------------------------------------------------------------------------
