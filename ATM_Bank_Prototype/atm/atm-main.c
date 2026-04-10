/* 
 * The main program for the ATM.
 *
 * You are free to change this as necessary.
 */

#include "atm.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
    if (argc != 2) 
    {
        fprintf(stderr, "Error opening ATM initialization file\n");
        return 64;
    }
    
    char user_input[1000];

    ATM *atm = atm_create(argv[1]);

    printf("ATM: ");
    fflush(stdout);

    while (fgets(user_input, 10000, stdin) != NULL)
    {
        atm_process_command(atm, user_input);
        
        if (atm->active) {
            printf("ATM (%s): ", atm->user_logged_in);
        } else {
            printf("ATM: ");
        }
        fflush(stdout);
    }
    
    atm_free(atm);
    return EXIT_SUCCESS;
}
