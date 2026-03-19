import random
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

# Wheel configuration: each segment has a label and its center angle in degrees
# 0° = top (where the pointer is), going clockwise
SEGMENTS = [
    {"label": "WIN",  "color": "#FFD700", "start": 0,   "end": 180},
    {"label": "LOSE", "color": "#CC0000", "start": 180, "end": 360},
]

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/spin', methods=['POST'])
def spin():
    outcome = random.choice(['win', 'lose'])
    # Pick a random angle within the segment, then add enough full rotations
    # so the wheel spins visually (5-8 full rotations before landing)
    extra_spins = random.randint(5, 8) * 360

    if outcome == 'win':
        # CSS rotate(X) brings the point at (360-X)° to the pointer.
        # WIN occupies 0-180° (right half), so we need 360-X in 0-180 → X in 180-360.
        segment_angle = random.uniform(200, 340)
    else:
        # LOSE occupies 180-360° (left half), so we need 360-X in 180-360 → X in 0-180.
        segment_angle = random.uniform(20, 160)

    total_rotation = extra_spins + segment_angle
    return jsonify({'result': outcome, 'angle': total_rotation})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
