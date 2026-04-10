#!/usr/bin/env python3

import sys

# Block size is 128 bits = 16 bytes
BLOCK_SIZE = 16

def read_blocks(filename):
    """Read binary file and split into 16-byte blocks."""
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Split into blocks
    blocks = []
    for i in range(0, len(data), BLOCK_SIZE):
        block = data[i:i+BLOCK_SIZE]
        if len(block) == BLOCK_SIZE:
            blocks.append(block)
        else:
            print(f"Warning: Incomplete block at end of file ({len(block)} bytes)", file=sys.stderr)
    
    return blocks

def parse_session(blocks):
    # Track what we've learned about block meanings
    block_types = {}  # maps block bytes to field type (account, balance_tag, transfer_tag, etc.)
    
    # Try all 6 possible orderings of first appearance of transaction types
    # Each ordering is represented as a string like "BTI" for Balance, Transfer, Invoice
    orderings = [
        ['BALANCE', 'TRANSFER', 'INVOICE'],
        ['BALANCE', 'INVOICE', 'TRANSFER'],
        ['TRANSFER', 'BALANCE', 'INVOICE'],
        ['TRANSFER', 'INVOICE', 'BALANCE'],
        ['INVOICE', 'BALANCE', 'TRANSFER'],
        ['INVOICE', 'TRANSFER', 'BALANCE']
    ]
    
    for ordering in orderings:
        transactions, details = try_parse(blocks, ordering)
        if transactions is not None:
            return transactions, details
    
    return None, None

def try_parse(blocks, ordering):
    if len(blocks) < 2:
        return None, None
    
    # print(f"Trying ordering: {ordering}", file=sys.stderr)
    
    # Track mappings
    accounts = set()  # Set of account blocks
    balance_tags = set()  # Balance type indicators
    transfer_tags = set()  # Transfer type indicators
    invoice_tags = set()  # Invoice type indicators
    amounts = set()  # Amount blocks
    times = set()  # Time blocks
    
    transactions = []
    transaction_details = []  # List of (type, start_pos, blocks_consumed)
    pos = 0
    types_seen = set()
    
    # Start by assuming first transaction is the first type in ordering
    next_type = ordering[0]
    
    while pos < len(blocks):
        # Try to parse as next_type
        result = try_parse_transaction(blocks, pos, next_type, accounts, balance_tags, transfer_tags, invoice_tags, amounts, times)
        
        if result is None:
            # Failed to parse as next_type, try other types
            possible_types = ['BALANCE', 'TRANSFER', 'INVOICE']
            parsed = False
            
            for try_type in possible_types:
                if try_type == next_type:
                    continue  # Already tried this
                
                result = try_parse_transaction(blocks, pos, try_type, accounts, balance_tags, transfer_tags, invoice_tags, amounts, times)
                if result is not None:
                    trans_type, blocks_consumed = result
                    transactions.append(trans_type)
                    transaction_details.append((trans_type, pos, blocks_consumed))
                    types_seen.add(trans_type)
                    pos += blocks_consumed
                    
                    # Determine next type
                    if len(types_seen) < 3:
                        # Find next unseen type in ordering
                        for t in ordering:
                            if t not in types_seen:
                                next_type = t
                                break
                    else:
                        # All types seen, any type can come next
                        next_type = trans_type
                    
                    parsed = True
                    break
            
            if not parsed:
                # print(f"Failed to parse at position {pos}, {len(blocks) - pos} blocks remaining", file=sys.stderr)
                return None, None  # Failed to parse
        else:
            trans_type, blocks_consumed = result
            transactions.append(trans_type)
            transaction_details.append((trans_type, pos, blocks_consumed))
            types_seen.add(trans_type)
            pos += blocks_consumed
            
            # print(f"Parsed {trans_type} at position {pos - blocks_consumed}, consumed {blocks_consumed} blocks", file=sys.stderr)
            
            # Update next_type
            if len(types_seen) < 3:
                # Find next unseen type in ordering
                for t in ordering:
                    if t not in types_seen:
                        next_type = t
                        break
            else:
                # All types seen, predict based on patterns (just use same type as hint)
                next_type = trans_type
    
    # Validate: all 3 types must appear
    if len(types_seen) != 3:
        # print(f"Only {len(types_seen)} transaction types found: {types_seen}", file=sys.stderr)
        return None, None
    
    # print(f"Successfully parsed {len(transactions)} transactions", file=sys.stderr)
    return transactions, transaction_details

def try_parse_transaction(blocks, pos, trans_type, accounts, balance_tags, transfer_tags, invoice_tags, amounts, times):
    """
    Try to parse a transaction of given type starting at pos.
    Returns (trans_type, blocks_consumed) if successful, None otherwise.
    """
    if trans_type == 'BALANCE':
        # BALANCE: account (1 block) + tag (1 block) = 2 blocks
        if pos + 1 >= len(blocks):
            return None
        
        acc = blocks[pos]
        tag = blocks[pos + 1]
        
        # Check constraints
        if tag in transfer_tags or tag in invoice_tags or tag in amounts or tag in times:
            return None
        if acc in balance_tags or acc in transfer_tags or acc in invoice_tags or acc in amounts or acc in times:
            return None
        
        # Accept
        accounts.add(acc)
        balance_tags.add(tag)
        return ('BALANCE', 2)
    
    elif trans_type == 'TRANSFER':
        # TRANSFER: account (1) + tag (1) + amount (1) + account2 (1) + time (1) = 5 blocks
        if pos + 4 >= len(blocks):
            return None
        
        acc1 = blocks[pos]
        tag = blocks[pos + 1]
        amount = blocks[pos + 2]
        acc2 = blocks[pos + 3]
        time = blocks[pos + 4]
        
        # Check constraints
        if tag in balance_tags or tag in invoice_tags or tag in amounts or tag in times or tag in accounts:
            return None
        if amount in balance_tags or amount in transfer_tags or amount in invoice_tags or amount in times or amount in accounts:
            return None
        if time in balance_tags or time in transfer_tags or time in invoice_tags or time in amounts or time in accounts:
            return None
        if acc1 in balance_tags or acc1 in transfer_tags or acc1 in invoice_tags or acc1 in amounts or acc1 in times:
            return None
        if acc2 in balance_tags or acc2 in transfer_tags or acc2 in invoice_tags or acc2 in amounts or acc2 in times:
            return None
        if acc1 == acc2:  # Source and destination must be different
            return None
        
        # Accept
        accounts.add(acc1)
        accounts.add(acc2)
        transfer_tags.add(tag)
        amounts.add(amount)
        times.add(time)
        return ('TRANSFER', 5)
    
    elif trans_type == 'INVOICE':
        # INVOICE: account (1) + tag (1) + account2 (1) + amount (1) = 4 blocks
        if pos + 3 >= len(blocks):
            return None
        
        acc1 = blocks[pos]
        tag = blocks[pos + 1]
        acc2 = blocks[pos + 2]
        amount = blocks[pos + 3]
        
        # Check constraints
        if tag in balance_tags or tag in transfer_tags or tag in amounts or tag in times or tag in accounts:
            return None
        if amount in balance_tags or amount in transfer_tags or amount in invoice_tags or amount in times or amount in accounts:
            return None
        if acc1 in balance_tags or acc1 in transfer_tags or acc1 in invoice_tags or acc1 in amounts or acc1 in times:
            return None
        if acc2 in balance_tags or acc2 in transfer_tags or acc2 in invoice_tags or acc2 in amounts or acc2 in times:
            return None
        if acc1 == acc2:  # Source and destination must be different
            return None
        
        # Accept
        accounts.add(acc1)
        accounts.add(acc2)
        invoice_tags.add(tag)
        amounts.add(amount)
        return ('INVOICE', 4)
    
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: task1 <input_file>", file=sys.stderr)
        sys.exit(1)
    
    filename = sys.argv[1]
    blocks = read_blocks(filename)
    
    # print(f"Read {len(blocks)} blocks from {filename}", file=sys.stderr)
    
    transactions, details = parse_session(blocks)
    
    if transactions is None:
        print("Failed to parse session", file=sys.stderr)
        sys.exit(1)
    
    # Output to stdout
    for trans_type in transactions:
        print(trans_type)
    
    return transactions, details, blocks

if __name__ == "__main__":
    main()
