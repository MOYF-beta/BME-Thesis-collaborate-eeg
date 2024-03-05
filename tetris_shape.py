import numpy as np


_tetris_shapes = [
    [#z
        [1,1,0],
        [0,1,1]
    ],
    [#z'
        [0,1,1],
        [1,1,0]
    ],
    [#凸
        [1,1,1],
        [0,1,0]
    ],
    [#L'
        [0,1],
        [0,1],
        [1,1]
    ],
    [#L
        [1,0],
        [1,0],
        [1,1]
    ],
    [#田
        [1,1],
        [1,1]
    ],
    [#|
        [1],
        [1],
        [1],
        [1]
    ],
]
tetris_color = {0:'white',1:'pink',2:'blue',3:'cyan',4:'green',5:'yellow',6:'purple',7:'red'}

tetris_shapes = [np.array(x,dtype=np.int8).T for x in _tetris_shapes]