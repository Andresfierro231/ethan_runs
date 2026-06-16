from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path('/scratch/09748/andresfierro231/projects_scratch/ethan_runs')
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import save_matplotlib_figure
CASE_ROOT = Path('/scratch/09748/andresfierro231/projects_scratch/val_salt_test_2_coarse_mesh_laminar')
OUTDIR = ROOT / 'reports/2026-06-01_weekly_status'
FIGDIR = OUTDIR / 'figures'

LOG_PATH = CASE_ROOT / 'logs/log.foamRun'
TOTAL_Q_PATH = CASE_ROOT / 'postProcessing/total_Q.dat'
PIV_PATH = CASE_ROOT / 'postProcessing/piv_slab_velocity/0/volFieldValue.dat'
TP_PATH = CASE_ROOT / 'postProcessing/temperature_probes/0/T'
QOI_PATH = ROOT / 'work_products/val_salt_test_2_coarse_mesh_laminar/qoi_summary.json'
VAL_PATH = ROOT / 'work_products/val_salt_test_2_coarse_mesh_laminar/validation_summary.json'

MDOT_PATHS = {
    'test section': CASE_ROOT / 'postProcessing/mdot_pipeleg_left_04_test_section/0/surfaceFieldValue.dat',
    'lower straight': CASE_ROOT / 'postProcessing/mdot_pipeleg_lower_05_straight/0/surfaceFieldValue.dat',
    'right middle': CASE_ROOT / 'postProcessing/mdot_pipeleg_right_02_middle/0/surfaceFieldValue.dat',
    'cooler': CASE_ROOT / 'postProcessing/mdot_pipeleg_upper_05_cooler/0/surfaceFieldValue.dat',
}

CONV_RE = re.compile(r'convergenceMonitor: iter=(\d+) dTmean=([0-9.eE+-]+) dTsigma=([0-9.eE+-]+) dUmean=([0-9.eE+-]+)')

FINAL_SIM_TIME = 1724.714285714
FINAL_ITER = 296000
ELAPSED_HOURS = 74.1
RTOL = 1.0e-4
END_TIME = 10000.0
CURRENT_DTSIGMA = 7.73823203e-3
PROJECTED_HOURS_TO_DTSIGMA = 7.9 * 24.0


def load_convergence():
    iters, dtmean, dtsigma, dumean = [], [], [], []
    with LOG_PATH.open() as f:
        for line in f:
            m = CONV_RE.search(line)
            if not m:
                continue
            iters.append(int(m.group(1)))
            dtmean.append(float(m.group(2)))
            dtsigma.append(float(m.group(3)))
            dumean.append(float(m.group(4)))
    return np.array(iters), np.array(dtmean), np.array(dtsigma), np.array(dumean)


def load_two_col(path: Path):
    times, values = [], []
    with path.open() as f:
        for line in f:
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            times.append(float(parts[0]))
            values.append(float(parts[1]))
    return np.array(times), np.array(values)


def load_piv():
    times, uy, magu, temp = [], [], [], []
    with PIV_PATH.open() as f:
        for line in f:
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split()
            times.append(float(parts[0]))
            uy.append(float(parts[2].strip('()')))
            magu.append(float(parts[4]))
            temp.append(float(parts[5]))
    return np.array(times), np.array(uy), np.array(magu), np.array(temp)


def load_temperature_probes():
    rows = []
    with TP_PATH.open() as f:
        for line in f:
            if not line.strip() or line.startswith('#'):
                continue
            rows.append([float(x) for x in line.split()])
    data = np.array(rows)
    return data[:, 0], data[:, 1:]


def estimate_decay_metrics(iters, dtsigma):
    tail_n = min(25, len(iters))
    fit_iters = iters[-tail_n:]
    fit_vals = dtsigma[-tail_n:]
    coeff = np.polyfit(fit_iters, np.log(fit_vals), 1)
    slope = float(coeff[0])
    intercept = float(coeff[1])
    iter_rate_per_hour = FINAL_ITER / ELAPSED_HOURS
    hours_to_tol = (math.log(RTOL) - math.log(CURRENT_DTSIGMA)) / (slope * iter_rate_per_hour)
    dtsigma_after_120h = CURRENT_DTSIGMA * math.exp(slope * iter_rate_per_hour * 120.0)
    return {
        'tail_fit_slope_per_iter': slope,
        'iter_rate_per_hour': iter_rate_per_hour,
        'hours_to_tol_fit': hours_to_tol,
        'dtsigma_after_120h_fit': dtsigma_after_120h,
        'fit_tail_start_iter': int(fit_iters[0]),
    }


def figure_convergence(iters, dtmean, dtsigma, dumean, fit_metrics):
    hours = iters / fit_metrics['iter_rate_per_hour']
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.semilogy(hours, dtmean, label='dTmean', linewidth=2)
    ax.semilogy(hours, dumean, label='dUmean', linewidth=2)
    ax.semilogy(hours, dtsigma, label='dTsigma', linewidth=2.5)
    ax.axhline(RTOL, color='black', linestyle='--', linewidth=1.5, label='target rtol = 1e-4')
    ax.axvline(ELAPSED_HOURS, color='tab:red', linestyle=':', linewidth=1.5)
    ax.text(ELAPSED_HOURS + 1, CURRENT_DTSIGMA * 1.1, 'current stop\ncheck', color='tab:red')
    ax.set_title('Salt2 convergence monitor history')
    ax.set_xlabel('Estimated wall-clock hours from source run')
    ax.set_ylabel('Relative change metric')
    ax.grid(True, which='both', alpha=0.25)
    ax.legend(loc='upper right')
    note = (
        f"current dTsigma = {CURRENT_DTSIGMA:.3e} ({CURRENT_DTSIGMA / RTOL:.1f}x target)\n"
        f"fit-based dTsigma after 120 h = {fit_metrics['dtsigma_after_120h_fit']:.3e}\n"
        f"fit-based time to 1e-4 = {fit_metrics['hours_to_tol_fit'] / 24.0:.1f} days"
    )
    ax.text(0.02, 0.02, note, transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    fig.tight_layout()
    save_matplotlib_figure(fig, OUTDIR, 'salt2_convergence_monitor', dpi=180)
    plt.close(fig)


def figure_qoi_trends(total_q_t, total_q_v, mdot_series, piv_t, piv_u, piv_temp):
    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True)

    axes[0].plot(total_q_t, total_q_v, color='tab:red', linewidth=2)
    axes[0].axhline(total_q_v[-1], color='tab:red', linestyle=':', alpha=0.6)
    axes[0].set_ylabel('total_Q [W]')
    axes[0].set_title('Salt2 QoI trends from postProcessing')
    axes[0].grid(True, alpha=0.25)

    for name, (times, values) in mdot_series.items():
        axes[1].plot(times, np.abs(values), linewidth=1.8, label=name)
    axes[1].set_ylabel('|mdot| [kg/s]')
    axes[1].grid(True, alpha=0.25)
    axes[1].legend(loc='lower right', ncol=2, fontsize=8)

    axes[2].plot(piv_t, piv_u, label='PIV slab Uy', linewidth=2)
    ax2 = axes[2].twinx()
    ax2.plot(piv_t, piv_temp, color='tab:orange', label='PIV slab T', linewidth=2)
    axes[2].set_ylabel('Uy [m/s]')
    ax2.set_ylabel('T [K]', color='tab:orange')
    axes[2].set_xlabel('Simulation time [s]')
    axes[2].grid(True, alpha=0.25)

    lines = axes[2].get_lines() + ax2.get_lines()
    labels = [line.get_label() for line in lines]
    axes[2].legend(lines, labels, loc='lower right')
    fig.tight_layout()
    save_matplotlib_figure(fig, OUTDIR, 'salt2_qoi_trends', dpi=180)
    plt.close(fig)


def figure_temperature_snapshot(tp_final, piv_temp_final):
    labels = [f'TP{i}' for i in range(1, len(tp_final) + 1)]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(x, tp_final, color='tab:blue', alpha=0.85)
    ax.axhline(float(np.mean(tp_final)), color='black', linestyle='--', linewidth=1.5, label='TP mean')
    ax.axhline(piv_temp_final, color='tab:orange', linestyle=':', linewidth=2, label='PIV slab T')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Temperature [K]')
    ax.set_title('Salt2 final temperature snapshot')
    ax.grid(True, axis='y', alpha=0.25)
    ax.legend(loc='best')
    fig.tight_layout()
    save_matplotlib_figure(fig, OUTDIR, 'salt2_temperature_snapshot', dpi=180)
    plt.close(fig)


def write_summary(fit_metrics, qoi_summary, val_summary, total_q_t, total_q_v, tp_final):
    throughput_sim_s_per_hour = FINAL_SIM_TIME / ELAPSED_HOURS
    hours_to_end_time = (END_TIME - FINAL_SIM_TIME) / throughput_sim_s_per_hour
    summary = {
        'current_dTsigma': CURRENT_DTSIGMA,
        'rtol': RTOL,
        'dTsigma_over_target': CURRENT_DTSIGMA / RTOL,
        'fit_based_days_to_rtol': fit_metrics['hours_to_tol_fit'] / 24.0,
        'documented_days_to_rtol': PROJECTED_HOURS_TO_DTSIGMA / 24.0,
        'fit_based_dTsigma_after_120h': fit_metrics['dtsigma_after_120h_fit'],
        'hours_to_end_time_at_observed_throughput': hours_to_end_time,
        'days_to_end_time_at_observed_throughput': hours_to_end_time / 24.0,
        'throughput_sim_s_per_hour': throughput_sim_s_per_hour,
        'final_total_Q_W': float(total_q_v[-1]),
        'final_probe_mean_K': float(np.mean(tp_final)),
        'final_probe_span_K': float(np.max(tp_final) - np.min(tp_final)),
        'qoi_summary': qoi_summary,
        'validation_summary': val_summary,
    }
    with (OUTDIR / 'salt2_weekly_status_summary.json').open('w') as f:
        json.dump(summary, f, indent=2)


def main():
    FIGDIR.mkdir(parents=True, exist_ok=True)
    with QOI_PATH.open() as f:
        qoi_summary = json.load(f)
    with VAL_PATH.open() as f:
        val_summary = json.load(f)

    iters, dtmean, dtsigma, dumean = load_convergence()
    total_q_t, total_q_v = load_two_col(TOTAL_Q_PATH)
    piv_t, piv_uy, piv_magu, piv_temp = load_piv()
    tp_t, tp_vals = load_temperature_probes()
    tp_final = tp_vals[-1]

    mdot_series = {name: load_two_col(path) for name, path in MDOT_PATHS.items()}
    fit_metrics = estimate_decay_metrics(iters, dtsigma)

    figure_convergence(iters, dtmean, dtsigma, dumean, fit_metrics)
    figure_qoi_trends(total_q_t, total_q_v, mdot_series, piv_t, piv_uy, piv_temp)
    figure_temperature_snapshot(tp_final, float(piv_temp[-1]))
    write_summary(fit_metrics, qoi_summary, val_summary, total_q_t, total_q_v, tp_final)


if __name__ == '__main__':
    main()
