int num_of_letters(char* text){
    int num = 0;
    char * lett = text;
    while (lett != 0){
        if (*lett >= 'a' && *lett <= 'z'){
            num += 1;
        } else if (*lett >= 'A' && *lett <= 'Z'){
            num += 1;
        }
        lett += 1;
    }
    return num;
}
