#!/usr/bin/env python3

import sys
from task1 import read_blocks, parse_session, BLOCK_SIZE

def find_transfer_to_my_account(blocks, transaction_details):
    # Strategy 1: Find account that appears as destination in exactly one TRANSFER
    # and nowhere else in the session
    for idx, (trans_type, start_pos, blocks_consumed) in enumerate(transaction_details):
        if trans_type == 'TRANSFER':
            dest_account = blocks[start_pos + 3]
            
            # Check if this destination account appears in any other transaction
            appears_only_here = True
            
            for other_idx, (other_type, other_start, other_consumed) in enumerate(transaction_details):
                if other_idx == idx:
                    continue
                
                if other_type == 'BALANCE':
                    if blocks[other_start] == dest_account:
                        appears_only_here = False
                        break
                elif other_type == 'TRANSFER':
                    if blocks[other_start] == dest_account or blocks[other_start + 3] == dest_account:
                        appears_only_here = False
                        break
                elif other_type == 'INVOICE':
                    if blocks[other_start] == dest_account or blocks[other_start + 2] == dest_account:
                        appears_only_here = False
                        break
            
            if appears_only_here:
                print(f"Strategy 1: Found transfer to unique account at position {start_pos}", file=sys.stderr)
                return start_pos, blocks_consumed
    
    # Strategy 2: Find account that appears as TRANSFER destination exactly once,
    # but may appear elsewhere (as source or in other transaction types)
    dest_counts = {}  # Map destination account -> list of transfer indices
    
    for idx, (trans_type, start_pos, blocks_consumed) in enumerate(transaction_details):
        if trans_type == 'TRANSFER':
            dest_account = blocks[start_pos + 3]
            if dest_account not in dest_counts:
                dest_counts[dest_account] = []
            dest_counts[dest_account].append((idx, start_pos, blocks_consumed))
    
    # Find accounts that appear as destination exactly once
    unique_dest_accounts = [acc for acc, transfers in dest_counts.items() if len(transfers) == 1]
    
    if len(unique_dest_accounts) == 1:
        # Exactly one account is a transfer destination only once
        acc = unique_dest_accounts[0]
        idx, start_pos, blocks_consumed = dest_counts[acc][0]
        print(f"Strategy 2: Found account that receives transfer exactly once at position {start_pos}", file=sys.stderr)
        return start_pos, blocks_consumed
    

    return None, None

def main():
    if len(sys.argv) != 2:
        print("Usage: task2 <input_file>", file=sys.stderr)
        sys.exit(1)
    
    filename = sys.argv[1]
    blocks = read_blocks(filename)
    
    print(f"Read {len(blocks)} blocks from {filename}", file=sys.stderr)
    
    transactions, transaction_details = parse_session(blocks)
    
    if transactions is None:
        print("Failed to parse session", file=sys.stderr)
        sys.exit(1)
    
    # Output transaction types to stdout
    for trans_type in transactions:
        print(trans_type)
    
    # Find the transfer to my account
    transfer_start, transfer_len = find_transfer_to_my_account(blocks, transaction_details)
    
    if transfer_start is None:
        print("Failed to find transfer to my account", file=sys.stderr)
        sys.exit(1)
    
    # Create task2.out with the entire stream plus the replayed transfer
    # The replay should be added at the end
    with open('task2.out', 'wb') as out_file:
        # Write all original blocks
        for block in blocks:
            out_file.write(block)
        
        # Write the replayed transfer (copy of the transfer transaction)
        for i in range(transfer_start, transfer_start + transfer_len):
            out_file.write(blocks[i])
    
    print(f"Wrote replayed transfer to task2.out", file=sys.stderr)
    print(f"Original stream: {len(blocks)} blocks, Output stream: {len(blocks) + transfer_len} blocks", file=sys.stderr)

if __name__ == "__main__":
    main()
