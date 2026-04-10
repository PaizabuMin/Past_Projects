#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

int main(int argc, char *argv[]) 
{
    if (argc != 2) 
    {
        printf("Usage:  init <filename>\n");
        return 62;
    }
    
    char bank_filename[512];
    char atm_filename[512];
    snprintf(bank_filename, sizeof(bank_filename), "%s.bank", argv[1]);
    snprintf(atm_filename, sizeof(atm_filename), "%s.atm", argv[1]);
    
    struct stat st;
    if (stat(bank_filename, &st) == 0 || stat(atm_filename, &st) == 0) 
    {
        printf("Error: one of the files already exists\n");
        return 63;
    }
    
    FILE *bank_file = fopen(bank_filename, "w");
    if (!bank_file) 
    {
        printf("Error creating initialization files\n");
        return 64;
    }
    fclose(bank_file);
    
    FILE *atm_file = fopen(atm_filename, "w");
    if (!atm_file) 
    {
        remove(bank_filename);
        printf("Error creating initialization files\n");
        return 64;
    }
    fclose(atm_file);
    
    printf("Successfully initialized bank state\n");
    return 0;
}