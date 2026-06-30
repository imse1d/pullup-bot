PROGRAM = [

    {
        "pullups": [3, 3, 3, 3, 3, 3],
        "dips": [3, 3, 3, 3, 3, 3]
    },

    {
        "pullups": [2, 2, 2, 2, 2, 2, 2, 2],
        "dips": [2, 2, 2, 2, 2, 2, 2, 2]
    },

    {
        "pullups": [4, 4, 4, 4, 4],
        "dips": [4, 4, 4, 4, 4]
    },

    {
        "pullups": [
            1, 2, 3, 2, 1,
            1, 2, 3, 2, 1,
            1, 2, 3, 2, 1
        ],
        "dips": [
            1, 2, 3, 2, 1,
            1, 2, 3, 2, 1,
            1, 2, 3, 2, 1
        ]
    },

    {
        "pullups": [5, 5, 5, 5, 5],
        "dips": [5, 5, 5, 5, 5]
    },

    {
        "pullups": [6, 6, 6, 6],
        "dips": [6, 6, 6, 6]
    },

    {
        "pullups": [7, 7, 7],
        "dips": [7, 7, 7]
    },

    {
        "pullups": [-1],
        "dips": [-1]
    }

]

while len(PROGRAM) < 100:
    PROGRAM.extend(PROGRAM[:8])

PROGRAM = PROGRAM[:100]