"""Lulu regression checks; key events are delivered only to the pet in memory."""
import hashlib
from pathlib import Path
import unittest
from PIL import Image, ImageChops
from PyQt6.QtCore import Qt, QPoint, QPointF, QEvent
from PyQt6.QtGui import QMouseEvent, QTransform
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from config import PetState, PET_STATES, DEFAULT_CHARACTER, WALK_RANGE, TYPING_TIMEOUT
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
