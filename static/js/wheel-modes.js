// static/js/wheel-modes.js
//
// T80: Shared wheel-mode definitions for the frontend. Mirrors
// /static/wheel_modes.py exactly — keep these two files in sync.
//
// The same data lives inline in app.jsx as the WHEEL_MODE_DRAW table
// (for backward compatibility) and is now also exposed here for any
// other UI component (onboarding hints, settings panel, mode-selector
// tooltips) that wants to read it without importing the full React app.
//
// Per the ticket: "Add wheelProbabilities to the redraw effect dependency
// array" + "drawWheel() uses wheelProbabilities if provided, falls back
// to WHEEL_MODE_DRAW for backward compat". The fallback table stays in
// app.jsx; this file is the canonical place for mode metadata.
(function () {
    'use strict';

    var WHEEL_MODES = {
        steady: {
            win_pct: 70, loss_pct: 28, jackpot_pct: 2,
            jackpot_multiplier: 25,
            description: 'Default. Small wins, rare losses, standard jackpot.'
        },
        volatile: {
            win_pct: 45, loss_pct: 50, jackpot_pct: 5,
            jackpot_multiplier: 50,
            description: 'High variance. Big wins, frequent losses, double jackpot.'
        },
        inverted: {
            // T79: 60% lose is the GOOD outcome (loss-farming).
            win_pct: 35, loss_pct: 60, jackpot_pct: 5,
            jackpot_multiplier: 25,
            description: 'Losses become small wins — loss streaks still build bonus.'
        },
        gravity: {
            // T77: probabilities drift with recent results.
            win_pct: 55, loss_pct: 40, jackpot_pct: 5,
            jackpot_multiplier: 25,
            description: 'Outcomes drift toward the last result — streaks amplify both ways.'
        },
        mirror: {
            win_pct: 65, loss_pct: 30, jackpot_pct: 5,
            jackpot_multiplier: 25,
            description: 'Two spins resolve simultaneously; player takes the better result.'
        },
        singularity: {
            win_pct: 75, loss_pct: 10, jackpot_pct: 15,
            jackpot_multiplier: 50,
            description: 'The ultimate mode. Unlocked when the Singularity meter fills.'
        }
    };

    // T77: gravity drift bounds — keep in sync with wheel_modes.py.
    var GRAVITY_DRIFT_STEP = 10;
    var GRAVITY_DRIFT_MAX  = 35;
    var GRAVITY_DRIFT_MIN  = -35;

    function compute_gravity_probabilities(drift) {
        drift = drift | 0;
        return {
            win_pct:     55 + drift,
            loss_pct:    40 - drift,
            jackpot_pct: 5
        };
    }

    function clamp_gravity_drift(drift) {
        if (drift > GRAVITY_DRIFT_MAX) return GRAVITY_DRIFT_MAX;
        if (drift < GRAVITY_DRIFT_MIN) return GRAVITY_DRIFT_MIN;
        return drift;
    }

    // Public surface (browser global, matching static/js/format.js).
    window.WHEEL_MODES              = WHEEL_MODES;
    window.compute_gravity_probabilities = compute_gravity_probabilities;
    window.clamp_gravity_drift      = clamp_gravity_drift;
})();
