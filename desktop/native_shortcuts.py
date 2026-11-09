"""Registered application combinations, never an arbitrary page input bridge."""
import re
import threading
import time

from training import ServiceError

_MODIFIER = re.compile(r'^(Ctrl|Alt|Shift|Meta)\+', re.I)
_FUNCTION = re.compile(r'F(?:[1-9]|1\d|2[0-4])$', re.I)
_SPECIAL = {8: 'Backspace', 9: 'Tab', 13: 'Enter', 27: 'Escape', 32: 'Space',
            33: 'PageUp', 34: 'PageDown', 35: 'End', 36: 'Home', 37: 'ArrowLeft',
            38: 'ArrowUp', 39: 'ArrowRight', 40: 'ArrowDown', 45: 'Insert', 46: 'Delete'}
_SYMBOLS = {186: ';:', 187: '=+', 188: ',<', 189: '-_', 190: '.>', 191: '/?',
            192: '`~', 219: '[{', 220: '\\|', 221: ']}', 222: '\'"'}


def combination(value):
    if not isinstance(value, str) or not 0 < len(value) <= 80:
        return None
    modifiers = []
    while match := _MODIFIER.match(value):
        modifier = match[1].lower()
        if modifier in modifiers:
            return None
        modifiers.append(modifier)
        value = value[match.end():]
    if not value or any(ord(char) < 32 for char in value):
        return None
    # Plain text and ordinary editing keys remain with the webpage. The
    # frontend uses the same text-safe eligibility rule for native forwarding.
    if not {'ctrl', 'alt', 'meta'} & set(modifiers) and not (_FUNCTION.fullmatch(value) or value.lower() == 'escape'):
        return None
    if len(value) != 1 and value.lower() not in {item.lower() for item in _SPECIAL.values()} and not _FUNCTION.fullmatch(value):
        return None
    return '+'.join([item for item in ('ctrl', 'meta', 'alt', 'shift') if item in modifiers] + [value.lower()])


def validate_registration(value):
    if value is None:
        return {'serial': 0, 'bindings': []}
    if (not isinstance(value, dict) or set(value) != {'serial', 'bindings'}
            or type(value['serial']) is not int or not 0 < value['serial'] < 2**53
            or not isinstance(value['bindings'], list) or len(value['bindings']) > 192):
        raise ServiceError(400, '应用快捷键注册无效')
    for entry in value['bindings']:
        if (not isinstance(entry, dict) or set(entry) != {'route', 'id', 'combo', 'context'}
                or not all(isinstance(entry[field], str) and len(entry[field]) <= limit
                           and not any(ord(char) < 32 for char in entry[field])
                           for field, limit in (('route', 200), ('id', 80), ('context', 4096)))
                or not entry['route'] or not re.fullmatch('[a-z0-9-]{1,80}', entry['id'])
                or combination(entry['combo']) is None):
            raise ServiceError(400, '应用快捷键注册无效')
    return value


def windows_combination(key, *, control=False, alt=False, shift=False, meta=False):
    if 65 <= key <= 90:
        character = chr(key)
    elif 48 <= key <= 57:
        character = ')!@#$%^&*('[key - 48] if shift else chr(key)
    elif key in _SYMBOLS:
        character = _SYMBOLS[key][int(shift)]
    elif 112 <= key <= 135:
        character = 'F' + str(key - 111)
    else:
        character = _SPECIAL.get(key)
    if not character or meta:
        return None  # Never take Windows/Shell combinations.
    # Match eventShortcut: Shift is explicit for letters or named keys; shifted
    # punctuation already encodes it in the character (e.g. Ctrl+?).
    parts = [control and 'Ctrl', alt and 'Alt', shift and (len(character) != 1 or character.isalpha()) and 'Shift', character]
    return combination('+'.join(part for part in parts if part))


class NativeShortcuts:
    def __init__(self, *, clock=time.monotonic):
        self.clock, self.lock = clock, threading.RLock()
        self.serial = self.sequence = 0
        self.binding = self.view_id = None
        self.bindings, self.events, self.held = {}, [], set()
        self.active = False

    def configure(self, registration, binding, view_id):
        registration = validate_registration(registration)
        with self.lock:
            if (registration['serial'], binding, view_id) != (self.serial, self.binding, self.view_id):
                self.events.clear()
            self.serial, self.binding, self.view_id = registration['serial'], binding, view_id
            self.bindings = {}
            for item in registration['bindings']:
                self.bindings.setdefault(combination(item['combo']), {'route': item['route'], 'id': item['id']})
            self.active = bool(self.bindings)

    def pause(self):
        with self.lock:
            self.active = False
            self.events.clear()
            # Keep registered held keys until their real key-up, so a redraw,
            # context change or long save cannot turn repeat into another run.

    def listening(self):
        with self.lock:
            return self.active or bool(self.held)

    def has_held(self):
        with self.lock:
            return bool(self.held)

    def key(self, key, flags, *, child_owned, control=False, alt=False, shift=False, meta=False):
        with self.lock:
            released = bool(flags & 128)
            if flags & 0x12:
                return False
            if key in self.held:
                if released:
                    self.held.discard(key)
                return bool(child_owned and self.active)
            if released or not child_owned or not self.active:
                return False
            value = windows_combination(key, control=control, alt=alt, shift=shift, meta=meta)
            command = self.bindings.get(value)
            if command is None:
                return False
            self.held.add(key)
            self.sequence += 1
            self.events.append({**command, 'sequence': self.sequence, 'time': self.clock()})
            self.events = self.events[-32:]
            return True

    def snapshot(self, binding):
        with self.lock:
            active = bool(self.active and binding == self.binding)
            now = self.clock()
            return {'available': active, 'viewId': self.view_id if active else None,
                    'registration': self.serial, 'sequence': self.sequence,
                    'actions': [{key: value for key, value in event.items() if key != 'time'} |
                                {'ageSeconds': max(0., now - event['time'])}
                                for event in self.events if active and 0 <= now - event['time'] <= 2]}
