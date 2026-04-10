#!/usr/bin/env python3

import sys
from task1 import read_blocks, parse_session, BLOCK_SIZE

def find_invoice_from_my_account(blocks, transaction_details):
    # Track all account appearances
    account_transactions = {}  # account -> list of (transaction_idx, role)
    
    for idx, (tt, start, consumed) in enumerate(transaction_details):
        if tt == 'BALANCE':
            acc = blocks[start]
            if acc not in account_transactions:
                account_transactions[acc] = []
            account_transactions[acc].append((idx, 'balance'))
        elif tt == 'TRANSFER':
            src = blocks[start]
            dest = blocks[start + 3]
            if src not in account_transactions:
                account_transactions[src] = []
            account_transactions[src].append((idx, 'transfer_src'))
            if dest not in account_transactions:
                account_transactions[dest] = []
            account_transactions[dest].append((idx, 'transfer_dest'))
        elif tt == 'INVOICE':
            issuer = blocks[start]
            payer = blocks[start + 2]
            if issuer not in account_transactions:
                account_transactions[issuer] = []
            account_transactions[issuer].append((idx, 'invoice_issuer'))
            if payer not in account_transactions:
                account_transactions[payer] = []
            account_transactions[payer].append((idx, 'invoice_payer'))
    
    # Find account that appears in exactly one transaction
    for acc, txns in account_transactions.items():
        unique_txn_indices = set(t[0] for t in txns)
        if len(unique_txn_indices) == 1:
            # Check if it's an invoice payer
            if any(t[1] == 'invoice_payer' for t in txns):
                idx = txns[0][0]
                trans_type, start_pos, blocks_consumed = transaction_details[idx]
                print(f"Found invoice from my account at position {start_pos}", file=sys.stderr)
                return start_pos, blocks_consumed
    
    return None, None

def find_transfer_tag_and_time(blocks, transaction_details):
    for trans_type, start_pos, blocks_consumed in transaction_details:
        if trans_type == 'TRANSFER':
            # TRANSFER: account (1) + tag (1) + amount (1) + account2 (1) + time (1)
            transfer_tag = blocks[start_pos + 1]
            time_block = blocks[start_pos + 4]
            print(f"Found transfer tag at position {start_pos + 1}", file=sys.stderr)
            print(f"Found time block at position {start_pos + 4}", file=sys.stderr)
            return transfer_tag, time_block
    
    return None, None

def main():
    if len(sys.argv) != 2:
        print("Usage: task4 <input_file>", file=sys.stderr)
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
    
    # Find the invoice from my account
    invoice_start, invoice_len = find_invoice_from_my_account(blocks, transaction_details)
    
    if invoice_start is None:
        print("Failed to find invoice from my account", file=sys.stderr)
        sys.exit(1)
    
    # INVOICE structure: account (1) + tag (1) + account2 (1) + amount (1) = 4 blocks
    # TRANSFER structure: account (1) + tag (1) + amount (1) + account2 (1) + time (1) = 5 blocks
    
    # Get invoice components
    # INVOICE: issuer + invoice_tag + payer + amount
    issuer_account = blocks[invoice_start]      # The one requesting payment  
    invoice_tag = blocks[invoice_start + 1]
    payer_account = blocks[invoice_start + 2]   # MY account (paying)
    invoice_amount = blocks[invoice_start + 3]
    
    # Find transfer tag and time from another transfer
    transfer_tag, time_block = find_transfer_tag_and_time(blocks, transaction_details)
    
    if transfer_tag is None or time_block is None:
        print("Failed to find transfer tag and time", file=sys.stderr)
        sys.exit(1)
    
    # Create task4.out
    # Convert INVOICE to TRANSFER:
    # INVOICE: issuer + invoice_tag + payer + amount (4 blocks)
    # TRANSFER: source + transfer_tag + amount + dest + time (5 blocks)
    #
    # Result: Payment FROM me becomes Transfer TO me!
    
    with open('task4.out', 'wb') as out_file:
        i = 0
        while i < len(blocks):
            if i == invoice_start:
                # Replace the 4-block INVOICE with a 5-block TRANSFER
                # TRANSFER: source + tag + amount + destination + time
                out_file.write(issuer_account)     # Block 0: Source (was issuer)
                out_file.write(transfer_tag)       # Block 1: Transfer tag (from another transfer)
                out_file.write(invoice_amount)     # Block 2: Amount (from invoice - creates uniqueness)
                out_file.write(payer_account)      # Block 3: Dest MY ACCOUNT (was payer in invoice)
                out_file.write(time_block)         # Block 4: Time (from another transfer)
                
                print(f"Converted INVOICE to TRANSFER at position {i}", file=sys.stderr)
                print(f"  Issuer → Source: {issuer_account.hex()[:16]}...", file=sys.stderr)
                print(f"  Payer → Dest (MY ACCOUNT): {payer_account.hex()[:16]}...", file=sys.stderr)
                
                # Skip the original 4 invoice blocks
                i += 4
            else:
                out_file.write(blocks[i])
                i += 1
    
    output_blocks = len(blocks) - 4 + 5  # Removed 4 (invoice), added 5 (transfer)
    print(f"Wrote modified session to task4.out ({output_blocks} blocks)", file=sys.stderr)
    print(f"Original: {len(blocks)} blocks, Modified: {output_blocks} blocks (+1 block)", file=sys.stderr)

if __name__ == "__main__":
    main()
