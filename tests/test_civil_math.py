import pytest
from civil_math import calculate_concrete_volume, calculate_steel_weight, calculate_brickwork

def test_calculate_concrete_volume():
    vol = calculate_concrete_volume(1000, 1, 0.5)
    assert abs(vol - 14.1584) < 0.01

def test_calculate_steel_weight():
    vol = 14.1584
    steel = calculate_steel_weight(vol)
    assert abs(steel - 1667.15) < 0.1

def test_calculate_brickwork():
    bricks = calculate_brickwork(100, 10, 1, factor=50)
    assert abs(bricks - 4645.15) < 0.5
