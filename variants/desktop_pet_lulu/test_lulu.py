"""Lulu regression checks; key events are delivered only to the pet in memory."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch, Mock
from PIL import Image, ImageChops
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QEvent
from PyQt6.QtGui import QMouseEvent, QTransform, QGuiApplication
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMenu
from config import (PetState, PET_STATES, DEFAULT_CHARACTER, WALK_RANGE, WALK_SPEED,
                    TYPING_TIMEOUT, REFERENCE_ACTIONS, STATE_TRANSITION, FPS)
from pet_window import PetWindow

ROOT = Path(__file__).resolve().parent


class LuluTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.pet = PetWindow(keyboard_enabled=False)
        self.pet.show()
        self.app.processEvents()
        self.pet.state_machine.stop()
        self.pet.animation.stop()

    def tearDown(self):
        self.pet.state_machine.stop()
        self.pet.animation.stop()
        self.pet.typing_idle_timer.stop()
        self.pet.left_hand_tap_timer.stop()
        self.pet.bongo_release_timer.stop()
        self.pet.tray_icon.hide()
        self.pet.deleteLater()
        self.app.processEvents()

    def test_complete_transparent_assets_and_eight_walk_poses(self):
        for state in PET_STATES:
            files = sorted((ROOT/'assets'/DEFAULT_CHARACTER/state).glob('frame_*.png'))
            self.assertTrue(files,state)
            for file in files:
                im=Image.open(file)
                self.assertEqual(im.mode,'RGBA')
                alpha=im.getchannel('A'); box=alpha.getbbox()
                self.assertIsNotNone(box)
                self.assertGreater(box[0],0,file)
                self.assertGreater(box[1],0,file)
                self.assertLess(box[2],im.width,file)
                self.assertLess(box[3],im.height,file)
        walk=[Image.open(p) for p in sorted((ROOT/'assets/blue_chibi/walking').glob('frame_*.png'))]
        self.assertEqual(len(walk),8)
        self.assertEqual(len({hashlib.sha256(im.tobytes()).digest() for im in walk}),8)
        self.assertEqual(len({im.getchannel('A').getbbox()[3] for im in walk}),1)

    def test_nonactivating_window_and_transparent_corner(self):
        flags=self.pet.windowFlags()
        self.assertTrue(flags & Qt.WindowType.WindowStaysOnTopHint)
        self.assertTrue(flags & Qt.WindowType.WindowDoesNotAcceptFocus)
        self.assertTrue(self.pet.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating))
        self.assertEqual(self.pet.focusPolicy(),Qt.FocusPolicy.NoFocus)
        self.assertFalse(self.pet.mask().contains(QPoint(0,0)))

    def test_walk_head_stability_and_pose_preservation(self):
        from build_fullbody_assets import (
            walking_head_center, align_walking_heads, build_custom_walking_frames,
        )
        walk = [Image.open(p).convert('RGBA') for p in sorted(
            (ROOT/'assets/blue_chibi/walking').glob('frame_*.png'))]
        centers = [walking_head_center(frame) for frame in walk]
        self.assertLessEqual(max(centers) - min(centers), 1.0)
        # Rebuilding must preserve registration, and alignment must not distort
        # any limb or introduce per-frame scale changes.
        for stored, rebuilt in zip(walk, build_custom_walking_frames()):
            self.assertEqual(stored.tobytes(), rebuilt.tobytes())
        for before, after in zip(walk, align_walking_heads(walk)):
            before_box = before.getchannel('A').getbbox()
            after_box = after.getchannel('A').getbbox()
            self.assertEqual(before_box[1::2], after_box[1::2])
            self.assertEqual(before.crop(before_box).tobytes(), after.crop(after_box).tobytes())

    def test_walk_stops_without_reversing_on_each_monitor(self):
        p = self.pet
        for screen in [QRect(0, 24, 1440, 876), QRect(1440, 0, 1920, 1080),
                       QRect(-1920, -200, 1920, 1080)]:
            for direction in [-1, 1]:
                with self.subTest(screen=screen, direction=direction), patch.object(
                    p, '_available_screen_geometry', return_value=screen
                ):
                    home = screen.left() + 400
                    p.move(home, screen.top() + 250)
                    p.home_position = p.pos()
                    p.state_machine.request_state(PetState.WALKING, True)
                    p.state_machine.stop()
                    p.state_machine.walk_direction = direction
                    positions = [p.x()]
                    for _ in range(100):
                        p._on_walk_step(direction)
                        positions.append(p.x())
                        self.assertEqual(p.state_machine.walk_direction, direction)
                    deltas = [b-a for a, b in zip(positions, positions[1:])]
                    self.assertTrue(all(0 <= d * direction <= WALK_SPEED for d in deltas))
                    self.assertEqual(p.x(), home + direction * WALK_RANGE)
                    self.assertEqual(p.state_machine.current_state, PetState.IDLE)
                    self.assertFalse(p.state_machine.walk_step_timer.isActive())
                    # A later walk at the boundary starts inward, once.
                    p.state_machine.request_state(PetState.WALKING, True)
                    p.state_machine.stop()
                    self.assertEqual(p.state_machine.walk_direction, -direction)

    def test_offscreen_home_and_small_screen_never_invert_bounds(self):
        p = self.pet
        for screen, home in [(QRect(0, 0, 1440, 900), 1300),
                             (QRect(1440, 0, 1920, 1080), 3300),
                             (QRect(-1920, 0, 1920, 1080), -2000),
                             (QRect(50, 0, 200, 180), 180)]:
            with self.subTest(screen=screen, home=home), patch.object(
                p, '_available_screen_geometry', return_value=screen
            ):
                p.move(home, 0)
                p.home_position = p.pos()
                p.state_machine.request_state(PetState.WALKING, True)
                p.state_machine.stop()
                left, right = p._walk_limits()
                self.assertLessEqual(left, right)
                p._on_walk_step(p.state_machine.walk_direction)
                stopped = p.x()
                for _ in range(20):
                    p._on_walk_step(p.state_machine.walk_direction)
                    self.assertEqual(p.x(), stopped)
                self.assertLessEqual(left, stopped)
                self.assertLessEqual(stopped, right)
                self.assertEqual(p.state_machine.current_state, PetState.IDLE)

    def test_screen_geometry_refreshes_after_monitor_change(self):
        screen = Mock()
        geometries = [QRect(1440, 0, 1920, 1080), QRect(-1920, 24, 1920, 1056)]
        with patch.object(QGuiApplication, 'screenAt', return_value=screen) as screen_at:
            for geometry in geometries:
                screen.availableGeometry.return_value = geometry
                self.assertEqual(self.pet._available_screen_geometry(), geometry)
                screen_at.assert_called_with(self.pet.frameGeometry().center())

    def test_walk_orientation_and_masks_change_on_frame(self):
        p=self.pet
        p.state_machine.request_state(PetState.WALKING,True);p.state_machine.stop()
        p.state_machine.walk_direction=1;p.animation.set_frame(0)
        right=p._get_display_frame().toImage();right_mask=p.mask()
        p.animation.set_frame(2)
        self.assertNotEqual(p.mask(),right_mask)
        p.animation.set_frame(0);p.state_machine.walk_direction=-1;p._update_click_mask()
        left=p._get_display_frame().toImage()
        self.assertEqual(left,right.transformed(QTransform().scale(-1,1)))
        self.assertNotEqual(p.mask(),right_mask)

    def test_key_highlight_left_hand_release_and_typing_timeout(self):
        p=self.pet
        p._on_key_pressed('kc:0')
        self.assertEqual(p.state_machine.current_state,PetState.TYPING)
        self.assertIn('A',p.active_keys)
        self.assertTrue(p.left_hand_down)
        QTest.qWait(130)
        self.assertFalse(p.left_hand_down)
        self.assertIn('A',p.active_keys)
        p._on_key_released('kc:0');QTest.qWait(70)
        self.assertNotIn('A',p.active_keys)
        QTest.qWait(TYPING_TIMEOUT+30)
        self.assertNotEqual(p.state_machine.current_state,PetState.TYPING)
        self.assertFalse(p.active_keys)

    def test_only_left_hand_has_two_distinct_layers(self):
        path=ROOT/'assets'/DEFAULT_CHARACTER
        base=Image.open(path/'typing_mongocat_base.png')
        tap=Image.open(path/'typing_mongocat_tap.png')
        self.assertIsNone(ImageChops.difference(base,tap).getbbox())
        rest_arm=Image.open(path/'typing_mongocat_rest_overlay.png')
        tap_arm=Image.open(path/'typing_mongocat_tap_overlay.png')
        self.assertIsNotNone(ImageChops.difference(rest_arm,tap_arm).getbbox())
        for arm in [rest_arm,tap_arm]:
            box=arm.getchannel('A').getbbox()
            self.assertGreater(box[0],arm.width*.60)
            self.assertLess(box[2],arm.width*.81)

    def test_drag_updates_home_and_walk_stays_near_home(self):
        p=self.pet
        p.move(250,250)
        local=QPointF(p.width()/2,p.height()/2)
        start=QPointF(p.mapToGlobal(local.toPoint()))
        press=QMouseEvent(QEvent.Type.MouseButtonPress,local,start,Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
        p.mousePressEvent(press)
        self.assertTrue(p.dragging)
        target=start+QPointF(30,20)
        move=QMouseEvent(QEvent.Type.MouseMove,local,target,Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
        p.mouseMoveEvent(move)
        release=QMouseEvent(QEvent.Type.MouseButtonRelease,local,target,Qt.MouseButton.LeftButton,Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier)
        p.mouseReleaseEvent(release)
        self.assertFalse(p.dragging)
        self.assertEqual(p.home_position,p.pos())
        p.state_machine.request_state(PetState.WALKING,True);p.state_machine.stop()
        for _ in range(200):
            p._on_walk_step(p.state_machine.walk_direction)
            self.assertLessEqual(abs(p.x()-p.home_position.x()),WALK_RANGE)

    def test_wakeup_returns_to_idle_and_selfie_disabled(self):
        machine=self.pet.state_machine
        machine.request_state(PetState.SLEEPING,True)
        machine.notify_activity()
        self.assertEqual(machine.current_state,PetState.WAKEUP)
        machine.release_state(PetState.WAKEUP)
        self.assertEqual(machine.current_state,PetState.IDLE)
        self.assertFalse(machine.request_state(PetState.SELFIE,True))
        actions=self.pet.tray_icon.contextMenu().actions()
        state_menu=next(a.menu() for a in actions if a.text()=='切换状态')
        self.assertFalse(next(a for a in state_menu.actions() if a.text()=='自拍').isVisible())

    def test_six_reference_actions_have_independent_poses_and_autoplay(self):
        self.assertEqual({s['reference'] for s in REFERENCE_ACTIONS.values()}, set(range(1, 7)))
        all_hashes = set()
        for state, spec in REFERENCE_ACTIONS.items():
            with self.subTest(state=state):
                self.assertGreater(STATE_TRANSITION[PetState.IDLE][state], 0)
                for quality in ['blue_chibi', 'blue_chibi_hd']:
                    files = sorted((ROOT/'assets'/quality/state).glob('frame_*.png'))
                    self.assertEqual(len(files), 4)
                    hashes = {hashlib.sha256(Image.open(f).tobytes()).digest() for f in files}
                    self.assertEqual(len(hashes), 4)
                    self.assertFalse(all_hashes & hashes)
                    all_hashes.update(hashes)
                with patch('state_machine.random.choices', return_value=[state]):
                    self.pet.state_machine.request_state(PetState.IDLE, True)
                    self.pet.state_machine._on_idle_timeout()
                self.assertEqual(self.pet.state_machine.current_state, state)
                self.assertEqual(self.pet.animation.current_state, state)
                self.assertEqual(self.pet.animation.frame_delay, spec['frame_ms'])
                self.assertEqual(self.pet.animation.frame_count, len(spec['sequence']))
                self.assertEqual(self.pet.state_machine.action_timer.interval(), spec['duration_ms'])
                self.assertTrue(self.pet.state_machine.action_timer.isActive())
        self.assertAlmostEqual(sum(STATE_TRANSITION[PetState.IDLE].values()), 1)

    def test_reference_actions_timeout_and_do_not_move_window(self):
        machine = self.pet.state_machine
        position = self.pet.pos()
        for state in REFERENCE_ACTIONS:
            with self.subTest(state=state):
                machine.request_state(state, True)
                for _ in range(16):
                    self.pet.animation._next_frame()
                    self.pet._on_walk_step(1)
                    self.assertEqual(self.pet.pos(), position)
                machine.action_timer.start(10)
                QTest.qWait(30)
                self.assertEqual(machine.current_state, PetState.IDLE)
                self.assertEqual(self.pet.animation.frame_delay, int(1000/FPS))
                self.assertFalse(machine.action_timer.isActive())

    def test_pullup_bar_is_fixed_while_character_changes_pose(self):
        frames = [Image.open(p).convert('RGBA') for p in sorted(
            (ROOT/'assets/blue_chibi/pullups').glob('frame_*.png'))]
        centers = []
        for frame in frames:
            counts = []
            for y in range(frame.height):
                count = 0
                for x in range(60, 260):
                    r, g, b, a = frame.getpixel((x, y))
                    count += a > 100 and g > r * 1.15 and g > b * 1.15
                counts.append(count)
            rows = [y for y, count in enumerate(counts) if count >= max(counts) * .6]
            centers.append((min(rows)+max(rows))/2)
        self.assertLessEqual(max(centers)-min(centers), 1)
        # Both posts below the grips use the same generated layer in every pose.
        for frame in frames[1:]:
            for box in [(20, 110, 55, 310), (275, 110, 300, 310)]:
                self.assertEqual(frame.crop(box).tobytes(), frames[0].crop(box).tobytes())

    def test_typing_and_dragging_cancel_reference_actions(self):
        machine = self.pet.state_machine
        for state in REFERENCE_ACTIONS:
            for interrupt in [PetState.TYPING, PetState.DRAGGING]:
                with self.subTest(state=state, interrupt=interrupt):
                    machine.request_state(state, True)
                    machine.action_timer.start(10)
                    self.assertTrue(machine.request_state(interrupt))
                    self.assertFalse(machine.action_timer.isActive())
                    QTest.qWait(25)
                    self.assertEqual(machine.current_state, interrupt)
                    machine._on_action_timeout()
                    self.assertEqual(machine.current_state, interrupt)
                    machine.release_state(interrupt)
                    self.assertEqual(machine.current_state, PetState.IDLE)

    def test_reference_menus_offer_and_trigger_all_six_actions(self):
        def check_menu(parent):
            menu = next(a.menu() for a in parent.actions() if a.text() == '参考图动作')
            actions = menu.actions()
            self.assertEqual({a.data() for a in actions}, set(REFERENCE_ACTIONS))
            for action in actions:
                action.trigger()
                self.assertEqual(self.pet.state_machine.current_state, action.data())
                self.assertEqual(action.text(), REFERENCE_ACTIONS[action.data()]['label'])
        check_menu(self.pet.tray_icon.contextMenu())
        with patch.object(QMenu, 'exec', new=lambda menu, *args: check_menu(menu)):
            self.pet._show_context_menu(QPoint(0, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
