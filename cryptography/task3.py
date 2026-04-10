#!/usr/bin/env python3

import sys
from task1 import read_blocks, parse_session, BLOCK_SIZE

def find_transfer_to_my_account(blocks, transaction_details):
    # Find all accounts that appear as TRANSFER destination
    dest_counts = {}  # Map destination account -> list of (idx, start_pos, blocks_consumed)
    
    for idx, (trans_type, start_pos, blocks_consumed) in enumerate(transaction_details):
        if trans_type == 'TRANSFER':
            # TRANSFER: account (1) + tag (1) + amount (1) + account2 (1) + time (1)
            dest_account = blocks[start_pos + 3]
            if dest_account not in dest_counts:
                dest_counts[dest_account] = []
            dest_counts[dest_account].append((idx, start_pos, blocks_consumed))
    
    # Find the account that appears as destination exactly once
    for acc, transfers in dest_counts.items():
        if len(transfers) == 1:
            idx, start_pos, blocks_consumed = transfers[0]
            print(f"Found transfer to my account at position {start_pos}", file=sys.stderr)
            return start_pos, blocks_consumed
    
    return None, None

def find_invoice_amount(blocks, transaction_details, transfer_amount_block):
    invoice_amounts = []
    
    for trans_type, start_pos, blocks_consumed in transaction_details:
        if trans_type == 'INVOICE':
            # INVOICE: account (1) + tag (1) + account2 (1) + amount (1)
            invoice_amount = blocks[start_pos + 3]
            invoice_amounts.append(invoice_amount)
            
            # Prefer an amount different from the current transfer amount
            if invoice_amount != transfer_amount_block:
                print(f"Found invoice amount at position {start_pos + 3} to use as replacement", file=sys.stderr)
                return invoice_amount
    
    # If all invoice amounts are the same as the transfer amount, use the first one
    # (This shouldn't happen given the task setup, but handle it gracefully)
    if invoice_amounts:
        print(f"Using invoice amount (same as original transfer amount)", file=sys.stderr)
        return invoice_amounts[0]
    
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: task3 <input_file>", file=sys.stderr)
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
    
    # TRANSFER structure: account (1) + tag (1) + amount (1) + account2 (1) + time (1)
    # The amount is at position transfer_start + 2
    transfer_amount_pos = transfer_start + 2
    transfer_amount_block = blocks[transfer_amount_pos]
    
    print(f"Transfer amount block is at position {transfer_amount_pos}", file=sys.stderr)
    
    # Find an invoice amount to use as replacement
    new_amount_block = find_invoice_amount(blocks, transaction_details, transfer_amount_block)
    
    if new_amount_block is None:
        print("Failed to find invoice amount for replacement", file=sys.stderr)
        sys.exit(1)
    
    # Create task3.out with modified transfer amount
    with open('task3.out', 'wb') as out_file:
        for i, block in enumerate(blocks):
            if i == transfer_amount_pos:
                # Replace with the new amount
                out_file.write(new_amount_block)
                print(f"Replaced amount at position {i} with invoice amount", file=sys.stderr)
            else:
                out_file.write(block)
    
    print(f"Wrote modified transfer to task3.out ({len(blocks)} blocks)", file=sys.stderr)

if __name__ == "__main__":
    main()
