# Depthcharge Demonstrations

Demonstrations of Depthcharge to accompany the manuscript.

## Project Organization
```
├── Makefile                       <- Makefile with commands like `make data` or `make env`
├── README.md                      <- The top-level README you.
├── data                           <- The data.
│   └── manual                     <- Data that is maintained under version control.
├── notebooks                      <- Jupyter notebooks and/or analysis scripts.
│   └── cool-task                  <- A subdirectory for a task.
│       ├── cool-task.ipynb        <- The task demo notebook that is Colab compatible.
│       └── figures                <- A subdirectory to put the generated figures
├── scripts                        <- Scripts used for things like data preparation.
└── env.yml                        <- Creates an environment similar to Colab.
```

## Work on a task

To work on a task, start up Jupyter Lab in the correct directory with:

``` bash
make env && make <task>
```

Where `<task>` should match one of the task subdirectory names.
