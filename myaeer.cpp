#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <cstdio>
#include <cstring>
#include <cerrno>
#include <cstdlib>
#include "include/f8fe6ef5.h"
#include "include/18ce86af.h"

#define _MYAE_PATH_PREFIX(x) #x
#define MYAE_PREFIX1 _MYAE_PATH_PREFIX(/home/andy/myae/data/)
#define MYAE_PREFIX2 _MYAE_PATH_PREFIX(/opt/myae/)
#define FILENAME_LEN 16

static void get_rand_str(char [], int);
int main(int argc, char* argv[]) {
    char fnsh[3][FILENAME_LEN] = {0};
    get_rand_str(fnsh[0], sizeof(fnsh[0]));

    int fd(0);
    const char* cursh(fnsh[0]);
    unsigned char* sharr(_opt_myae_driver_sh);
    int slen(sizeof(_opt_myae_driver_sh));

    if(2==argc && !strncmp(argv[1], "--clean", 7)) {
        sharr = _opt_myae_clean_sh;
        slen = sizeof(_opt_myae_clean_sh);
    } else {
        if (F_OK != access(MYAE_PREFIX1"myae_scratch", 0)) {
            system("mkdir -p "MYAE_PREFIX2"images "MYAE_PREFIX2"scratch");
            system("mkdir -p -m 755 "MYAE_PREFIX1"myae_images "MYAE_PREFIX1"myae_scratch");
            system("mount --bind "MYAE_PREFIX2"scratch "MYAE_PREFIX1"myae_scratch");
            system("mount --bind "MYAE_PREFIX2"images "MYAE_PREFIX1"myae_images");
        }
    }

    snprintf(fnsh[1], FILENAME_LEN*2, "/var/tmp/%s", fnsh[0]);
    if((fd = open(fnsh[1], O_RDWR|O_CREAT|O_TRUNC, S_IRWXU)) < 0) {
        perror("open Error=> ");
        return 1;
    }
    if(write(fd, sharr, slen) < 0) {
        perror("write Error=> ");
        return 2;
    }
    close(fd);

    if(execl(fnsh[1], NULL) < 0) {
        perror("execl Error=> ");
        return 3;
    }

    //正常情况以下代码将不会被执行
    printf("THIS LINE WILL NOT BE PRINTED\n");
}

void get_rand_str(char s[], int num) {
    const char* str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz,./;\"'<>?";
    const int lstr(strlen(str));

    memset(s, 0, num);
    srand((unsigned int)time((time_t *)NULL));
    s[num -7] = s[0] = '\"';
    strncpy(s+num-6, ".mysh", 5);

    for(int i=1; i<num-7; i++) {
        s[i] = str[rand() % lstr];
    }
}
