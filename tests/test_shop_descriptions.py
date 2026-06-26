import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_bonus_power_descriptions_show_multiplier():
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'app.js')) as f:
        built = f.read()
    assert '2\u00d7 streak bonuses' in built
    assert '4\u00d7 streak bonuses' in built
    assert '8\u00d7 streak bonuses' in built
    assert 'Multiplies streak bonuses' not in built


if __name__ == '__main__':
    test_bonus_power_descriptions_show_multiplier()
    print('ok')
