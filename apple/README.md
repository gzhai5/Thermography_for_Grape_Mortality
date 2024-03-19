# Apple GUI

There are 2 options to open the GUI and start acquisition.

The functionalities of this GUI is majorly to stream and record down the thermal data in 1 fps.

## Option 1: use Git Bash

1. Open the Git Bash

2. Direct to the code path

```bash
cd /c/Users/Public/Documents/Thermography_for_Grape_Mortality/apple
```

3. Run shell script

```bash
./ start.sh
```

4. Then the code will keep running the GUI in acquisition mode. When any error occurs that leads to the python crash, it will still rerun it. Use Ctrl+C to exit.

5. (Optional) It is also allowed to run below code. But in this case, it will lose a sh wrapper rerun logic. 

```bash
python main.py
```

There're three mode that can be specified: <halt>, <stream>, <acquire>. Default is <halt>.

```bash
python main.py --mode <mode-option>
```

## Option 2: use VScode

1. Open the VScode software, by default, the path is correct to the Thermography_for_Grape_Mortality folder

2. Open the terminal (bash terminal). The terminal button could be find on top panel, and the bash option could be find in the terminal panel beside "+".

3. Adjust the path to the apple folder

4. Run the GUI using the same steps shown in option 1 3~5.