'''
@author: roj-idl71
'''

import matplotlib

#USED IN jroplot_spectra.py
RTI_CODE = 0            #Range time intensity (RTI).
SPEC_CODE = 1           #Spectra (and Cross-spectra) information.
CROSS_CODE = 2          #Cross-Correlation information.
COH_CODE = 3            #Coherence map.
BASE_CODE = 4           #Base lines graphic.
ROW_CODE = 5            #Row Spectra.
TOTAL_CODE = 6          #Total Power.
DRIFT_CODE = 7          #Drifts graphics.
HEIGHT_CODE = 8         #Height profile.
PHASE_CODE = 9          #Signal Phase.

POWER_CODE = 16
NOISE_CODE = 17
BEACON_CODE = 18

#USED IN jroplot_parameters.py
WIND_CODE = 22
MSKYMAP_CODE = 23
MPHASE_CODE = 24

MOMENTS_CODE = 25
PARMS_CODE = 26
SPECFIT_CODE = 27
EWDRIFT_CODE = 28


#COLOR TABLES

refl = [
    "#2a323b", "#3f4c59", "#556576", "#6a7f94", "#7f99b2",
    "#00ffff", "#007fff", "#0000ff", "#00ff00", "#00bf00",
    "#007f00", "#ffff00", "#ffbf00", "#ff7f00", "#ff0000",
    "#bf0000", "#7f0000", "#fe00fe", "#8e59ff", "#f0f0f0",
    ]

#refl_bounds = [-25, -20, -15, -10, -5, 0, 5, 10 ,15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]

doppler = [
    "#003300", "#005500", "#007700", "#009900", "#00bb00", "#24ce24", "#6cd26c", "#b4d6b4",
    "#d6b4b4", "#d26c6c", "#ce2424", "#bb0000", "#980000", "#760000", "#540000", "#330000",
]

width = [
    "#00ffff", "#00aaf2", "#0055e5", "#0000d8", 
    "#007f00", "#00aa00", "#00d400", "#00ff00",
    "#ffff00", "#ffd400", "#ffaa00", "#ff7f00",
    "#ff0000", "#d40000", "#aa0000", "#7f0000",
    "#ff00ff", "#d400d4", "#aa00aa", "#7f007f",
    "#9938ff", "#832ed8", "#6e25b2", "#591c8c",
]

zdr = [
    "#7333cc", "#7e3cd5", "#8945de", "#944ee7", "#9f57f0", "#aa5ff8",
    "#82345c", "#984272", "#ae4f88", "#c55c9f", "#db6ab5", "#f177cb",
    "#b5842d", "#c29a4c", "#d0b16b", "#ddc78a", "#ebddaa", "#f8f4c9",
    "#f0f5ff", "#c4d8ff", "#97bbff", "#6a9eff", "#3e81ff", "#1164ff",
    "#17f576", "#13df60", "#0ec949", "#0ab233", "#059c1d", "#018606",
    "#fff300", "#ffdd00", "#ffc700", "#ffb000", "#ff9a00", "#ff8400",
    "#f10000", "#db0000", "#c40000", "#ae0000", "#980000", "#810000",
]

phi = [
    "#ff3f40", "#ec3b6d", "#bf2f7e", "#92247c", "#7b1f7f", "#732492", "#782fbf", "#6f3bec",
    "#513fff", "#3b4bec", "#2f57bf", "#245592", "#1f5a7f", "#247992", "#2fb4bf", "#3bece0",
    "#3fffd8", "#3becb1", "#2fbf7d", "#249253", "#1f7f3d", "#24923b", "#2fbf3e", "#3bec3b",
    "#50ff3f", "#5aec3b", "#55bf2f", "#4a9224", "#487f1f", "#5a9224", "#80bf2f", "#aaec3b",
    "#c4ff3f", "#c0ec3b", "#a4bf2f", "#839224", "#777f1f", "#8e9224", "#bfbc2f", "#ece03b",
    "#ffea3f", "#ecd13b", "#bfa42f", "#927924", "#7f661f", "#927124", "#bf8f2f", "#ecac3b",
    "#ffb43f", "#eca23b", "#bf7f2f", "#925e24", "#7f501f", "#925924", "#bf712f", "#ec883b",
    "#ff8f3f", "#ec813b", "#bf662f", "#924c24", "#7f401f", "#924824", "#bf5c2f", "#ec6f3b",
]

rho = [
    "#2a323b", "#3f4c59", "#556576", "#6a7f94", "#7f99b2",
    "#00ffff", "#00bff5", "#007feb", "#003fe2", "#0000d8",
    "#00ff00", "#00df00", "#00bf00", "#009f00", "#007f00",
    "#ffff00", "#ffdf00", "#ffbf00", "#ff9f00", "#ff7f00",
    "#ff0000", "#df0000", "#bf0000", "#9f0000", "#7f0000",
    "#ff00ff", "#df00df", "#bf00bf", "#9f009f", "#7f007f",
    "#9938ff", "#8931e2", "#792ac5", "#6923a8", "#591c8c",
]

rho_bounds = [0.2, 0.306, 0.412, 0.518, 0.624, 0.73,
            0.75, 0.77, 0.79, 0.81, 0.83,
            0.85, 0.87, 0.89, 0.91, 0.93,
            0.936, 0.942, 0.948, 0.954, 0.96,
            0.966, 0.972, 0.978, 0.984, 0.99, 
            0.996, 1.002, 1.008, 1.014, 1.02,
            1.026, 1.032, 1.038, 1.044, 1.05, 1.056]

cb_tables = {
    'sophy_z': {'colors': refl, 'norm': None },
    'sophy_v': {'colors': doppler, 'norm': None },
    'sophy_w': {'colors': width, 'norm': None },
    'sophy_d': {'colors': zdr, 'norm': None},
    'sophy_p': {'colors': phi, 'norm': None },
    'sophy_r': {'colors': rho, 'norm': matplotlib.colors.BoundaryNorm(rho_bounds, 37), 'extremes': ['#15191d', '#333899']},
}

def register_cmap():
    
    for colormap in cb_tables:
        cmap = matplotlib.colors.ListedColormap(cb_tables[colormap]['colors'], name=colormap)
        if 'extremes' in cb_tables[colormap]:
            cmap = cmap.with_extremes(under=cb_tables[colormap]['extremes'][0], over=cb_tables[colormap]['extremes'][1])
        matplotlib.pyplot.register_cmap(cmap=cmap)
