'''
@author: roj-idl71
'''
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

reflectivity = [
#    "#000000", # -30
#    "#15191d", # -25
    "#2a323b", # -20
    "#3f4c59", # -15
    "#556576", # -10
    "#6a7f94", # -5
    "#7f99b2", # 0
    "#00ffff", # 5
    "#007fff", # 10
    "#0000ff", # 15
    "#00ff00", # 20
    "#00bf00", # 25
    "#007f00", # 30
    "#ffff00", # 35
    "#ffbf00", # 40
    "#ff7f00", # 45
    "#ff0000", # 50
    "#bf0000", # 55
    "#7f0000", # 60
    "#fe00fe", # 65
    "#8e59ff", # 70
    "#f0f0f0", # 75
    ]

velocity = [
    "#003300", "#005500", "#007700", "#009900", "#00bb00", "#24ce24", "#6cd26c", "#b4d6b4",
    "#d6b4b4", "#d26c6c", "#ce2424", "#bb0000", "#980000", "#760000", "#540000", "#330000",
]

spc_width = [
    "#00ffff", "#00aaf2", "#0055e5", "#0000d8",
    "#007f00", "#00aa00", "#00d400", "#00ff00",
    "#ffff00", "#ffd400", "#ffaa00", "#ff7f00",
    "#ff0000", "#d40000", "#aa0000", "#7f0000",
    "#ff00ff", "#d400d4", "#aa00aa", "#7f007f",
    "#9938ff", "#832ed8", "#6e25b2", "#591c8c",
    "#aaaaaa", "#8e8e8e"
]

zdr = [
    "#7333cc", "#7e3cd5", "#8945de", "#944ee7", "#9f57f0", "#aa5ff8",
    "#82345c", "#984272", "#ae4f88", "#c55c9f", "#db6ab5", "#db6ab5",
    "#b5842d", "#c29a4c", "#d0b16b", "#ddc78a", "#ebddaa", "#f8f4c9",
    "#f0f5ff", "#c4d8ff", "#97bbff", "#6a9eff", "#3e81ff", "#1164ff",
    "#17f576", "#13df60", "#0ec949", "#0ab233", "#059c1d", "#018606",
    "#fff300", "#ffdd00", "#ffc700", "#ffb000", "#ff9a00", "#ff8400",
    "#f10000", "#db0000", "#c40000", "#ae0000", "#980000", "#810000",
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


sophy_cb_tables = [
    ('sophy_z', reflectivity),
    ('sophy_v', velocity),
    ('sophy_w', spc_width),
    ('sophy_d', zdr),
    ('sophy_r', rho),

]
