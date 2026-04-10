#include "branchsim.hpp"

/**
 * A set of global variables
 * You may define and set any global classes and variables here as needed.
 */
static unsigned int* pht;
static std::uint64_t ghr;
static unsigned int ctr_max;
static unsigned int ctr_weakly_taken;
static std::uint64_t index_mask;
static std::uint64_t  history_shift;
static std::uint64_t history_mask;
static predictor_type pred_type;
static std::uint64_t* hist_table;

/**
 * This subroutine initializes the branch predictors.
 * You many add and initialize any global or heap
 * variables as needed.
 * (1) You're responsible for completing this routine
 *
 * Inputs and outputs:
 * @param[in]   ptype       The type of branch predictor to simulate
 * @param[in]   num_entries The number of entries a PC is hashed into
 * @param[in]   counter_bits The number of bits per counter
 * @param[in]   history_bits The number of bits per history
 * @param[out]  p_stats     Pointer to the stats structure
 */
void setup_predictor(predictor_type ptype,
                     int num_entries,
                     int counter_bits,
                     int history_bits,
                     branch_stats_t* p_stats) {
  ctr_max = (unsigned int)(1 << counter_bits) - 1;
  ctr_weakly_taken = (unsigned int) (1 << (counter_bits - 1));

  index_mask = (std::uint64_t)num_entries - 1;
  history_mask = (std::uint64_t)(1 << history_bits) - 1;
  history_shift = history_bits;

  int pht_size = num_entries;
  pred_type = ptype;
  /*
   * For each type of branch prediction, complete the following switch
   * to define pht_size and p_stats based on num_entries, counter_bits, and history_bits.
   * The code for Bimodal branch predictor is provided as an example.
   */
  switch (ptype) {
    case PTYPE_BIMODAL: {
      pht_size = num_entries;
      p_stats->storage_overhead = ((std::uint64_t)pht_size) * ((std::uint64_t)counter_bits);
      break;
    }
    case PTYPE_TWO_LEVEL_ADAPTIVE: {
      /*
       * 1.1. Add your code here
       * uses a local history table of num_entries entries (each history_bits big) 
       * and a shared pattern history table (PHT) indexed only by the history value.
       * Thus the PHT size is 2^{history_bits} counters.
       */
      pht_size = 1 << history_bits;
      p_stats->storage_overhead =
          ((std::uint64_t)num_entries * (std::uint64_t)history_bits) +
          ((std::uint64_t)pht_size * (std::uint64_t)counter_bits);
      break;
    }
    case PTYPE_LOCAL_HISTORY: {
      /*
       * 1.2. Add your code here
       * Local history predictor keeps a history register per entry and a
       * separate PHT for each history value.  The PHT has
       * num_entries * 2^{history_bits} counters.
       */
      pht_size = num_entries * (1 << history_bits);
      p_stats->storage_overhead =
          ((std::uint64_t)num_entries * (std::uint64_t)history_bits) +
          ((std::uint64_t)pht_size * (std::uint64_t)counter_bits);
      break;
    }
    case PTYPE_GSHARE: {
      /*
       * 1.3. Add your code here
       * Gshare uses a global history register (history_bits big) and a
       * PHT with one counter per entry (num_entries counters).
       */
      pht_size = num_entries;
      p_stats->storage_overhead =
          ((std::uint64_t)pht_size * (std::uint64_t)counter_bits) +
          (std::uint64_t)history_bits;
      break;
    }
  }

  /*
   * We initial the pht, ghr, and hist_table in the following:
   */
  pht = new unsigned int[pht_size];
  for (int i = 0; i < pht_size; i++) {
    pht[i] = ctr_weakly_taken;
  }
  ghr = 0;
  if (pred_type == PTYPE_LOCAL_HISTORY || pred_type == PTYPE_TWO_LEVEL_ADAPTIVE) {
    hist_table = new std::uint64_t[num_entries];
    for (int i = 0; i < num_entries; i++) {
      hist_table[i] = 0;
    }
  }
}

/**
 * This subroutine calculates the index for accessing the pht
 * (2) You're responsible for completing this routine
 *
 * Inputs and outputs:
 * @param[in]   pc       The program counter
 * @param[out]  The index for accessing the pht
 * The code for bimodal branch predictor is provided as an example.
 */
std::uint64_t get_index(std::uint64_t pc) {
  /*
   * For each type of branch prediction, complete the following switch
   * to calculate the index. You may combine pc with index_mask and use
   * history_shift, hist_table, and history_mask in your calculation.
   * The code for the Local History branch predictor is provided as an example.
   */
  switch (pred_type) {
    case PTYPE_BIMODAL: {
      /*
       * 2.1. Add your code here
       */
      return pc & index_mask;
    }
    case PTYPE_TWO_LEVEL_ADAPTIVE: {
      /*
       * 2.2. Add your code here
       * index into the PHT comes from the local history value of the branch.
       */
      std::uint64_t hist_index = pc & index_mask;
      return (hist_table[hist_index] & history_mask);
    }
    case PTYPE_LOCAL_HISTORY: {
      std::uint64_t hist_index = pc & index_mask;
      return (hist_index * (1 << history_shift)) + (hist_table[hist_index] & history_mask);
    }
    case PTYPE_GSHARE: {
      /*
       * 2.3. Add your code here
       * Gshare XORs the low-order PC bits with the global history.
       */
      std::uint64_t pc_index = pc & index_mask;
      std::uint64_t hist_bits = ghr & index_mask;
      return (pc_index ^ hist_bits) & index_mask;
    }
    default:
      return 0;
  }
}

/**
 * This subroutine run the branch prediction for a PC, returns either TAKEN or
 * NOT_TAKEN and accordingly increaments the pred_taken or pred_not_taken++.
 * (3) You're responsible for completing this routine
 *
 * @param[in]   pc          The PC value of the branch instruction.
 * @param[out]  p_stats     Pointer to the stats structure
 *
 * @return                  Either TAKEN ('T'), or NOT_TAKEN ('N')
 */
branch_dir predict_branch(std::uint64_t pc, branch_stats_t* p_stats) {
  // Increment branch count
  p_stats->num_branches++;

  // Identify index
  std::uint64_t index = get_index(pc);

  // Predict the branch by accessing the pht
  /*
   * 3.1. Add your code here
   */
  unsigned int counter = pht[index];
  branch_dir prediction;
  if (counter >= ctr_weakly_taken) {
    prediction = TAKEN;
    p_stats->pred_taken++;
  } else {
    prediction = NOT_TAKEN;
    p_stats->pred_not_taken++;
  }

  return prediction;
}

/**
 * This subroutine updates the branch predictor.
 * The branch predictor needs to be notified whether
 * the prediction was right or wrong.
 * To do so, update pht, ghr, hist_table, and any other variables as needed.
 * (4) You're responsible for completing this routine
 *
 * @param[in]   pc          The PC value of the branch instruction.
 * @param[in]   actual      The actual direction of the branch
 * @param[in]   predicted   The predicted direction of the branch (from predict_branch)
 * @param[out]  p_stats     Pointer to the stats structure
 */
void update_predictor(std::uint64_t pc,
                      branch_dir actual,
                      branch_dir predicted,
                      branch_stats_t* p_stats) {
  std::uint64_t index = get_index(pc);

  if (actual == predicted) {
    p_stats->correct++;
  }

  if (actual == TAKEN) {
    ghr = ((ghr << 1) | 1);
    /*
     * 4.1. Add your code here
     */
    if (pht[index] < ctr_max)
      pht[index]++;
    if (pred_type == PTYPE_LOCAL_HISTORY || pred_type == PTYPE_TWO_LEVEL_ADAPTIVE) {
      std::uint64_t hist_index = pc & index_mask;
      hist_table[hist_index] = ((hist_table[hist_index] << 1) | 1) & history_mask;
    }
  } else {
    ghr = ((ghr << 1) | 0);
    /*
     * 4.2. Add your code here
     */
    if (pht[index] > 0)
      pht[index]--;
    if (pred_type == PTYPE_LOCAL_HISTORY || pred_type == PTYPE_TWO_LEVEL_ADAPTIVE) {
      std::uint64_t hist_index = pc & index_mask;
      hist_table[hist_index] = ((hist_table[hist_index] << 1) | 0) & history_mask;
    }
  }
}

/**
 * This subroutine cleans up any outstanding memory operations and calculating overall statistics.
 *
 * @param[out]  p_stats     Pointer to the statistics structure
 */
void complete_predictor(branch_stats_t *p_stats) {
  p_stats->misprediction_rate = (double)(p_stats->num_branches - p_stats->correct) / (double)p_stats->num_branches;
  delete[] pht;
  if (pred_type == PTYPE_LOCAL_HISTORY) {
    delete[] hist_table;
  }
}
