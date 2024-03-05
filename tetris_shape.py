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
tetris_color = {
    0: [1, 1, 1],    # white
    1: [1, 0.753, 0.796],  # pink
    2: [0, 0, 1],    # blue
    3: [0, 1, 1],    # cyan
    4: [0, 1, 0],    # green
    5: [1, 1, 0],    # yellow
    6: [0.627, 0.125, 0.941],  # purple
    7: [1, 0, 0]     # red
}


tetris_shapes = [np.array(x,dtype=np.int8).T for x in _tetris_shapes]