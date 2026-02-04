###---Modulacion en Frecuencia con SDR para el radar meteorologico Sophy---###

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


"""
ChirpMod Inputs
- A             # Amplitud (valor unitario)
- ipp           # IPP (segundos)  
- dc            # DC (porcentaje %)
- sr_tx         # Sample rate en transmision (MHz)
- sr_rx         # Sample rate en recepcion (MHz)
- fc            # Frecuencia central (Hz)
- bw            # Ancho de banda (MHz)
- t_d           # Tiempo de desplazamiento Chirp (us)
- window        # Tipo de ventana "R", "K", "B"
                # window = "R": Ventana rectangular
                # window = "K": Ventana de Kaiser 70 dB
                # window = "B": Ventana Blackman
- mode_f        # Utilizado para trabajar con la variacion de 
                  frecuencia cuando sr_tx y sr_rx son diferentes
                # mode_f = 0: Trabajo normal
                # mode_f = 1: Trabajo con la variacion de frecuencia
- phi           # Angulo de desfase (rad)

ChirpMod Outputs
- chirp         # Arreglo 
                # solo de la senal Chirp
- full_chirp    # Arreglo 
                # de la senal Chirp completa (IPP)
"""


def chirpMod(A, ipp, dc, sr_tx, sr_rx, fc, bw, t_d = 0, window='R', mode_f=0, phi=0):

    f0_Hz = (fc - bw/2.0)
    T_chirp = (dc * ipp / 100.0)
    k = np.float32(bw / T_chirp)

    # Número de muestras
    n = int(sr_tx * T_chirp)

    # Tiempo vector
    t = np.arange(n, dtype=np.float32) / sr_tx

    # Selección de ventana
    if window == 'K':
        beta = signal.kaiser_beta(70)
        B = A * signal.windows.kaiser(n, beta, dtype=np.float32)
    elif window == 'B':
        B = A * signal.windows.tukey(n, 1.0).astype(np.float32)
    else:
        B = np.float32(A)

    # Frecuencia instantánea f(t)
    f = k * t + f0_Hz

    # Reducción / expansión de frecuencia (optimizada)
    if mode_f == 1:
        r = int(sr_tx / sr_rx)
        # downsample
        f = f[::r]
        # upsample replicando via repeat (MUCHO más rapido que list comprehension)
        f = f.repeat(r)

    # Fase instantánea
    # phi(t) = (k/2) t^2 + f0 t
    phi_f = (k * t * t * 0.5 + f0_Hz * t).astype(np.float32)

    # Fase en radianes
    phi_rad = (2 * np.pi * phi_f + phi).astype(np.float32)

    # Señal Chirp baseband
    chirp = B * np.exp(1j * phi_rad, dtype=np.complex64)

    # Muestras totales por IPP
    N = int(n * 100 / dc)

    # Zeros padding
    full_chirp = np.zeros(N, dtype=np.complex64)
    full_chirp[:n] = chirp

    # Delay en muestras
    N_d = int(N * t_d / (ipp * 1e6))

    # Shift eficiente
    full_chirp = np.roll(full_chirp, N_d)

    return chirp, full_chirp


# Funcion para el doble pulso Chirp (de acuerdo con el articulo de referencia PX1000)
def chirpModUnion_1(ipp, sr_tx, sr_rx, A_1, A_2, dc_1, dc_2, fc_1, fc_2, bw_1, bw_2, t_d_, window_1, window_2):
    
    _, full_chirp_1 = chirpMod(A_1, ipp, dc_1, sr_tx, sr_rx, fc_1, bw_1, t_d = t_d_, window = window_1, mode_f = 0)
    _, full_chirp_2 = chirpMod(A_2, ipp, dc_2, sr_tx, sr_rx, fc_2, bw_2, t_d = t_d_ + dc_1*ipp*(1e6/1e2), window = window_2, mode_f = 0)
    full_chirp = np.array(full_chirp_1) + np.array(full_chirp_2)

    return full_chirp


# Funcion para el doble pulso Chirp (de acuerdo con la forma de envio actual CC)
def chirpModUnion_2(ipp, sr_tx, sr_rx, A_1, A_2, dc_1, dc_2, fc_1, fc_2, bw_1, bw_2, t_d_, window_1, window_2, rep_1 = 1, rep_2 = 1):
    
    _, full_chirp_1 = chirpMod(A_1, ipp, dc_1, sr_tx, sr_rx, fc_1, bw_1, t_d = t_d_, window = window_1, mode_f = 0)
    _, full_chirp_2 = chirpMod(A_2, ipp, dc_2, sr_tx, sr_rx, fc_2, bw_2, t_d = t_d_, window = window_2, mode_f = 0)

    full_chirp_1 = np.tile(full_chirp_1, int(rep_1))
    full_chirp_2 = np.tile(full_chirp_2, int(rep_2))
    full_chirp = np.concatenate((full_chirp_1, full_chirp_2))

    return full_chirp


# Ejemplo
if __name__ == "__main__":
  
  A = 1.0
  ipp = 400.0e-6
  dc = 5.0
  sr_tx = 20.0e6
  sr_rx = 5.0e6
  fc = 1.25e6
  bw = 0.0e6
  td_ = 0
  window_ = 'B' 
  mode_f_ = 0 
  phi_ = 0 
  rep_ = 1 

  # chirp, full_chirp = chirpMod(A, ipp, dc, sr_rx, sr_rx, fc, bw, t_d = td_, window = window_, mode_f = mode_f_, phi = phi_)
  full_chirp_1 = chirpModUnion_1(ipp, sr_rx, sr_rx, A, A, 10.0, 1.0, -0.5e6, 1.25e6, 1.0e6, 0.0e6, 0, 'B', 'B')

  t = [i for i in range(len(full_chirp_1))]
  plt.plot(t, np.real(full_chirp_1))
  plt.plot(t, np.imag(full_chirp_1))
  plt.show() 