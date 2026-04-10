#include "atm.h"
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

ATM* atm_create(const char *auth_file)
{
    ATM *atm = (ATM*) malloc(sizeof(ATM));
    if(atm == NULL)
    {
        perror("Could not allocate ATM");
        exit(1);
    }

    // Set up the network state
    atm->sockfd=socket(AF_INET,SOCK_DGRAM,0);

    bzero(&atm->rtr_addr,sizeof(atm->rtr_addr));
    atm->rtr_addr.sin_family = AF_INET;
    atm->rtr_addr.sin_addr.s_addr=inet_addr("127.0.0.1");
    atm->rtr_addr.sin_port=htons(ROUTER_PORT);

    bzero(&atm->atm_addr, sizeof(atm->atm_addr));
    atm->atm_addr.sin_family = AF_INET;
    atm->atm_addr.sin_addr.s_addr=inet_addr("127.0.0.1");
    atm->atm_addr.sin_port = htons(ATM_PORT);
    bind(atm->sockfd,(struct sockaddr *)&atm->atm_addr,sizeof(atm->atm_addr));

    // Set up the protocol state
    atm->user_logged_in[0] = '\0';
    atm->active = 0;  

    if (load_auth_file(auth_file) != 0) 
    {
        fprintf(stderr, "Error opening ATM initialization file\n");
        atm_free(atm);
        exit(64);
    } 

    return atm;
}

void atm_free(ATM *atm)
{
    if(atm != NULL)
    {
        close(atm->sockfd);
        free(atm);
    }
}

ssize_t atm_send(ATM *atm, char *data, size_t data_len)
{
    // Returns the number of bytes sent; negative on error
    return sendto(atm->sockfd, data, data_len, 0,
                  (struct sockaddr*) &atm->rtr_addr, sizeof(atm->rtr_addr));
}

ssize_t atm_recv(ATM *atm, char *data, size_t max_data_len)
{
    // Returns the number of bytes received; negative on error
    return recvfrom(atm->sockfd, data, max_data_len, 0, NULL, NULL);
}

static int card_exists(const char *username)
{
    char filename[300];
    snprintf(filename, sizeof(filename), "%s.card", username);
    
    FILE *f = fopen(filename, "r");
    if (!f) 
    {
        return 0;
    }
    fclose(f);
    return 1;
}

void atm_process_command(ATM *atm, char *command)
{
    char recvline[10000];
    int n;
    
    size_t len = strlen(command);
    while (len > 0 && (command[len-1] == '\n' || command[len-1] == '\r' || command[len-1] == ' ')) 
    {
        len--;
    }
    command[len] = '\0';

    char command_parsed[1024];
    strncpy(command_parsed, command, sizeof(command_parsed));
    command_parsed[sizeof(command_parsed)-1] = '\0';

    char *blocks[7];
    int block_count = 0;
    char *block = strtok(command_parsed, " ");
    while (block != NULL && block_count < 7) 
    {
        blocks[block_count++] = block;
        block = strtok(NULL, " ");
    }
    
    if (block_count == 0) return;

    if (strcmp(blocks[0], "begin-session") == 0) 
    {
        if (atm->active) 
        {
            printf("A user is already logged in\n");
            return;
        }
        
        if (block_count != 2) 
        {
            printf("Usage: begin-session <user-name>\n");
            return;
        }
        
        char *username = blocks[1];

        for (int i = 0; username[i]; i++) 
        {
            if (!isalpha(username[i])) 
            {
                printf("Usage: begin-session <user-name>\n");
                return;
            }
        }
        
        if (!card_exists(username)) 
        {
            printf("No such user\n");
            return;
        }
        
        printf("PIN? ");
        fflush(stdout);
        
        char pin[10];
        if (fgets(pin, sizeof(pin), stdin) == NULL) 
        {
            printf("Error reading PIN\n");
            return;
        }
        
        size_t pin_len = strlen(pin);
        while (pin_len > 0 && (pin[pin_len-1] == '\n' || pin[pin_len-1] == '\r')) {
            pin_len--;
        }
        pin[pin_len] = '\0';
        
        if (strlen(pin) != 4) 
        {
            printf("Not authorized\n");
            return;
        }
        for (int i = 0; i < 4; i++) 
        {
            if (!isdigit(pin[i])) 
            {
                printf("Not authorized\n");
                return;
            }
        }
        
        char message[256];
        snprintf(message, sizeof(message), "begin-session %s %s", username, pin);
        atm_send(atm, message, strlen(message));

        n = atm_recv(atm, recvline, sizeof(recvline));
        recvline[n] = '\0';

        if (strcmp(recvline, "Authorized") == 0) 
        {
            atm->active = 1;
            strncpy(atm->user_logged_in, username, sizeof(atm->user_logged_in)-1);
            atm->user_logged_in[sizeof(atm->user_logged_in)-1] = '\0';
            printf("Authorized\n");
        } 
        else 
        {
            printf("%s\n", recvline);
        }
        return;
    }
    if (strcmp(blocks[0], "withdraw") == 0) 
    {
        if (!atm->active) 
        {
            printf("No user logged in\n");
            return;
        }

        if (block_count != 2) 
        {
            printf("Usage: withdraw <amt>\n");
            return;
        }
        
        char *amt_str = blocks[1];
        for (int i = 0; amt_str[i]; i++) 
        {
            if (!isdigit(amt_str[i])) 
            {
                printf("Usage: withdraw <amt>\n");
                return;
            }
        }

        char withdraw_message[256];
        snprintf(withdraw_message, sizeof(withdraw_message), "withdraw %s %s", 
                 atm->user_logged_in, blocks[1]);

        atm_send(atm, withdraw_message, strlen(withdraw_message));

        n = atm_recv(atm, recvline, sizeof(recvline));
        recvline[n] = '\0';
        printf("%s\n", recvline);
        return;
    }
    
    if (strcmp(blocks[0], "balance") == 0) 
    {
        if (!atm->active) 
        {
            printf("No user logged in\n");
            return;
        }
        
        if (block_count != 1) 
        {
            printf("Usage: balance\n");
            return;
        }

        char balance_message[256];
        snprintf(balance_message, sizeof(balance_message), "balance %s", atm->user_logged_in);

        atm_send(atm, balance_message, strlen(balance_message));

        n = atm_recv(atm, recvline, sizeof(recvline));
        recvline[n] = '\0';
        printf("%s\n", recvline);
        return;
    }
    
    if (strcmp(blocks[0], "end-session") == 0) 
    {
        if (!atm->active) 
        {
            printf("No user logged in\n");
            return;
        }
        
        if (block_count != 1) 
        {
            printf("Usage: end-session\n");
            return;
        }

        char end_message[256];
        snprintf(end_message, sizeof(end_message), "end-session %s", atm->user_logged_in);

        atm_send(atm, end_message, strlen(end_message));

        n = atm_recv(atm, recvline, sizeof(recvline));
        recvline[n] = '\0';
        printf("%s\n", recvline);

        atm->active = 0;
        atm->user_logged_in[0] = '\0';
        return;
    }

    printf("Invalid command\n");

    /*
	 * The following is a toy example that simply sends the
	 * user's command to the bank, receives a message from the
	 * bank, and then prints it to stdout.
	 */

	/*
    char recvline[10000];
    int n;

    atm_send(atm, command, strlen(command));
    n = atm_recv(atm,recvline,10000);
    recvline[n]=0;
    fputs(recvline,stdout);
	*/
}