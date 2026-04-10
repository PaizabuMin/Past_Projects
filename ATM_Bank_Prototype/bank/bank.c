#include "bank.h"
#include "ports.h"
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

static int load_auth_file(const char *auth_file) 
{
    FILE *fp = fopen(auth_file, "rb");
    if (!fp) {
        return -1; 
    }
    
    fclose(fp);
    return 0;
}

Bank* bank_create(const char *auth_file)
{
    Bank *bank = (Bank*) malloc(sizeof(Bank));
    if(bank == NULL)
    {
        perror("Could not allocate Bank");
        exit(1);
    }

    // Set up the network state
    bank->sockfd=socket(AF_INET,SOCK_DGRAM,0);

    bzero(&bank->rtr_addr,sizeof(bank->rtr_addr));
    bank->rtr_addr.sin_family = AF_INET;
    bank->rtr_addr.sin_addr.s_addr=inet_addr("127.0.0.1");
    bank->rtr_addr.sin_port=htons(ROUTER_PORT);

    bzero(&bank->bank_addr, sizeof(bank->bank_addr));
    bank->bank_addr.sin_family = AF_INET;
    bank->bank_addr.sin_addr.s_addr=inet_addr("127.0.0.1");
    bank->bank_addr.sin_port = htons(BANK_PORT);
    bind(bank->sockfd,(struct sockaddr *)&bank->bank_addr,sizeof(bank->bank_addr));

    // Set up the protocol state
    bank->accounts = hash_table_create(100);

    if (load_auth_file(auth_file) != 0) 
    {
        fprintf(stderr, "Error opening bank initialization file\n");
        bank_free(bank);
        exit(64);
    }

    return bank;
}

void bank_free(Bank *bank)
{
    if(bank != NULL)
    {
        close(bank->sockfd);
        hash_table_free(bank->accounts);
        free(bank);
    }
}

ssize_t bank_send(Bank *bank, char *data, size_t data_len)
{
    // Returns the number of bytes sent; negative on error
    return sendto(bank->sockfd, data, data_len, 0,
                  (struct sockaddr*) &bank->rtr_addr, sizeof(bank->rtr_addr));
}

ssize_t bank_recv(Bank *bank, char *data, size_t max_data_len)
{
    // Returns the number of bytes received; negative on error
    return recvfrom(bank->sockfd, data, max_data_len, 0, NULL, NULL);
}

void bank_process_local_command(Bank *bank, char *command, size_t len)
{
    while (len > 0 && (command[len-1] == '\n' || command[len-1] == '\r' || command[len-1] == ' ')) 
    {
        len--;
    }
    command[len] = '\0';

    char command_parsed[1024];
    strncpy(command_parsed, command, sizeof(command_parsed));
    command_parsed[sizeof(command_parsed) - 1] = '\0';

    char *blocks[7];
    int block_count = 0;
    char *block = strtok(command_parsed, " ");
    while (block != NULL && block_count < 7) {
        blocks[block_count++] = block;
        block = strtok(NULL, " ");
    }

    if (block_count == 0) return;

    if (strcmp(blocks[0], "create-user") == 0) 
    {
        if (block_count != 4) 
        {
            printf("Usage:  create-user <user-name> <pin> <balance>\n");
            return;
        }
        
        char *username = blocks[1];
        char *pin_str = blocks[2];
        char *balance_str = blocks[3];

        int username_valid = 1;
        for (int i = 0; username[i]; i++) 
        {
            if (!isalpha(username[i]) || i >= 250) 
            {
                username_valid = 0;
                break;
            }
        }
        if (!username_valid) 
        {
            printf("Usage:  create-user <user-name> <pin> <balance>\n");
            return;
        }

        if (strlen(pin_str) != 4) {
            printf("Usage:  create-user <user-name> <pin> <balance>\n");
            return;
        }
        for (int i = 0; i < 4; i++)
        {
            if (!isdigit(pin_str[i])) 
            {
                printf("Usage:  create-user <user-name> <pin> <balance>\n");
                return;
            }
        }

        int pin = atoi(pin_str);

        char *endptr;
        long balance_long = strtol(balance_str, &endptr, 10);
        if (*endptr != '\0' || balance_long < 0 || balance_long > INT_MAX) 
        {
            printf("Usage:  create-user <user-name> <pin> <balance>\n");
            return;
        }
        int balance = (int)balance_long;

        if (hash_table_find(bank->accounts, username) != NULL) 
        {
            printf("Error: user %s already exists\n", username);
            return;
        }

        Account *account = malloc(sizeof(Account)); 
        if (!account) 
        { 
            perror("malloc"); 
            return; 
        } 
        account->username = strdup(username); 
        account->pin = pin; 
        account->balance = balance; 
        
        hash_table_add(bank->accounts, account->username, account); 
        
        char filename[300]; 
        snprintf(filename, sizeof(filename), "%s.card", username); 
        FILE *f = fopen(filename, "w"); 
        if (!f) 
        { 
            printf("Error creating card file for user %s\n", username); 
            hash_table_del(bank->accounts, account->username); 
            free(account->username); 
            free(account); 
            return; 
        } 
        fprintf(f, "PIN=%04d\n", pin); 
        fclose(f); 
        
        printf("Created user %s\n", username); 
        return;
    }
    else if (strcmp(blocks[0], "deposit") == 0) 
    { 
        if (block_count != 3) 
        { 
            printf("Usage: deposit <user-name> <amt>\n"); 
            return; 
        } 
        char *username = blocks[1]; 
        char *amt_str = blocks[2]; 
        char *endptr; 
        long amt_long = strtol(amt_str, &endptr, 10); 
        
        if (*endptr != '\0' || amt_long < 0 || amt_long > INT_MAX) 
        { 
            printf("Usage: deposit <user-name> <amt>\n"); 
            return; 
        } 
        int amt = (int)amt_long; 
        
        Account *account = (Account*) hash_table_find(bank->accounts, username); 
        
        if (!account) 
        { 
            printf("No such user\n"); 
            return; 
        } 

        if ((long)account->balance + amt > INT_MAX) 
        { 
            printf("Too rich for this program\n"); 
            return; 
        } 
        account->balance += amt; 
        printf("$%d added to %s's account\n", amt, username); 
        return; 
    }
    else if (strcmp(blocks[0], "balance") == 0) 
    { 
        if (block_count != 2) 
        { 
            printf("Usage: balance <user-name>\n"); 
            return; 
        } 
        
        char *username = blocks[1]; 
        Account *account = (Account*) hash_table_find(bank->accounts, username); 
        
        if (!account) 
        { 
            printf("No such user\n"); 
            return; 
        } 

        printf("$%d\n", account->balance); 
        return; 
    } 
    else 
    { 
        printf("Invalid command\n"); 
    }
}

void bank_process_remote_command(Bank *bank, char *command, size_t len)
{
    command[len] = '\0';

    char command_parsed[1024];
    strncpy(command_parsed, command, sizeof(command_parsed));
    command_parsed[sizeof(command_parsed) - 1] = '\0';

    char *blocks[7];
    int block_count = 0;
    char *block = strtok(command_parsed, " ");
    while (block != NULL && block_count < 7) {
        blocks[block_count++] = block;
        block = strtok(NULL, " ");
    }

    if (block_count == 0) return;

    char response[256] = {0}; 

    if (strcmp(blocks[0], "begin-session") == 0) 
    { 
        if (block_count != 3) 
        { 
            snprintf(response, sizeof(response), "Usage: begin-session <user-name>"); 
        } 
        else 
        { 
            char *username = blocks[1]; 
            char *pin_str = blocks[2]; 
            Account *account = (Account*) hash_table_find(bank->accounts, username); 
            if (!account) 
            { 
                snprintf(response, sizeof(response), "No such user"); 
            } 
            else 
            { 
                int valid_pin = strlen(pin_str) == 4; 
                for (int i = 0; i < 4 && valid_pin; i++) 
                {
                    if (!isdigit(pin_str[i])) 
                        valid_pin = 0; 
                    if (!valid_pin || atoi(pin_str) != account->pin) 
                        snprintf(response, sizeof(response), "Not authorized"); 
                    else 
                        snprintf(response, sizeof(response), "Authorized");
                } 
            } 
            bank_send(bank, response, strlen(response)); return; 
        }
    }
    else if (strcmp(blocks[0], "withdraw") == 0) 
    { 
        if (block_count != 3) 
        { 
            snprintf(response, sizeof(response), "Usage: withdraw <amt>"); 
        } 
        else 
        { 
            char *username = blocks[1]; 
            char *amt_str = blocks[2]; 
            Account *account = (Account*) hash_table_find(bank->accounts, username); 
            if (!account) 
            { 
                snprintf(response, sizeof(response), "No such user"); 
            } 
            else 
            { 
                char *endptr; 
                long amt = strtol(amt_str, &endptr, 10); 
                if (*endptr != '\0' || amt < 0 || amt > INT_MAX) 
                    snprintf(response, sizeof(response), "Usage: withdraw <amt>"); 
                else if (amt > account->balance) 
                    snprintf(response, sizeof(response), "Insufficient funds"); 
                else 
                {
                    account->balance -= (int)amt; 
                    snprintf(response, sizeof(response), "$%ld dispensed", amt); 
                }
            } 
        } 
        bank_send(bank, response, strlen(response)); 
        return; 
    }
    else if (strcmp(blocks[0], "balance") == 0) 
    { 
        if (block_count != 2) 
        { 
            snprintf(response, sizeof(response), "Usage: balance"); 
        } 
        else 
        { 
            char *username = blocks[1]; 
            Account *account = (Account*) hash_table_find(bank->accounts, username); 
            if (!account) 
            { 
                snprintf(response, sizeof(response), "No such user"); 
            } 
            else 
            { 
                snprintf(response, sizeof(response), "$%d", account->balance); 
            } 
        } 
        bank_send(bank, response, strlen(response)); 
        return; 
    }
    else if (strcmp(blocks[0], "end-session") == 0) 
    { 
        if (block_count != 2) 
        { 
            snprintf(response, sizeof(response), "Usage: end-session"); 
        } 
        else 
        { 
            snprintf(response, sizeof(response), "User logged out"); 
        } 
        bank_send(bank, response, strlen(response)); 
        return; 
    }
    else 
    { 
        snprintf(response, sizeof(response), "Invalid command");
        bank_send(bank, response, strlen(response)); 
        return; 
    }

    /*
     * The following is a toy example that simply receives a
     * string from the ATM, prepends "Bank got: " and echoes 
     * it back to the ATM before printing it to stdout.
     */

    /*
    char sendline[1000];
    command[len]=0;
    sprintf(sendline, "Bank got: %s", command);
    bank_send(bank, sendline, strlen(sendline));
    printf("Received the following:\n");
    fputs(command, stdout);
    */
}

