# -*- coding: utf-8 -*-
"""Amoniaco.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1LShnflUvc9dH7VIaw9huDW5JegFYx6uz
"""

#!/usr/bin/env python3
# (c) Pedro Velarde, Universidad Politécnica de Madrid, 2024-2025
# Adaptación del script para simular la inversión de la molécula de amoníaco
# usando el método de Trotter-Suzuki de segundo orden.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from functools import partial

# ---------------------------------------------------------------------------
# 1. Definición del potencial por tramos (tipo 6) para la inversión de NH₃
# ---------------------------------------------------------------------------
def V(x, t, V0=0.25, type=6):
    """
    Potencial por tramos:
      - Para |x| > a: V = V_out (muy alto, simulando infinito)
      - Para b < |x| <= a: V = 0 (los pozos laterales)
      - Para |x| <= b: V = V0 (la barrera central)

    Parámetros (en nm):
      b = 0.04 nm   (mitad de la anchura de la barrera)
      d ≈ 0.03 nm   (distancia del N al plano de H)
      a = b + d ≈ 0.07 nm
    """
    a = 0.07   # nm, límite de los pozos
    b = 0.04   # nm, mitad de la anchura de la barrera
    V_out = 1e6  # Valor muy alto para simular potencial infinito

    V_array = np.empty_like(x)
    # Fuera del pozo: |x| > a
    V_array[np.abs(x) > a] = V_out
    # Pozos laterales: b < |x| <= a, potencial 0
    cond_wells = (np.abs(x) <= a) & (np.abs(x) > b)
    V_array[cond_wells] = 0.0
    # Barrera central: |x| <= b, potencial V0
    cond_barrier = np.abs(x) <= b
    V_array[cond_barrier] = V0
    return V_array

# ---------------------------------------------------------------------------
# 2. Inicialización: función de onda inicial
# ---------------------------------------------------------------------------
def init():
    """
    Se inicializa la función de onda como una gaussiana
    localizada en el pozo derecho (x cerca de +0.06 nm)
    """
    sigma = 0.005  # anchura de la gaussiana (en nm)
    center = 0.06  # posición centrada en el pozo derecho (nm)
    psi = np.exp(-((x - center)**2) / (2 * sigma**2))

    # Normalización (integral aproximada usando dx)
    norm0 = np.sqrt(np.sum(np.abs(psi)**2) * dx)
    psi /= norm0

    density_prob = np.zeros((Nt//f + 1, Nx))
    time_arr = np.zeros(Nt//f + 1)
    norm_arr = np.zeros(Nt//f + 1)

    density_prob[0] = np.abs(psi)**2
    norm_arr[0] = np.sum(np.abs(psi)**2) * dx
    return density_prob, time_arr, norm_arr, psi

# ---------------------------------------------------------------------------
# 3. Operador cinético (usando FFT)
# ---------------------------------------------------------------------------
def Top(psi, dt):
    psi_k = np.fft.fft(psi)
    k_vec = np.fft.fftfreq(Nx, dx) * 2 * np.pi  # vector de momentos
    psi_k *= np.exp(-1j * (hbar * k_vec**2 * dt) / (2 * m))
    psi = np.fft.ifft(psi_k)
    return psi

# ---------------------------------------------------------------------------
# 4. Operador potencial
# ---------------------------------------------------------------------------
def Vop(psi, x, t, dt):
    psi *= np.exp(-1j * V(x, t + dt/2, V0, type=6) * dt / hbar)
    return psi

# ---------------------------------------------------------------------------
# 5. Evolución temporal (método de splitting de operadores)
# ---------------------------------------------------------------------------
def runsplit(psi):
    print("Norma inicial =", norm_arr[0])
    for nt in range(0, Nt//f):
        psi = Top(psi, -dt/2)
        t_current = time_arr[nt]
        for na in range(f):
            t_current += dt
            psi = Top(psi, dt)
            psi = Vop(psi, x, t_current, dt)
        psi = Top(psi, dt/2)
        norm_arr[nt+1] = np.sum(np.abs(psi)**2) * dx
        density_prob[nt+1] = np.abs(psi)**2
        time_arr[nt+1] = t_current
    print("Norma final =", norm_arr[-1])
    return psi

# ---------------------------------------------------------------------------
# 6. Funciones de visualización
# ---------------------------------------------------------------------------
def update(frame, line, ax, fig, maxv):
    y = density_prob[frame]
    title = r"t = {0:1.4f}   Norma = {1:1.4f}".format(time_arr[frame], norm_arr[frame])
    ax.clear()
    ax.set_title(title)
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(0, maxv)
    ax.plot(x, y, lw=2, label='|ψ|²')
    # Graficar el potencial (escalado para visualizar)
    V_plot = V(x, time_arr[frame], V0, type=6)
    # Se escalan los valores del potencial para que se vean en la misma gráfica
    scale_factor = maxv / np.max(V_plot[V_plot < 1e5]) if np.any(V_plot < 1e5) else 1
    ax.plot(x, V_plot * scale_factor, lw=2, color='red', label='Potencial')
    ax.legend()
    return line,

def inita(line):
    line.set_data([], [])
    return line,

def show(density_prob, frames, L, T):
    plt.figure(figsize=(10, 6))
    plt.imshow(density_prob, extent=[x[0], x[-1], T, 0], aspect='auto', cmap='rainbow')
    plt.colorbar(label='$|\psi(x,t)|^2$')
    plt.xlabel('x (nm)')
    plt.ylabel('Tiempo')
    plt.title('Evolución temporal de la función de onda')
    plt.show()

    fig, ax = plt.subplots()
    maxv = np.amax(density_prob)
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(0, maxv)
    ax.set_xlabel('x (nm)')
    ax.set_ylabel('$|\psi|^2$')
    line, = ax.plot([], [], lw=2)
    ani = FuncAnimation(fig, partial(update, line=line, ax=ax, fig=fig, maxv=maxv),
                        frames=frames, init_func=partial(inita, line=line), blit=False)
    plt.show()

    plt.figure()
    plt.plot(x, density_prob[-1], label='|ψ|² al final')
    plt.xlabel('x (nm)')
    plt.ylabel('$|\psi|^2$')
    plt.legend()
    plt.show()

# ---------------------------------------------------------------------------
# 7. Parámetros de la simulación y ejecución
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # Escala espacial en nm: se usa un dominio simétrico para trabajar con potencial simétrico
    L = 0.2         # Longitud total del dominio (nm) => x ∈ [-0.1, 0.1]
    Nx = 1000       # Número de puntos espaciales
    dx = L / Nx     # Paso espacial (nm)

    # Parámetros temporales
    Nt = 10000      # Número total de pasos temporales
    dt = 1e-5       # Paso de tiempo (en unidades usadas)
    f = 10          # Se almacena cada f pasos

    # Dominio espacial simétrico: x de -L/2 a L/2
    x = np.linspace(-L/2, L/2, Nx)

    # Unidades y parámetros físicos (en unidades adimensionales simplificadas)
    hbar = 1.0      # constante reducida de Planck
    m = 1.0         # masa de la partícula (ajustable según el modelo)
    V0 = 0.25       # Altura de la barrera central (en eV o en unidades adimensionales)

    # Inicializar arreglos globales para la densidad, tiempos y norma
    density_prob, time_arr, norm_arr, psi = init()

    # Evolución temporal usando splitting de operadores
    psi = runsplit(psi)

    frames = Nt // f + 1
    show(density_prob, frames, L, Nt*dt)