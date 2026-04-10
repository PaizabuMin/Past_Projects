## CMSC411: Computer Systems Architecture
## Branch Prediction


## Important policies
1.  Sharing of code between students is viewed as cheating and will receive appropriate action in accordance with university policy.
2.  You are not allowed to use your AI tools such as Chat GPT.
3.  It is acceptable for you to compare your results, and only your results, with other students to help debug your program. It is not acceptable to collaborate either on the code development or on the final experiments.
4.  You should do all your work in the C or C++ programming language and should be written according to the C99 or C++11 standards, using only the standard libraries.


## Project Description
In this project, we will be designing a simple simulator for predicting the outcomes of branches. Trace files (“.trc” files in test-trace folder) are provided, with each line indicating the PC value of each branch, and the actual outcome (e.g., 0x10 T). The simulator will process these traces, predict the outcome of each branch, and verify the prediction.

You will be modeling a few different predictor types. The predictors also accept the following input parameters so that we can vary the configuration:
1.  **The predictor type (ptype)** - You should implement the bimodal, two-level adaptive, local history (p-share), and g-share branch predictors.
2.  **The number of entries in the predictor table (num_entries)** - We use the lower bits of an address as the hash to the table. For example, in a 4-entry table, addresses ending in 000 (in binary) should go to entry 0, 001 to entry 1, 010 to entry 2, and 011 to entry 3, and 100 to entry 0 again.
3.  **Bits per counter (counter_bits)** - The counters are initialized as weakly taken. For example, for a 3-bit counter, the counter value is 0-7, and the initial value is 4.
4.  **Bits for each history register (history_bits)** - The history register is initialized as all not-taken. For example, 2-bit history should be initialized as 00.

To follow the thought process involved in designing a branch predictor, we will also look at the tradeoffs between storage and accuracy; more accurate predictors tend to require more storage overhead and attempt to find the right balance.

## Specification of simulator and what to do
Before going to the details of what you need to do, we briefly explain a general overview of the code. For this project, we provide you with following files and folders:
- **branchsim.cpp**: You need to make your changes in this file, which will include the implementations of a few branch predictors.
- **branchsim_driver.cpp**: This file includes the main() function and runs the simulator for you. You don’t have to change anything in this file. But feel free to read it to better get familiar with the code.
- **branchsim.hpp**: This file includes the definition of the functions, structs, etc. You should not  change anything in this file, but feel free to read it to better get familiar with the code.
- **Makefile**: This is the makefile that you need to run to compile your predictor:
```
$make
```

```
$make clean
```

- `test-traces/` and `test-output/`: These two folders respectively include a group of test traces that your simulator will read and the output that it must generate if your simulator works correctly.
- `traces/`: This folder includes three real-world benchmarks that you will use to optimize your branch predictors for.
- `validate-test-traces.sh`: You will be running this script to test your branch predictor. Basically, this scripts runs branchsim for all the traces in `test-traces/`, writes the outputs in `myoutput/`, compares everything in `test-output/` with `myoutput/` and prints out the differences.

1.  The `setup_predictor` function: This function initializes the branch predictor and calculates the storage overhead of each. In the three parts specified in this function with 1.1, 1.2, and 1.3 (see the following figure), you need to calculate the size of the two-level adaptive, local history, and g-share branch predictors, respectively, and update ‘p_stats->storage_overhead’ with that. The code for the bimodal branch predictor is provided as an example.

2.	The `get_index` function: This function returns the index, using which we look up the pattern history table (PHT). In the three parts specified in this function with 2.1, 2.2, and 2.3 (see the following figure), you need to calculate the pht index for bimodal, two-level adaptive, and g-share branch predictors, respectively, and return it. In this function, the code for the local history branch predictor is provided as an example.


3.	The `predict_branch` function: This function queries the branch predictor for the branch located at pc. The prediction result is returned as an enum branch_dir, which can be either TAKEN ('T'), or NOT_TAKEN ('N'). You may update any branch-related stats in p_stats as needed. More specifically, this function includes three parts: first, it updates the total number of branches (i.e., p_stats->num_branches); then, it gets the index based on pc using the get_index function we defined above; finally, it predicts the branch by accessing the pht. You need to write the required code for the last part, specified with 3.1 in this function (see the figure below). The template code always returns ‘TAKEN’. You need to remove line 154 and replace it with your code.


4.	The `update_predictor` function: This function updates the branch predictor and trains it for the next query. You may update any branch-related stats in p_stats as needed in part specified with 4.1. and 4.2.


5.	The `complete_predictor` function: This function cleans up memory and calculates the overall system statistics. You do not need to change anything in this function.

## Statistics (output)
The simulator outputs the following statistics after completion of the run:
1.	number of branches
2.	number of branches predicted to be taken
3.	number of branches predicted to be not-taken
4.	number of correct predictions
5.	misprediction rate
6.	storage overhead

## Validation
We have provided several test traces in the test-traces directory, along with the correct output in the output directory. You must run your simulator and debug it until it matches 100% all the statistics in the validation outputs. The validation script, `validate-test-traces.sh`, will do all that for you. You just need to make it an executable, with

```
chmod +x ./validate-test-trace.sh
```

or run it with

```
sh ./validate-test-traces.sh
```

The script will run all the configuration and run a diff between validated output and your output and print out all the differences. If the script does not print anything, you are good to go to the next step. If it prints some diff, I suggest that you first find the configuration that causes that diff and then run that instance alone to debug it.
