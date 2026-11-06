"""Unlimited local administrator cosmetics; real isolated SQLite, no account service."""
import json
from pathlib import Path
import subprocess
import unittest
import uuid
from unittest.mock import patch

import admin_stickers
import gameplay
import test_training as fixtures
from training import ServiceError, TrainingService


class AdminStickerTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def inventory(self):
        self.service.admin_mode = True
        return gameplay.stickers(self.service)

    def action(self, kind, **value):
        return gameplay.stickers(self.service, kind, {'requestId': str(uuid.uuid4()), **value})

    def place(self, identity, **point):
        state = self.inventory()
        unit = next(unit for unit in state['units'] if unit['stickerId'] == identity and unit['placement'] is None)
        return self.action('place', unitId=unit['id'], revision=unit['revision'], x=.4, y=.5, angle=0, **point)

    def test_full_collection_matches_shared_catalogue_including_all_backgrounds(self):
        root = Path(__file__).resolve().parents[1]
        raw = subprocess.check_output(['node', '--input-type=module', '-e',
            "import {STICKERS} from './server/leaderboard/src/gameplay.mjs';process.stdout.write(JSON.stringify(STICKERS))"], cwd=root)
        self.assertEqual(self.inventory()['catalogue'], json.loads(raw))
        state = self.inventory()
        self.assertTrue(state['unlimited'])
        self.assertEqual(len([item for item in state['catalogue'] if item.get('kind') == 'background']), 11)
        self.assertEqual(set(state['discoveredStickers']), {item['id'] for item in state['catalogue']})

    def test_inventory_reads_do_not_mint_or_write_any_rewards(self):
        state = self.inventory()
        before = self.service.connection.total_changes
        with patch.object(gameplay, '_request', side_effect=AssertionError('Admin must stay local')):
            self.assertEqual(self.inventory(), state)
            self.assertEqual(self.inventory(), state)
        self.assertEqual(before, self.service.connection.total_changes)
        self.assertIsNone(self.service.connection.execute('SELECT 1 FROM account_preferences WHERE key=?', (admin_stickers.KEY,)).fetchone())

    def test_sixty_same_stickers_keep_fresh_stock_with_no_finite_quantity(self):
        with patch.object(gameplay, '_request', side_effect=AssertionError('Admin must stay local')):
            for count in range(1, 61):
                state = self.place('common-leaf')
                placed = [unit for unit in state['units'] if unit['placement']]
                self.assertEqual(len(placed), count)
                self.assertEqual(len({unit['id'] for unit in state['units']}), len(state['units']))
                self.assertEqual(len([unit for unit in state['units'] if unit['stickerId'] == 'common-leaf' and unit['placement'] is None]), 1)
                self.assertTrue(state['unlimited'])
        self.assertEqual(len(state['units']), len(state['catalogue']) + 60)

    def test_all_backgrounds_can_be_repeatedly_selected_and_recycled(self):
        backgrounds = [item for item in self.inventory()['catalogue'] if item.get('kind') == 'background']
        for _ in range(2):
            for item in backgrounds:
                state = self.place(item['id'])
                active = [unit for unit in state['units'] if unit['placement']]
                self.assertEqual(len(active), 1)
                self.assertEqual(active[0]['stickerId'], item['id'])
                self.assertEqual(active[0]['placement'], {'x': .5, 'y': .5, 'angle': 0, 'scale': 1})
        state = self.action('recycle', unitId=active[0]['id'], revision=active[0]['revision'])
        self.assertFalse(any(unit['placement'] for unit in state['units']))
        self.assertEqual(len(state['units']), len(state['catalogue']))

    def test_request_replays_do_not_duplicate_units_and_stale_edits_are_rejected(self):
        unit = self.inventory()['units'][0]
        payload = {'requestId': str(uuid.uuid4()), 'unitId': unit['id'], 'revision': 0, 'x': .4, 'y': .5, 'angle': 0}
        state = gameplay.stickers(self.service, 'place', payload)
        self.assertEqual(gameplay.stickers(self.service, 'place', payload), state)
        with self.assertRaises(ServiceError) as caught:
            gameplay.stickers(self.service, 'place', {**payload, 'x': .6})
        self.assertEqual(caught.exception.status, 409)
        with self.assertRaises(ServiceError) as caught:
            self.action('place', unitId=unit['id'], revision=0, x=.6, y=.5, angle=0)
        self.assertEqual(caught.exception.status, 409)
        for invalid in [float('nan'), float('inf'), True, -1, 2]:
            with self.subTest(x=invalid), self.assertRaises(ServiceError):
                self.action('place', unitId=unit['id'], revision=1, x=invalid, y=.5, angle=0)
        self.assertEqual(self.inventory(), state)

    def test_outfits_presets_duplicate_copies_and_restart_remain_available(self):
        person = next(item['id'] for item in self.inventory()['catalogue'] if item['shape'].startswith('person'))
        state = self.place(person)
        unit = next(unit for unit in state['units'] if unit['placement'])
        state = self.action('outfit', unitId=unit['id'], revision=unit['revision'], appearance={'hat': 'crown'})
        state = self.place(person)
        state = self.action('scene-save', name='管理员场景', inventoryRevision=state['revision'])
        preset = state['scenePresets'][0]
        for unit in [unit for unit in state['units'] if unit['placement']]:
            state = self.action('recycle', unitId=unit['id'], revision=unit['revision'])
        state = self.action('scene-apply', presetId=preset['id'], inventoryRevision=state['revision'])
        placed = [unit for unit in state['units'] if unit['placement']]
        self.assertEqual(len(placed), 2)
        self.assertTrue(any(unit.get('appearance', {}).get('hat') == 'crown' for unit in placed))
        self.assertEqual(state['scene']['missing'], [])
        self.service.close()
        self.service = TrainingService(self.library, self.db, self.assets, self.judge, self.clock, self.root / 'backups', admin_mode=True)
        restored = self.inventory()
        self.assertEqual(restored['units'], state['units'])
        self.assertEqual(restored['scenePresets'], state['scenePresets'])
        self.assertTrue(restored['unlimited'])

    def test_user_cannot_request_unlimited_inventory_or_call_admin_storage(self):
        self.assertFalse(self.service.admin_mode)
        with self.assertRaises(ServiceError) as caught:
            admin_stickers.stickers(self.service)
        self.assertEqual(caught.exception.status, 404)
        with self.assertRaises(ServiceError):
            gameplay.stickers(self.service, 'place', {'unlimited': True})
        response = {'owner': self.service._ranking_profile()['user_id'], 'revision': 1, 'units': [], 'catalogue': []}
        with patch.object(gameplay, '_request', return_value=response), patch.object(gameplay, '_grant_pending'), patch('sticker_rewards.grant_pending'), patch('background_rewards.deliver_completed'), patch('fun_moments.confirmed_gameplay'):
            self.assertNotIn('unlimited', gameplay.stickers(self.service))
        self.assertIsNone(self.service.connection.execute('SELECT 1 FROM account_preferences WHERE key=?', (admin_stickers.KEY,)).fetchone())
