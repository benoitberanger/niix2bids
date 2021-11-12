# the approach is simple : the sequence name ('gre') defines which decision tree to apply
products = [
    # [seq_regex             fcn name]
    ['^tfl$'                , 'prog_mprage' ],  # mprage & mp2rage
    ['.*mp2rage.*'          , 'prog_mprage' ],  # mp2rage WIP
    ['^tse_vfl$'            , 'prog_tse_vfl'],  # 3DT2 space & 3DFLAIR space_ir
    ['.*diff.*'             , 'prog_diff'   ],  # diffusion
    ['(.*bold.*)|(.*pace.*)', 'prog_bold'   ],  # bold fmri
    ['^gre_field_mapping$'  , 'prog_fmap'   ],  # dual echo field map, with pre-substracted phase
    ['^gre$'                , 'prog_gre'    ],  # FLASH
    ['^tse$'                , 'prog_tse'    ],  # tse, usually AX_2DT1 or AX_2DT2
    ['.*ep2d_se.*'          , 'prog_ep2d_se'],  # SpinEcho EPI
    ['^haste$'              , 'prog_discard'],  # haste is used as first sequence to get subject position in the magnet
]

wip = [
    ["ep2d_stejskal_386"    , "prog_diff"   ],  # diffusion WIP
    ["cstfl_wip925b"        , "prog_mprage" ],  # compressed sensing mprage & mp2rage
]

c2p = [
    ["^icm_gre$"            , "prog_gre"    ],  # ICM version of the GRE, with better phase reconstruction
]

# the "output" variable has to be called "config"
config = products + wip + c2p
