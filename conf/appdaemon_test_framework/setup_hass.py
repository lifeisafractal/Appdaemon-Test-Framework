import mock
from appdaemon.plugins.hass.hassapi import Hass


def patch_hass():
    """
    Patch the Hass API and returns a tuple of:
    - The patched functions (as Dict)
    - A callback to un-patch all functions
    """
    #### Non-actionable functions ####
    # Patch the __init__ method to skip Hass initialisation
    patch___init__ = mock.patch.object(Hass, '__init__')
    patched___init__ = patch___init__.__enter__()
    patched___init__.return_value = None
    # Path the log method
    patch_log = mock.patch.object(Hass, 'log')
    _patched_log = patch_log.__enter__()

    #### Actionable functions ####
    # Callback registrations functions
    patch_run_daily = mock.patch.object(Hass, 'run_daily')
    patch_listen_event = mock.patch.object(Hass, 'listen_event')
    patch_listen_state = mock.patch.object(Hass, 'listen_state')
    # State functions
    patch_get_state = mock.patch.object(Hass, 'get_state')
    patch_time = mock.patch.object(Hass, 'time')
    # Interactions functions
    patch_call_service = mock.patch.object(Hass, 'call_service')
    patch_turn_on = mock.patch.object(Hass, 'turn_on')
    patch_turn_off = mock.patch.object(Hass, 'turn_off')

    ## Initialize patches
    patched_run_daily = patch_run_daily.__enter__()
    patched_listen_event = patch_listen_event.__enter__()
    patched_listen_state = patch_listen_state.__enter__()
    patched_get_state = patch_get_state.__enter__()
    patched_time = patch_time.__enter__()
    patched_call_service = patch_call_service.__enter__()
    patched_turn_on = patch_turn_on.__enter__()
    patched_turn_off = patch_turn_off.__enter__()

    ## Setup un-patch callback
    def unpatch_callback():
        patch___init__.__exit__()
        patch_log.__exit__()

        patch_run_daily.__exit__()
        patch_listen_event.__exit__()
        patch_listen_state.__exit__()
        patch_get_state.__exit__()
        patch_time.__exit__()
        patch_call_service.__exit__()
        patch_turn_off.__exit__()
        patch_turn_on.__exit__()

    return ({
        'run_daily': patched_run_daily,
        'listen_event': patched_listen_event,
        'listen_state': patched_listen_state,
        'get_state': patched_get_state,
        'time': patched_time,
        'call_service': patched_call_service,
        'turn_on': patched_turn_on,
        'turn_off': patched_turn_off
    }, unpatch_callback)