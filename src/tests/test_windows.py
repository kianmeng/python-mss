"""This is part of the MSS Python's module.
Source: https://github.com/BoboTiG/python-mss.
"""

from __future__ import annotations

import threading
from typing import Tuple

import pytest

import mss
from mss.exception import ScreenShotError

try:
    import mss.windows
except ImportError:
    pytestmark = pytest.mark.skip


def test_implementation(monkeypatch: pytest.MonkeyPatch) -> None:
    # Test bad data retrieval
    with mss.mss() as sct:
        assert isinstance(sct, mss.windows.MSS)  # For Mypy

        monkeypatch.setattr(sct.gdi32, "GetDIBits", lambda *_: 0)
        with pytest.raises(ScreenShotError):
            sct.shot()


def test_region_caching() -> None:
    """The region to grab is cached, ensure this is well-done."""
    with mss.mss() as sct:
        assert isinstance(sct, mss.windows.MSS)  # For Mypy

        # Grab the area 1
        region1 = {"top": 0, "left": 0, "width": 200, "height": 200}
        sct.grab(region1)
        bmp1 = id(sct._handles.bmp)

        # Grab the area 2, the cached BMP is used
        # Same sizes but different positions
        region2 = {"top": 200, "left": 200, "width": 200, "height": 200}
        sct.grab(region2)
        bmp2 = id(sct._handles.bmp)
        assert bmp1 == bmp2

        # Grab the area 2 again, the cached BMP is used
        sct.grab(region2)
        assert bmp2 == id(sct._handles.bmp)


def test_region_not_caching() -> None:
    """The region to grab is not bad cached previous grab."""
    grab1 = mss.mss()
    grab2 = mss.mss()

    assert isinstance(grab1, mss.windows.MSS)  # For Mypy
    assert isinstance(grab2, mss.windows.MSS)  # For Mypy

    region1 = {"top": 0, "left": 0, "width": 100, "height": 100}
    region2 = {"top": 0, "left": 0, "width": 50, "height": 1}
    grab1.grab(region1)
    bmp1 = id(grab1._handles.bmp)
    grab2.grab(region2)
    bmp2 = id(grab2._handles.bmp)
    assert bmp1 != bmp2

    # Grab the area 1, is not bad cached BMP previous grab the area 2
    grab1.grab(region1)
    bmp1 = id(grab1._handles.bmp)
    assert bmp1 != bmp2


def run_child_thread(loops: int) -> None:
    for _ in range(loops):
        with mss.mss() as sct:  # New sct for every loop
            sct.grab(sct.monitors[1])


def test_thread_safety() -> None:
    """Thread safety test for issue #150.

    The following code will throw a ScreenShotError exception if thread-safety is not guaranted.
    """
    # Let thread 1 finished ahead of thread 2
    thread1 = threading.Thread(target=run_child_thread, args=(30,))
    thread2 = threading.Thread(target=run_child_thread, args=(50,))
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()


def run_child_thread_bbox(loops: int, bbox: Tuple[int, int, int, int]) -> None:
    with mss.mss() as sct:  # One sct for all loops
        for _ in range(loops):
            sct.grab(bbox)


def test_thread_safety_regions() -> None:
    """Thread safety test for different regions.

    The following code will throw a ScreenShotError exception if thread-safety is not guaranted.
    """
    thread1 = threading.Thread(target=run_child_thread_bbox, args=(100, (0, 0, 100, 100)))
    thread2 = threading.Thread(target=run_child_thread_bbox, args=(100, (0, 0, 50, 1)))
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
